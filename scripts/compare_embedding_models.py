"""
Del-MaintOps Copilot - Perbandingan Model Embedding
-----------------------------------------------------
Skrip untuk membandingkan tiga model embedding pada data SOP FITE:
  (a) sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  (b) intfloat/multilingual-e5-small  (prefix: "query: " / "passage: ")
  (c) sentence-transformers/all-MiniLM-L6-v2  (English-only baseline)

Metrik: Hit@1, rata-rata cosine ke dokumen target vs non-target,
dimensi vektor, ukuran model, waktu encode.

Output: docs/embedding_model_comparison.md

Penggunaan:
    uv run python scripts/compare_embedding_models.py

Pemilik: Lucas Pardede (12S24015)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Tambahkan src/ ke sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

import numpy as np
from sentence_transformers import SentenceTransformer

from knowledge.sops import SOP_CATALOG

# ---------------------------------------------------------------------------
# Data uji: dokumen (judul + prosedur dari SOP_CATALOG)
# ---------------------------------------------------------------------------

DOCUMENTS: list[dict] = []
for sop_id, sop in SOP_CATALOG.items():
    text = sop["title"] + ". " + " ".join(sop["procedure"])
    DOCUMENTS.append({"id": sop_id, "text": text})

# ---------------------------------------------------------------------------
# Kueri uji bahasa Indonesia (non-literal, sinonim)
# ---------------------------------------------------------------------------

QUERIES: list[dict] = [
    {
        "id": "Q01",
        "query": "alat presentasi di kelas tidak bisa menampilkan gambar",
        "target": "SOP-01",
        "notes": "Sinonim proyektor → alat presentasi",
    },
    {
        "id": "Q02",
        "query": "ruangan terasa panas dan pengatur suhu tidak berfungsi",
        "target": "SOP-02",
        "notes": "Sinonim AC → pengatur suhu, tidak dingin → panas",
    },
    {
        "id": "Q03",
        "query": "mahasiswa tidak bisa mengakses internet di laboratorium",
        "target": "SOP-03",
        "notes": "Sinonim jaringan/LAN → internet, lab → laboratorium",
    },
    {
        "id": "Q04",
        "query": "tempat duduk di area santai sudah patah dan berbahaya",
        "target": "SOP-04",
        "notes": "Sinonim kursi → tempat duduk, saung → area santai",
    },
    {
        "id": "Q05",
        "query": "colokan di ruang server mengeluarkan percikan api",
        "target": "SOP-05",
        "notes": "Sinonim listrik/korsleting → percikan api",
    },
    {
        "id": "Q06",
        "query": "komputer di lab tidak bisa booting dan layar hitam",
        "target": "SOP-06",
        "notes": "Sinonim PC → komputer, boot error",
    },
    {
        "id": "Q07",
        "query": "papan digital interaktif layar sentuhnya tidak merespons",
        "target": "SOP-07",
        "notes": "Sinonim Idea Hub → papan digital interaktif",
    },
    {
        "id": "Q08",
        "query": "kamera keamanan di plafon lab tidak merekam video",
        "target": "SOP-08",
        "notes": "Sinonim CCTV → kamera keamanan",
    },
    {
        "id": "Q09",
        "query": "perangkat pendingin udara bocor air ke lantai",
        "target": "SOP-02",
        "notes": "Sinonim AC → pendingin udara, bocor",
    },
    {
        "id": "Q10",
        "query": "koneksi WiFi lambat saat ujian praktikum berlangsung",
        "target": "SOP-03",
        "notes": "Sinonim jaringan → WiFi, konteks praktikum",
    },
]

# ---------------------------------------------------------------------------
# Konfigurasi model
# ---------------------------------------------------------------------------

MODELS_CONFIG = [
    {
        "name": "paraphrase-multilingual-MiniLM-L12-v2",
        "full_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "query_prefix": "",
        "passage_prefix": "",
    },
    {
        "name": "multilingual-e5-small",
        "full_name": "intfloat/multilingual-e5-small",
        "query_prefix": "query: ",
        "passage_prefix": "passage: ",
    },
    {
        "name": "all-MiniLM-L6-v2",
        "full_name": "sentence-transformers/all-MiniLM-L6-v2",
        "query_prefix": "",
        "passage_prefix": "",
    },
]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Hitung cosine similarity antara dua vektor."""
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def evaluate_model(config: dict) -> dict:
    """Evaluasi satu model embedding terhadap semua kueri uji."""
    print(f"\n--- Evaluasi: {config['name']} ---")
    model = SentenceTransformer(config["full_name"])
    dim = model.get_sentence_embedding_dimension()

    # Hitung ukuran model (jumlah parameter)
    num_params = sum(p.numel() for p in model.parameters())
    model_size_mb = sum(
        p.numel() * p.element_size() for p in model.parameters()
    ) / (1024 * 1024)

    # Encode semua dokumen
    doc_texts = [
        config["passage_prefix"] + d["text"] for d in DOCUMENTS
    ]
    t0 = time.perf_counter()
    doc_embeddings = model.encode(doc_texts, normalize_embeddings=True)
    t_doc = time.perf_counter() - t0

    # Encode semua kueri
    query_texts = [
        config["query_prefix"] + q["query"] for q in QUERIES
    ]
    t0 = time.perf_counter()
    query_embeddings = model.encode(query_texts, normalize_embeddings=True)
    t_query = time.perf_counter() - t0

    # Evaluasi Hit@1 dan similarity
    hit_at_1 = 0
    total_target_sim = 0.0
    total_nontarget_sim = 0.0
    nontarget_count = 0

    query_details = []

    for qi, q in enumerate(QUERIES):
        q_emb = query_embeddings[qi]
        target_idx = None
        sims = []

        for di, d in enumerate(DOCUMENTS):
            sim = cosine_similarity(q_emb, doc_embeddings[di])
            sims.append((d["id"], sim))
            if d["id"] == q["target"]:
                target_idx = di

        # Urutkan menurun
        sims.sort(key=lambda x: x[1], reverse=True)
        rank1_id = sims[0][0]
        rank1_sim = sims[0][1]

        target_sim = cosine_similarity(q_emb, doc_embeddings[target_idx])
        total_target_sim += target_sim

        for doc_id, sim in sims:
            if doc_id != q["target"]:
                total_nontarget_sim += sim
                nontarget_count += 1

        is_hit = rank1_id == q["target"]
        if is_hit:
            hit_at_1 += 1

        query_details.append({
            "id": q["id"],
            "query": q["query"],
            "target": q["target"],
            "rank1": rank1_id,
            "rank1_sim": rank1_sim,
            "target_sim": target_sim,
            "hit": is_hit,
        })

    avg_target_sim = total_target_sim / len(QUERIES)
    avg_nontarget_sim = total_nontarget_sim / nontarget_count if nontarget_count else 0

    result = {
        "name": config["name"],
        "full_name": config["full_name"],
        "dim": dim,
        "num_params": num_params,
        "model_size_mb": model_size_mb,
        "t_doc_encode": t_doc,
        "t_query_encode": t_query,
        "hit_at_1": hit_at_1,
        "hit_at_1_rate": hit_at_1 / len(QUERIES),
        "avg_target_sim": avg_target_sim,
        "avg_nontarget_sim": avg_nontarget_sim,
        "query_details": query_details,
    }

    print(f"  Hit@1: {hit_at_1}/{len(QUERIES)} ({result['hit_at_1_rate']:.0%})")
    print(f"  Avg target sim: {avg_target_sim:.4f}")
    print(f"  Avg non-target sim: {avg_nontarget_sim:.4f}")
    print(f"  Dimensi: {dim}, Ukuran: {model_size_mb:.1f} MB")
    print(f"  Waktu encode dokumen: {t_doc:.3f}s, kueri: {t_query:.3f}s")

    return result


def generate_report(results: list[dict]) -> str:
    """Buat laporan Markdown dari hasil evaluasi."""
    lines = [
        "# Perbandingan Model Embedding untuk Pipeline Retrieval SOP FITE",
        "",
        "> Dokumen ini dihasilkan secara otomatis oleh `scripts/compare_embedding_models.py`.",
        "> Semua angka berasal dari eksekusi nyata, bukan dikarang.",
        "",
        "## 1. Tujuan",
        "",
        "Membandingkan tiga model embedding untuk memilih model terbaik bagi",
        "pipeline pencarian semantik SOP/kebijakan FITE berbahasa Indonesia.",
        "",
        "## 2. Model yang Dibandingkan",
        "",
        "| # | Model | Bahasa | Dimensi | Ukuran (MB) | Parameter |",
        "|---|-------|--------|---------|-------------|-----------|",
    ]

    for i, r in enumerate(results, 1):
        lang = "Multilingual" if "multilingual" in r["name"].lower() else "English"
        lines.append(
            f"| {i} | `{r['full_name']}` | {lang} | {r['dim']} | "
            f"{r['model_size_mb']:.1f} | {r['num_params']:,} |"
        )

    lines += [
        "",
        "## 3. Data Uji",
        "",
        f"- **Dokumen**: {len(DOCUMENTS)} SOP dari `SOP_CATALOG` (judul + prosedur)",
        f"- **Kueri**: {len(QUERIES)} kueri bahasa Indonesia non-literal (sinonim)",
        "",
        "### Daftar Kueri",
        "",
        "| ID | Kueri | Target | Catatan |",
        "|----|-------|--------|---------|",
    ]
    for q in QUERIES:
        lines.append(f"| {q['id']} | {q['query']} | {q['target']} | {q['notes']} |")

    lines += [
        "",
        "## 4. Hasil Perbandingan",
        "",
        "### 4.1 Ringkasan Metrik",
        "",
        "| Metrik | " + " | ".join(r["name"] for r in results) + " |",
        "|--------|" + "|".join("-----" for _ in results) + "|",
        "| Hit@1 | " + " | ".join(
            f"{r['hit_at_1']}/{len(QUERIES)} ({r['hit_at_1_rate']:.0%})"
            for r in results
        ) + " |",
        "| Avg Cosine (target) | " + " | ".join(
            f"{r['avg_target_sim']:.4f}" for r in results
        ) + " |",
        "| Avg Cosine (non-target) | " + " | ".join(
            f"{r['avg_nontarget_sim']:.4f}" for r in results
        ) + " |",
        "| Separation (target - non-target) | " + " | ".join(
            f"{r['avg_target_sim'] - r['avg_nontarget_sim']:.4f}" for r in results
        ) + " |",
        "| Dimensi vektor | " + " | ".join(
            str(r["dim"]) for r in results
        ) + " |",
        "| Ukuran model (MB) | " + " | ".join(
            f"{r['model_size_mb']:.1f}" for r in results
        ) + " |",
        "| Waktu encode dokumen (s) | " + " | ".join(
            f"{r['t_doc_encode']:.3f}" for r in results
        ) + " |",
        "| Waktu encode kueri (s) | " + " | ".join(
            f"{r['t_query_encode']:.3f}" for r in results
        ) + " |",
    ]

    lines += [
        "",
        "### 4.2 Detail Hit@1 per Kueri",
        "",
        "| Kueri | Target | " + " | ".join(
            f"{r['name']} (rank1 / sim)" for r in results
        ) + " |",
        "|-------|--------|" + "|".join("-----" for _ in results) + "|",
    ]

    for qi in range(len(QUERIES)):
        row = f"| {QUERIES[qi]['id']} | {QUERIES[qi]['target']} | "
        for r in results:
            d = r["query_details"][qi]
            hit_mark = "✅" if d["hit"] else "❌"
            row += f"{d['rank1']} ({d['target_sim']:.3f}) {hit_mark} | "
        lines.append(row)

    lines += [
        "",
        "## 5. Analisis & Kesimpulan",
        "",
    ]

    # Pilih model terbaik berdasarkan Hit@1, lalu avg target sim
    best = max(results, key=lambda r: (r["hit_at_1_rate"], r["avg_target_sim"]))

    lines += [
        f"### Model Terpilih: `{best['full_name']}`",
        "",
        "**Alasan pemilihan:**",
        "",
        f"1. **Hit@1 tertinggi**: {best['hit_at_1']}/{len(QUERIES)} "
        f"({best['hit_at_1_rate']:.0%}) — model ini paling akurat menempatkan",
        "   dokumen target di peringkat 1 untuk kueri sinonim bahasa Indonesia.",
        f"2. **Rata-rata cosine similarity ke dokumen target**: {best['avg_target_sim']:.4f}",
        f"   — separation dari non-target: {best['avg_target_sim'] - best['avg_nontarget_sim']:.4f}.",
        f"3. **Dukungan bahasa**: Model ini mendukung bahasa Indonesia secara native",
        "   (multilingual), berbeda dengan all-MiniLM-L6-v2 yang hanya English.",
        f"4. **Ukuran efisien**: {best['model_size_mb']:.1f} MB dengan dimensi "
        f"{best['dim']}, cocok untuk deployment di lingkungan kampus.",
        "",
    ]

    # Catatan tentang E5
    e5 = next((r for r in results if "e5" in r["name"]), None)
    if e5:
        lines += [
            "### Catatan tentang model E5",
            "",
            f"Model `{e5['full_name']}` memerlukan prefix `query: ` dan `passage: ` "
            "saat encoding. Jika model E5 dipilih, `QUERY_PREFIX` dan "
            "`PASSAGE_PREFIX` di `retrieval_config.py` harus diperbarui.",
            "",
        ]

    return "\n".join(lines)


def main() -> None:
    """Entry point."""
    print("=" * 65)
    print("  Perbandingan Model Embedding — Del-MaintOps Copilot")
    print("=" * 65)

    results = []
    for config in MODELS_CONFIG:
        result = evaluate_model(config)
        results.append(result)

    # Generate laporan
    report = generate_report(results)
    output_path = _REPO_ROOT / "docs" / "embedding_model_comparison.md"
    output_path.write_text(report, encoding="utf-8")
    print(f"\nLaporan ditulis ke: {output_path}")

    # Tampilkan model terpilih
    best = max(results, key=lambda r: (r["hit_at_1_rate"], r["avg_target_sim"]))
    print(f"\n✅ Model terpilih: {best['full_name']}")
    print(f"   Hit@1: {best['hit_at_1']}/{len(QUERIES)} ({best['hit_at_1_rate']:.0%})")
    print(f"   Avg target sim: {best['avg_target_sim']:.4f}")


if __name__ == "__main__":
    main()

