#!/usr/bin/env python3
"""Eksperimen chunking dan retrieval untuk Milestone 3.

Jalankan dari root repository:
  uv run python scripts/experiment_chunking.py
  uv run python scripts/experiment_chunking.py --model paraphrase-multilingual-MiniLM-L12-v2

Membutuhkan sentence-transformers (yang membawa transformers/tokenizers).
Hasil aktual ditulis ke reports/chunking_experiment_results.json dan .csv.
Tidak mengubah korpus maupun parameter default chunker.py.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.knowledge.chunker import load_and_chunk_corpus  # noqa: E402

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
CONFIGS = [
    (60, 10),
    (80, 15),
    (100, 15),
    (120, 20),
    (150, 30),
]
QUERIES = [
    {"id": "Q01", "type": "relevan", "query": "Bagaimana menangani proyektor yang tidak menampilkan gambar?", "expected_doc_ids": ["SOP-01"]},
    {"id": "Q02", "type": "sinonim", "query": "Pendingin ruangan mengeluarkan air dan tidak terasa dingin", "expected_doc_ids": ["SOP-02"]},
    {"id": "Q03", "type": "sinonim", "query": "Koneksi internet komputer laboratorium terputus", "expected_doc_ids": ["SOP-03"]},
    {"id": "Q04", "type": "kontekstual", "query": "Apa tindakan ketika jaringan mati saat praktikum berlangsung?", "expected_doc_ids": ["SOP-03", "KB-12"]},
    {"id": "Q05", "type": "ambigu", "query": "Siapa yang boleh menangani masalah listrik di ruang server?", "expected_doc_ids": ["SOP-05", "KB-10", "KB-14"]},
    {"id": "Q06", "type": "ambigu", "query": "Apa yang harus dilakukan jika perangkat presentasi rusak dan unit pengganti diperlukan?", "expected_doc_ids": ["SOP-01", "KB-13"]},
    {"id": "Q07", "type": "relevan", "query": "Bagaimana cara melaporkan kerusakan fasilitas dan membuat tiket?", "expected_doc_ids": ["KB-11"]},
    {"id": "Q08", "type": "out_of_domain", "query": "Bagaimana resep membuat nasi goreng seafood?", "expected_doc_ids": []},
    {"id": "Q09", "type": "out_of_domain", "query": "Siapa pemenang pertandingan sepak bola tadi malam?", "expected_doc_ids": []},
]


def evaluate(chunks: list[dict[str, Any]], model: Any, tokenizer: Any, max_tokens: int,
             config: tuple[int, int], prepend_title: bool) -> dict[str, Any]:
    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    doc_ids = [c["metadata"]["doc_id"] for c in chunks]

    token_lengths = [
        len(tokenizer(text, add_special_tokens=True, truncation=False)["input_ids"])
        for text in texts
    ]
    # SentenceTransformer uses its max_seq_length during encoding. Count before encoding
    # to expose truncation risk rather than silently treating truncated text as complete.
    embeddings = model.encode(
        texts, convert_to_numpy=True, normalize_embeddings=True,
        show_progress_bar=False,
    )
    rows: list[dict[str, Any]] = []
    in_domain_hits_1, in_domain_hits_3, reciprocal_ranks = [], [], []
    target_cosines: list[float] = []
    ood_top_scores: list[float] = []

    for q in QUERIES:
        qv = model.encode([q["query"]], convert_to_numpy=True,
                          normalize_embeddings=True, show_progress_bar=False)[0]
        scores = embeddings @ qv
        order = scores.argsort()[::-1]
        top = [
            {"chunk_id": ids[i], "doc_id": doc_ids[i], "cosine_similarity": float(scores[i])}
            for i in order[:5]
        ]
        expected = set(q["expected_doc_ids"])
        if expected:
            ranked_docs = [doc_ids[i] for i in order]
            first_rank = next((rank for rank, d in enumerate(ranked_docs, 1) if d in expected), None)
            in_domain_hits_1.append(1 if first_rank == 1 else 0)
            in_domain_hits_3.append(1 if first_rank is not None and first_rank <= 3 else 0)
            reciprocal_ranks.append(1 / first_rank if first_rank else 0)
            target_cosines.append(max(float(scores[i]) for i in order if doc_ids[i] in expected))
        else:
            ood_top_scores.append(float(scores[order[0]]))
        rows.append({
            "query_id": q["id"], "query_type": q["type"], "query": q["query"],
            "expected_doc_ids": q["expected_doc_ids"], "top_results": top,
            "top1_score": float(scores[order[0]]),
            "top1_is_expected": bool(expected and doc_ids[order[0]] in expected) if expected else None,
        })

    return {
        "chunk_size_words": config[0], "overlap_words": config[1],
        "prepend_title": prepend_title, "n_chunks": len(chunks),
        "token_max": max(token_lengths), "token_p95": sorted(token_lengths)[int(.95 * (len(token_lengths)-1))],
        "model_max_seq_length": max_tokens,
        "chunks_over_model_limit": sum(n > max_tokens for n in token_lengths),
        "hit_at_1": sum(in_domain_hits_1) / len(in_domain_hits_1),
        "hit_at_3": sum(in_domain_hits_3) / len(in_domain_hits_3),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "mean_best_target_cosine": sum(target_cosines) / len(target_cosines),
        "ood_top1_scores": ood_top_scores,
        "query_results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--corpus-dir", default="data/corpus")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise SystemExit(
            "Dependensi belum tersedia. Instal dengan: uv add sentence-transformers"
        ) from exc

    model = SentenceTransformer(args.model)
    tokenizer = model.tokenizer
    max_tokens = int(model.max_seq_length)
    all_results = []

    for size, overlap in CONFIGS:
        for use_title in (True, False):
            chunks = load_and_chunk_corpus(
                args.corpus_dir, chunk_size_words=size,
                overlap_words=overlap, prepend_title=use_title,
            )
            result = evaluate(chunks, model, tokenizer, max_tokens,
                              (size, overlap), use_title)
            all_results.append(result)
            print(
                f"size={size:3} overlap={overlap:2} title={use_title!s:5} "
                f"chunks={result['n_chunks']:3} "
                f"Hit@1={result['hit_at_1']:.3f} Hit@3={result['hit_at_3']:.3f} "
                f"MRR={result['mrr']:.3f} "
                f"over_limit={result['chunks_over_model_limit']}"
            )

    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": args.model,
        "model_max_seq_length": max_tokens,
        "query_set": QUERIES,
        "results": all_results,
        "notes": (
            "Cosine dihitung dari embedding ternormalisasi. Hit@k menghitung dokumen "
            "target yang muncul pada k hasil teratas. OOD hanya melaporkan skor top-1; "
            "ambang penolakan harus ditentukan dari validasi, bukan ditebak."
        ),
    }
    json_path = output_dir / "chunking_experiment_results.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = output_dir / "chunking_experiment_summary.csv"
    fields = [
        "chunk_size_words", "overlap_words", "prepend_title", "n_chunks",
        "token_max", "token_p95", "model_max_seq_length", "chunks_over_model_limit",
        "hit_at_1", "hit_at_3", "mrr", "mean_best_target_cosine",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: row[k] for k in fields} for row in all_results)

    print(f"\nHasil tersimpan:\n- {json_path}\n- {csv_path}")
    print("Pilih parameter berdasarkan gabungan Hit@k/MRR, cosine target, dan nol pemotongan token.")


if __name__ == "__main__":
    main()
