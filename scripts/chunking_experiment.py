"""
Del-MaintOps Copilot - Eksperimen Parameter Chunking (Milestone 3)
------------------------------------------------------------------
Grid ``chunk_size_words`` x ``overlap_words`` (+ ``prepend_title`` True/False).
Tiap konfigurasi memakai direktori sementara (tempfile) dan nama collection
unik, sehingga ``chroma_db/`` utama TIDAK tersentuh.

Per konfigurasi diukur: jumlah chunk, rata-rata kata per chunk, persentase
chunk yang melebihi batas token model (risiko terpotong saat di-embed),
Hit@1, Hit@3, MRR, rata-rata cosine ke dokumen target (kueri relevan saja).

Penggunaan:
    uv run python scripts/chunking_experiment.py

Keluaran: docs/chunking_experiment_results.md dan reports/chunking_grid_results.json.
Semua angka berasal dari eksekusi nyata.

Pemilik: Geralda Natali Gultom (QA, Sensitivity & Interface Lead)
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from benchmark_retrieval import RELEVANT_TYPES, load_queries, relevant_metrics, run_queries  # noqa: E402
from knowledge.chunker import load_and_chunk_corpus  # noqa: E402
from knowledge.retrieval_config import (  # noqa: E402
    DEFAULT_CHUNK_SIZE_WORDS,
    DEFAULT_OVERLAP_WORDS,
    EMBEDDING_MODEL_NAME,
)
from knowledge.vector_store import SOPVectorStore  # noqa: E402

SIZES = [60, 100, 150, 200]
OVERLAPS = [0, 10, 20, 30]
TOP_K = 3


def _f(x: Optional[float], nd: int = 3) -> str:
    return "n/a" if x is None else f"{x:.{nd}f}"


def token_stats(model: Any, texts: Sequence[str]) -> Dict[str, Any]:
    """Menghitung panjang token tiap chunk dan proporsi yang melebihi batas model."""
    if model is None:
        return {"max_seq_length": None, "pct_over_limit": None, "token_max": None}
    limit = getattr(model, "max_seq_length", None)
    tok = model.tokenizer
    lengths = [len(tok(t, add_special_tokens=True, truncation=False)["input_ids"]) for t in texts]
    over = sum(1 for n in lengths if limit and n > limit)
    return {
        "max_seq_length": limit,
        "pct_over_limit": over / len(lengths) if lengths else None,
        "token_max": max(lengths) if lengths else None,
    }


def run_config(size: int, overlap: int, prepend: bool, corpus_dir: str,
               queries: List[Dict[str, Any]], shared: Dict[str, Any]) -> Dict[str, Any]:
    chunks = load_and_chunk_corpus(corpus_dir=corpus_dir, chunk_size_words=size,
                                   overlap_words=overlap, prepend_title=prepend)
    words = [len(c["text"].split()) for c in chunks]
    name = f"exp_s{size}_o{overlap}_t{int(prepend)}"
    # ignore_cleanup_errors: Windows menahan file sqlite Chroma sampai proses selesai.
    with tempfile.TemporaryDirectory(prefix="chroma_exp_", ignore_cleanup_errors=True) as tmp:
        store = SOPVectorStore(persist_dir=tmp, collection_name=name)
        if shared.get("model") is None:
            try:
                shared["model"] = store._get_model()
            except Exception as exc:  # noqa: BLE001 - model tak tersedia: lanjut tanpa statistik token
                print(f"[PERINGATAN] statistik token dilewati: {exc}")
                shared["model"] = False
        elif shared["model"]:
            store._model = shared["model"]  # reuse model; hindari muat ulang tiap konfigurasi
        store.index_chunks(chunks)
        recs = run_queries(store, queries, threshold=0.0)
    m = relevant_metrics(recs, TOP_K)
    ts = token_stats(shared["model"] or None, [c["text"] for c in chunks])
    return {
        "chunk_size_words": size, "overlap_words": overlap, "prepend_title": prepend,
        "n_chunks": len(chunks), "mean_words": sum(words) / len(words), "max_words": max(words),
        **ts,
        "hit_at_1": m["hit_at_1"], f"hit_at_{TOP_K}": m[f"hit_at_{TOP_K}"], "mrr": m["mrr"],
        "mean_target_cosine": m["mean_target_cosine"],
    }


def best_key(r: Dict[str, Any]):
    """Urutan prioritas: MRR, Hit@1, cosine target, lalu sedikit chunk terpotong."""
    return (r["mrr"], r["hit_at_1"], r["mean_target_cosine"] or 0.0, -(r["pct_over_limit"] or 0.0))


def render(rows: List[Dict[str, Any]], meta: Dict[str, Any]) -> str:
    best = max(rows, key=best_key)
    L = ["# Hasil Eksperimen Chunking (Milestone 3)\n",
         "> Dihasilkan otomatis oleh `scripts/chunking_experiment.py`. Jangan disunting manual.\n",
         f"- Waktu eksekusi: {meta['generated_at']} (durasi {meta['duration_s']:.1f} detik)",
         f"- Model embedding: `{EMBEDDING_MODEL_NAME}`; batas token model: {rows[0]['max_seq_length']}",
         f"- Kueri evaluasi: {meta['n_queries']} kueri relevan (synonym + ambiguous) dari `data/benchmark_queries.json`",
         f"- Konfigurasi bawaan saat ini: size={DEFAULT_CHUNK_SIZE_WORDS}, overlap={DEFAULT_OVERLAP_WORDS}, prepend_title=True",
         "- Tiap konfigurasi memakai indeks sementara; `chroma_db/` utama tidak disentuh.\n",
         "## Tabel hasil\n",
         "| Size | Overlap | Judul | #Chunk | Rata-rata kata | Chunk > batas token | Hit@1 | Hit@3 | MRR | Cosine target |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        mark = "**" if r is best else ""
        pct = "n/a" if r["pct_over_limit"] is None else f"{r['pct_over_limit'] * 100:.0f}%"
        L.append(f"| {mark}{r['chunk_size_words']}{mark} | {r['overlap_words']} | {'ya' if r['prepend_title'] else 'tidak'} | {r['n_chunks']} | "
                 f"{r['mean_words']:.1f} | {pct} | {_f(r['hit_at_1'])} | {_f(r['hit_at_3'])} | {_f(r['mrr'])} | {_f(r['mean_target_cosine'])} |")
    L.append("\nBaris tebal = konfigurasi terbaik menurut urutan: MRR, Hit@1, cosine target, lalu proporsi chunk terpotong terkecil.\n")

    L.append("## Kesimpulan (dihitung dari tabel di atas)\n")
    L.append(f"- Konfigurasi terbaik: **size={best['chunk_size_words']}, overlap={best['overlap_words']}, "
             f"prepend_title={best['prepend_title']}** (MRR={_f(best['mrr'])}, Hit@1={_f(best['hit_at_1'])}, "
             f"cosine target={_f(best['mean_target_cosine'])}, {best['n_chunks']} chunk).")
    tied = [r for r in rows if best_key(r)[:3] == best_key(best)[:3]]
    if len(tied) > 1:
        L.append(f"- Ada {len(tied)} konfigurasi dengan MRR, Hit@1, dan cosine target identik; pemenang dipilih lewat aturan seri (chunk terpotong paling sedikit).")
    for flag, label in ((True, "dengan"), (False, "tanpa")):
        sub = [r for r in rows if r["prepend_title"] is flag]
        L.append(f"- Rata-rata MRR {label} judul: {_f(sum(r['mrr'] for r in sub) / len(sub))}; "
                 f"rata-rata cosine target: {_f(sum(r['mean_target_cosine'] for r in sub) / len(sub))}.")
    by_size: Dict[int, List[float]] = {}
    for r in rows:
        by_size.setdefault(r["chunk_size_words"], []).append(r["mrr"])
    L.append("- Rata-rata MRR per ukuran chunk: " + ", ".join(f"{s} kata = {_f(sum(v) / len(v))}" for s, v in sorted(by_size.items())) + ".")
    if rows[0]["pct_over_limit"] is not None:
        worst = max(rows, key=lambda r: r["pct_over_limit"])
        L.append(f"- Chunk yang melebihi batas {rows[0]['max_seq_length']} token terpotong diam-diam saat di-embed (bagian akhir tidak ikut terwakili). "
                 f"Proporsi terbesar: {worst['pct_over_limit'] * 100:.0f}% (size={worst['chunk_size_words']}, overlap={worst['overlap_words']}).")
    L.append("\n## Trade-off\n")
    L.append("- Chunk kecil: representasi fokus dan muat di batas token model, tetapi jumlah chunk membengkak dan konteks prosedur lebih mudah terpecah.")
    L.append("- Chunk besar: konteks utuh, tetapi bagian yang melewati batas token tidak terwakili dalam vektor dan topik bercampur.")
    L.append("- Overlap besar: menjaga kontinuitas antar-chunk, tetapi menambah duplikasi dan jumlah chunk; overlap 0 berisiko memutus konteks di batas chunk.")
    L.append("\n## Keterbatasan\n")
    L.append(f"- Hanya {meta['n_queries']} kueri relevan; selisih satu kueri mengubah Hit@1 sebesar {100 / meta['n_queries']:.0f} poin persen. "
             "Perbedaan kecil antar konfigurasi tidak boleh dianggap signifikan secara statistik dan tidak boleh diklaim sebagai generalisasi.")
    L.append("- Korpus hanya 15 dokumen berukuran seragam (sekitar 250-320 kata per dokumen).")
    return "\n".join(L) + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Eksperimen chunking Milestone 3.")
    ap.add_argument("--corpus-dir", default="data/corpus")
    ap.add_argument("--queries", default=str(_REPO_ROOT / "data" / "benchmark_queries.json"))
    ap.add_argument("--output", default=str(_REPO_ROOT / "docs" / "chunking_experiment_results.md"))
    ap.add_argument("--json-output", default=str(_REPO_ROOT / "reports" / "chunking_grid_results.json"))
    args = ap.parse_args(argv)

    queries = [q for q in load_queries(Path(args.queries)) if q["type"] in RELEVANT_TYPES]
    shared: Dict[str, Any] = {"model": None}
    rows, t0 = [], time.perf_counter()
    grid = [(s, o, p) for s in SIZES for o in OVERLAPS if o < s for p in (True, False)]
    # Baris acuan: konfigurasi bawaan repo (120/20) agar dapat dibandingkan langsung.
    grid += [(DEFAULT_CHUNK_SIZE_WORDS, DEFAULT_OVERLAP_WORDS, p) for p in (True, False)]
    for i, (s, o, p) in enumerate(grid, start=1):
        print(f"[{i}/{len(grid)}] size={s} overlap={o} prepend_title={p}")
        rows.append(run_config(s, o, p, args.corpus_dir, queries, shared))
    meta = {"generated_at": datetime.now().isoformat(timespec="seconds"),
            "duration_s": time.perf_counter() - t0, "n_queries": len(queries)}

    out_md, out_json = Path(args.output), Path(args.json_output)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render(rows, meta), encoding="utf-8")
    out_json.write_text(json.dumps({"meta": meta, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    best = max(rows, key=best_key)
    print(f"Terbaik: size={best['chunk_size_words']} overlap={best['overlap_words']} prepend={best['prepend_title']} MRR={_f(best['mrr'])}")
    print(f"Ditulis: {out_md}\n         {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
