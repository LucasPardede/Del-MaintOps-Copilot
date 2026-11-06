"""
Del-MaintOps Copilot - Benchmark Temu Balik Semantik (Milestone 3)
------------------------------------------------------------------
Mengevaluasi SOPVectorStore terhadap data/benchmark_queries.json:

* Kueri relevan (synonym + ambiguous): Hit@1, Hit@k, MRR, rata-rata cosine
  top-1, rata-rata cosine ke dokumen target. Hit dihitung pada level doc_id
  (chunk-chunk dari dokumen yang sama diciutkan menjadi satu peringkat dokumen).
* Kueri OOD (ood_far + ood_near): kelas positif = "seharusnya ditolak".
  rejection precision = TP/(TP+FP), recall = TP/(TP+FN), false-rejection rate
  = proporsi kueri relevan yang salah ditolak.
* Sweep threshold, rekomendasi threshold, kuartil & histogram sebaran
  similarity top-1.
* Pembanding baseline pencarian kata kunci (detect_category dari sops.py).

Semua angka berasal dari eksekusi nyata; skrip tidak memuat angka tetap.

Penggunaan:
    uv run python scripts/benchmark_retrieval.py
    uv run python scripts/benchmark_retrieval.py --k 3 --threshold 0.35

Pemilik: Geralda Natali Gultom (QA, Sensitivity & Interface Lead)
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from knowledge.retrieval_config import (  # noqa: E402
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL_NAME,
    OOD_SIMILARITY_THRESHOLD,
    PERSIST_DIR,
)

RELEVANT_TYPES = ("synonym", "ambiguous")
OOD_TYPES = ("ood_far", "ood_near")
DEFAULT_SWEEP = [round(0.20 + 0.05 * i, 2) for i in range(9)]  # 0.20 .. 0.60


# ---------------------------------------------------------------------------
# Pengumpulan hasil pencarian
# ---------------------------------------------------------------------------
def load_queries(path: Path) -> List[Dict[str, Any]]:
    """Membaca dan memvalidasi data/benchmark_queries.json (kontrak G)."""
    queries = json.loads(Path(path).read_text(encoding="utf-8"))
    valid_types = RELEVANT_TYPES + OOD_TYPES
    for q in queries:
        for key in ("id", "query", "type", "expected_doc_ids"):
            if key not in q:
                raise ValueError(f"Kueri {q.get('id', '?')}: kunci '{key}' hilang.")
        if q["type"] not in valid_types:
            raise ValueError(f"Kueri {q['id']}: type '{q['type']}' tidak dikenal.")
        if q["type"] in OOD_TYPES and q["expected_doc_ids"]:
            raise ValueError(f"Kueri OOD {q['id']} harus memiliki expected_doc_ids kosong.")
        if q["type"] in RELEVANT_TYPES and not q["expected_doc_ids"]:
            raise ValueError(f"Kueri relevan {q['id']} harus memiliki expected_doc_ids.")
    return queries


def collapse_to_documents(results: Sequence[Any]) -> List[Dict[str, Any]]:
    """Menciutkan daftar SearchResult (urut similarity) menjadi peringkat dokumen unik.

    Tiap dokumen diwakili chunk dengan similarity tertinggi.
    """
    seen, ranked = set(), []
    for r in results:
        doc_id = r.metadata.get("doc_id", "?")
        if doc_id in seen:
            continue
        seen.add(doc_id)
        ranked.append(
            {
                "doc_id": doc_id,
                "title": r.metadata.get("title", ""),
                "chunk_id": r.id,
                "similarity": float(r.similarity),
            }
        )
    return ranked


def run_queries(store: Any, queries: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """Menjalankan semua kueri; mengambil SELURUH peringkat chunk (k = jumlah chunk)."""
    total = store.count()
    records = []
    for q in queries:
        resp = store.search(q["query"], k=total, threshold=threshold)
        ranked = collapse_to_documents(resp.results)
        records.append(
            {
                "id": q["id"],
                "query": q["query"],
                "type": q["type"],
                "expected_doc_ids": list(q["expected_doc_ids"]),
                "notes": q.get("notes", ""),
                "top_similarity": float(resp.top_similarity),
                "ranked_docs": ranked,
            }
        )
    return records


# ---------------------------------------------------------------------------
# Metrik (fungsi murni, mudah diuji tanpa model)
# ---------------------------------------------------------------------------
def _first_rank(rec: Dict[str, Any]) -> Optional[int]:
    expected = set(rec["expected_doc_ids"])
    for i, d in enumerate(rec["ranked_docs"], start=1):
        if d["doc_id"] in expected:
            return i
    return None


def _target_cosine(rec: Dict[str, Any]) -> Optional[float]:
    expected = set(rec["expected_doc_ids"])
    sims = [d["similarity"] for d in rec["ranked_docs"] if d["doc_id"] in expected]
    return max(sims) if sims else None


def relevant_metrics(records: List[Dict[str, Any]], k: int) -> Dict[str, Any]:
    """Hit@1, Hit@k, MRR, rata-rata cosine top-1 dan cosine ke dokumen target."""
    rel = [r for r in records if r["type"] in RELEVANT_TYPES]
    if not rel:
        return {"n": 0}
    ranks = [_first_rank(r) for r in rel]
    targets = [c for c in (_target_cosine(r) for r in rel) if c is not None]
    return {
        "n": len(rel),
        "hit_at_1": sum(1 for x in ranks if x == 1) / len(rel),
        f"hit_at_{k}": sum(1 for x in ranks if x is not None and x <= k) / len(rel),
        "mrr": sum(1.0 / x for x in ranks if x) / len(rel),
        "mean_top1_cosine": sum(r["top_similarity"] for r in rel) / len(rel),
        "mean_target_cosine": (sum(targets) / len(targets)) if targets else None,
    }


def ood_metrics(records: List[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
    """Metrik penolakan OOD pada satu threshold (kelas positif = harus ditolak)."""
    tp = fn = fp = tn = 0
    far_rej = far_n = near_rej = near_n = 0
    for r in records:
        rejected = r["top_similarity"] < threshold
        if r["type"] in OOD_TYPES:
            if rejected:
                tp += 1
            else:
                fn += 1
            if r["type"] == "ood_far":
                far_n += 1
                far_rej += int(rejected)
            else:
                near_n += 1
                near_rej += int(rejected)
        else:
            if rejected:
                fp += 1
            else:
                tn += 1
    n_rel, n_ood = fp + tn, tp + fn
    return {
        "threshold": threshold,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": tp / (tp + fp) if (tp + fp) else None,
        "recall": tp / n_ood if n_ood else None,
        "false_rejection_rate": fp / n_rel if n_rel else None,
        "recall_far": far_rej / far_n if far_n else None,
        "recall_near": near_rej / near_n if near_n else None,
    }


def threshold_sweep(records: List[Dict[str, Any]], thresholds: Sequence[float]) -> List[Dict[str, Any]]:
    return [ood_metrics(records, t) for t in thresholds]


def recommend_threshold(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merekomendasikan threshold dari sebaran similarity top-1.

    Jika sebaran terpisah (maks OOD < min relevan) -> titik tengah celah.
    Jika tumpang-tindih -> threshold (grid 0.005) dengan F1 penolakan tertinggi;
    seri dimenangkan oleh false-rejection terendah, lalu threshold terendah.
    """
    rel = [r["top_similarity"] for r in records if r["type"] in RELEVANT_TYPES]
    ood = [r["top_similarity"] for r in records if r["type"] in OOD_TYPES]
    if not rel or not ood:
        return {"threshold": None, "separable": None, "note": "Butuh kueri relevan dan OOD."}
    max_ood, min_rel = max(ood), min(rel)
    if max_ood < min_rel:
        return {
            "threshold": round((max_ood + min_rel) / 2, 3),
            "separable": True,
            "max_ood": max_ood,
            "min_relevant": min_rel,
            "margin": min_rel - max_ood,
        }
    best = None
    for i in range(0, 201):
        t = i * 0.005
        m = ood_metrics(records, t)
        p, rc = m["precision"], m["recall"]
        f1 = 0.0 if not p or not rc else 2 * p * rc / (p + rc)
        key = (f1, -m["false_rejection_rate"], -t)
        if best is None or key > best[0]:
            best = (key, t, f1, m)
    return {
        "threshold": round(best[1], 3),
        "separable": False,
        "max_ood": max_ood,
        "min_relevant": min_rel,
        "overlap": max_ood - min_rel,
        "f1": best[2],
    }


def keyword_baseline(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Baseline: detect_category() (kata kunci) vs semantic search (Hit@1)."""
    from knowledge.sops import detect_category

    per_query, hits = [], {"synonym": [0, 0, 0], "ambiguous": [0, 0, 0]}  # [kw_hit, sem_hit1, n]
    false_accept = 0
    n_ood = 0
    for r in records:
        pred = detect_category(r["query"])
        if r["type"] in RELEVANT_TYPES:
            kw_hit = pred is not None and pred in r["expected_doc_ids"]
            sem_hit = bool(r["ranked_docs"]) and r["ranked_docs"][0]["doc_id"] in r["expected_doc_ids"]
            hits[r["type"]][0] += int(kw_hit)
            hits[r["type"]][1] += int(sem_hit)
            hits[r["type"]][2] += 1
            per_query.append({"id": r["id"], "type": r["type"], "keyword_pred": pred, "keyword_hit": kw_hit, "semantic_hit_at_1": sem_hit})
        else:
            n_ood += 1
            false_accept += int(pred is not None)
    return {
        "by_type": {t: {"keyword_hits": v[0], "semantic_hit_at_1": v[1], "n": v[2]} for t, v in hits.items()},
        "keyword_ood_false_accept": false_accept,
        "ood_n": n_ood,
        "per_query": per_query,
    }


def quartiles(values: Sequence[float]) -> Optional[Dict[str, float]]:
    if not values:
        return None
    if len(values) == 1:
        v = values[0]
        return {"n": 1, "min": v, "q1": v, "median": v, "q3": v, "max": v}
    q1, med, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return {"n": len(values), "min": min(values), "q1": q1, "median": med, "q3": q3, "max": max(values)}


def distribution(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups = {t: [r["top_similarity"] for r in records if r["type"] == t] for t in RELEVANT_TYPES + OOD_TYPES}
    return {t: quartiles(v) for t, v in groups.items()}


def histogram_lines(records: List[Dict[str, Any]], width: float = 0.05) -> List[str]:
    """Histogram teks sederhana: R = relevan, O = OOD (satu karakter per kueri)."""
    bins: Dict[int, str] = {}
    for r in records:
        b = int(max(r["top_similarity"], 0.0) // width)
        bins[b] = bins.get(b, "") + ("R" if r["type"] in RELEVANT_TYPES else "O")
    if not bins:
        return []
    lines = []
    for b in range(min(bins), max(bins) + 1):
        marks = "".join(sorted(bins.get(b, "")))
        lines.append(f"{b * width:0.2f}-{(b + 1) * width:0.2f} | {marks}")
    return lines


# ---------------------------------------------------------------------------
# Pelaporan
# ---------------------------------------------------------------------------
def _f(x: Optional[float], nd: int = 3) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def _esc(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def status_for(rec: Dict[str, Any], k: int, threshold: float) -> str:
    rejected = rec["top_similarity"] < threshold
    if rec["type"] in OOD_TYPES:
        return "DITOLAK (benar)" if rejected else "LOLOS (false accept)"
    rank = _first_rank(rec)
    if rejected:
        return "SALAH TOLAK (false rejection)" + (f", target rank {rank}" if rank else "")
    if rank == 1:
        return "HIT@1"
    if rank is not None and rank <= k:
        return f"HIT@{k} (rank {rank})"
    return "MISS"


def render_markdown(report: Dict[str, Any]) -> str:
    k, thr = report["k"], report["threshold"]
    recs = report["records"]
    L: List[str] = []
    L.append("# Hasil Benchmark Temu Balik Semantik (Milestone 3)\n")
    L.append("> Dihasilkan otomatis oleh `scripts/benchmark_retrieval.py`. Jangan disunting manual.\n")
    L.append(f"- Waktu eksekusi: {report['generated_at']}")
    L.append(f"- Model embedding: `{report['model']}`")
    L.append(f"- Koleksi: `{report['collection']}` ({report['n_chunks']} chunk), persist dir: `{report['persist_dir']}`")
    L.append(f"- k = {k}; threshold OOD = {thr}; jumlah kueri = {len(recs)}")
    L.append("- Hit/MRR dihitung pada level `doc_id` (chunk dari dokumen sama diciutkan; similarity dokumen = chunk terbaik).\n")

    m = report["relevant_metrics"]
    L.append("## 1. Metrik kueri relevan (synonym + ambiguous)\n")
    L.append("| Metrik | Nilai |\n|---|---|")
    L.append(f"| Jumlah kueri relevan | {m['n']} |")
    L.append(f"| Hit@1 | {_f(m.get('hit_at_1'))} |")
    L.append(f"| Hit@{k} | {_f(m.get(f'hit_at_{k}'))} |")
    L.append(f"| MRR | {_f(m.get('mrr'))} |")
    L.append(f"| Rata-rata cosine top-1 | {_f(m.get('mean_top1_cosine'))} |")
    L.append(f"| Rata-rata cosine ke dokumen target | {_f(m.get('mean_target_cosine'))} |\n")
    for t in RELEVANT_TYPES:
        mt = report["relevant_metrics_by_type"].get(t)
        if mt and mt.get("n"):
            L.append(f"- `{t}` (n={mt['n']}): Hit@1={_f(mt['hit_at_1'])}, Hit@{k}={_f(mt[f'hit_at_{k}'])}, MRR={_f(mt['mrr'])}")
    L.append("")

    o = report["ood_at_threshold"]
    L.append(f"## 2. Penolakan OOD pada threshold {thr}\n")
    L.append("Kelas positif = kueri yang seharusnya ditolak (OOD).\n")
    L.append("| TP | FP | FN | TN | Precision | Recall | False-rejection rate | Recall ood_far | Recall ood_near |\n|---|---|---|---|---|---|---|---|---|")
    L.append(f"| {o['tp']} | {o['fp']} | {o['fn']} | {o['tn']} | {_f(o['precision'])} | {_f(o['recall'])} | {_f(o['false_rejection_rate'])} | {_f(o['recall_far'])} | {_f(o['recall_near'])} |\n")

    L.append("## 3. Sweep threshold\n")
    L.append("| Threshold | TP | FP | FN | Precision | Recall | False-rejection | Recall far | Recall near |\n|---|---|---|---|---|---|---|---|---|")
    for s in report["sweep"]:
        L.append(f"| {s['threshold']:.2f} | {s['tp']} | {s['fp']} | {s['fn']} | {_f(s['precision'])} | {_f(s['recall'])} | {_f(s['false_rejection_rate'])} | {_f(s['recall_far'])} | {_f(s['recall_near'])} |")
    L.append("")

    L.append("## 4. Sebaran similarity top-1 dan kalibrasi threshold\n")
    L.append("| Kelompok | n | min | Q1 | median | Q3 | max |\n|---|---|---|---|---|---|---|")
    for t, q in report["distribution"].items():
        if q:
            L.append(f"| {t} | {q['n']} | {_f(q['min'])} | {_f(q['q1'])} | {_f(q['median'])} | {_f(q['q3'])} | {_f(q['max'])} |")
    L.append("\nHistogram (R = kueri relevan, O = kueri OOD; satu huruf per kueri):\n")
    L.append("```")
    L.extend(report["histogram"])
    L.append("```\n")
    rec = report["recommendation"]
    if rec.get("threshold") is None:
        L.append(f"Rekomendasi threshold: tidak dapat dihitung ({rec.get('note')}).\n")
    elif rec["separable"]:
        L.append(f"Sebaran **terpisah**: similarity OOD tertinggi = {_f(rec['max_ood'])}, relevan terendah = {_f(rec['min_relevant'])} (celah {_f(rec['margin'])}). Rekomendasi threshold = **{rec['threshold']}** (titik tengah celah).\n")
    else:
        L.append(f"Sebaran **tumpang-tindih** (OOD tertinggi {_f(rec['max_ood'])} >= relevan terendah {_f(rec['min_relevant'])}). Threshold dengan F1 penolakan tertinggi = **{rec['threshold']}** (F1 = {_f(rec['f1'])}); ada trade-off precision/recall yang tidak bisa dihilangkan.\n")
    L.append("> Keterbatasan: jumlah kueri sangat kecil sehingga threshold ini bersifat indikatif untuk korpus dan kueri uji ini, bukan klaim generalisasi.\n")

    b = report["baseline"]
    L.append("## 5. Pembanding: pencarian kata kunci (`detect_category`) vs semantic search\n")
    L.append("| Tipe kueri | n | Hit kata kunci | Hit@1 semantic |\n|---|---|---|---|")
    for t, v in b["by_type"].items():
        L.append(f"| {t} | {v['n']} | {v['keyword_hits']} | {v['semantic_hit_at_1']} |")
    L.append(f"\nKueri OOD yang tetap diberi kategori oleh pencarian kata kunci (false accept): {b['keyword_ood_false_accept']} dari {b['ood_n']}.\n")

    L.append(f"## 6. Hasil per kueri (top-{k} dokumen, status pada threshold {thr})\n")
    L.append(f"| ID | Tipe | Kueri | Target | Top-{k} (doc_id: similarity) | Status |\n|---|---|---|---|---|---|")
    for r in recs:
        top = "; ".join(f"{d['doc_id']}: {d['similarity']:.3f}" for d in r["ranked_docs"][:k])
        tgt = ", ".join(r["expected_doc_ids"]) or "(OOD)"
        L.append(f"| {r['id']} | {r['type']} | {_esc(r['query'])} | {tgt} | {top} | {status_for(r, k, thr)} |")
    L.append("")
    return "\n".join(L)


def build_report(store: Any, queries: List[Dict[str, Any]], k: int, threshold: float,
                 persist_dir: str, sweep: Sequence[float]) -> Dict[str, Any]:
    records = run_queries(store, queries, threshold)
    by_type = {t: relevant_metrics([r for r in records if r["type"] == t], k) for t in RELEVANT_TYPES}
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": EMBEDDING_MODEL_NAME,
        "collection": COLLECTION_NAME,
        "persist_dir": str(persist_dir),
        "n_chunks": store.count(),
        "k": k,
        "threshold": threshold,
        "relevant_metrics": relevant_metrics(records, k),
        "relevant_metrics_by_type": by_type,
        "ood_at_threshold": ood_metrics(records, threshold),
        "sweep": threshold_sweep(records, sweep),
        "distribution": distribution(records),
        "histogram": histogram_lines(records),
        "recommendation": recommend_threshold(records),
        "baseline": keyword_baseline(records),
        "records": records,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Benchmark temu balik semantik Del-MaintOps Copilot.")
    ap.add_argument("--k", type=int, default=DEFAULT_TOP_K)
    ap.add_argument("--threshold", type=float, default=OOD_SIMILARITY_THRESHOLD)
    ap.add_argument("--persist-dir", default=PERSIST_DIR)
    ap.add_argument("--queries", default=str(_REPO_ROOT / "data" / "benchmark_queries.json"))
    ap.add_argument("--output", default=str(_REPO_ROOT / "docs" / "retrieval_benchmark_results.md"))
    ap.add_argument("--json-output", default=str(_REPO_ROOT / "reports" / "retrieval_benchmark_results.json"))
    args = ap.parse_args(argv)

    from knowledge.vector_store import SOPVectorStore

    store = SOPVectorStore(persist_dir=args.persist_dir)
    if store.count() == 0:
        print("[ERROR] Indeks kosong. Jalankan dulu: uv run python scripts/build_index.py --reset")
        return 2

    queries = load_queries(Path(args.queries))
    report = build_report(store, queries, args.k, args.threshold, args.persist_dir, DEFAULT_SWEEP)

    out_md, out_json = Path(args.output), Path(args.json_output)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    m, o, rec = report["relevant_metrics"], report["ood_at_threshold"], report["recommendation"]
    print(f"Hit@1={_f(m.get('hit_at_1'))}  Hit@{args.k}={_f(m.get(f'hit_at_{args.k}'))}  MRR={_f(m.get('mrr'))}")
    print(f"OOD @ {args.threshold}: precision={_f(o['precision'])} recall={_f(o['recall'])} false-rejection={_f(o['false_rejection_rate'])}")
    print(f"Rekomendasi threshold: {rec.get('threshold')} (separable={rec.get('separable')})")
    print(f"Tabel ditulis ke: {out_md}\nJSON mentah     : {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
