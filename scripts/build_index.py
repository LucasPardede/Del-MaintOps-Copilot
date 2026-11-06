"""
Del-MaintOps Copilot - Build Vector Index
------------------------------------------
Skrip CLI untuk membangun indeks vektor ChromaDB dari korpus dokumen
SOP/kebijakan. Menggunakan chunker Ika (knowledge.chunker) dan
SOPVectorStore (knowledge.vector_store).

Penggunaan:
    uv run python scripts/build_index.py --reset
    uv run python scripts/build_index.py --corpus-dir data/corpus --chunk-size 120 --overlap 20

Pemilik: Lucas Pardede (12S24015)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Tambahkan src/ ke sys.path agar import top-level berfungsi
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from knowledge.retrieval_config import (
    DEFAULT_CHUNK_SIZE_WORDS,
    DEFAULT_OVERLAP_WORDS,
    EMBEDDING_MODEL_NAME,
    PERSIST_DIR,
)
from knowledge.vector_store import SOPVectorStore


def main() -> None:
    """Entry point skrip build_index."""
    parser = argparse.ArgumentParser(
        description="Bangun indeks vektor ChromaDB dari korpus dokumen SOP/kebijakan.",
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default="data/corpus",
        help="Direktori korpus Markdown (default: data/corpus).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE_WORDS,
        help=f"Jumlah kata per chunk (default: {DEFAULT_CHUNK_SIZE_WORDS}).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP_WORDS,
        help=f"Jumlah kata overlap antar chunk (default: {DEFAULT_OVERLAP_WORDS}).",
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=PERSIST_DIR,
        help=f"Direktori penyimpanan ChromaDB (default: {PERSIST_DIR}).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Kosongkan collection sebelum mengindeks ulang.",
    )

    args = parser.parse_args()

    print("=" * 65)
    print("  Del-MaintOps Copilot — Build Vector Index")
    print("=" * 65)
    print(f"  Corpus dir  : {args.corpus_dir}")
    print(f"  Chunk size  : {args.chunk_size} kata")
    print(f"  Overlap     : {args.overlap} kata")
    print(f"  Persist dir : {args.persist_dir}")
    print(f"  Model       : {EMBEDDING_MODEL_NAME}")
    print(f"  Reset       : {args.reset}")
    print("-" * 65)

    # 1. Load & chunk korpus menggunakan chunker Ika (knowledge.chunker)
    print("\n[1/3] Memuat dan memotong korpus dokumen...")
    t0 = time.perf_counter()

    try:
        import importlib
        chunker_mod = importlib.import_module("knowledge.chunker")
        load_and_chunk_corpus = getattr(chunker_mod, "load_and_chunk_corpus")
    except (ImportError, ModuleNotFoundError, AttributeError):
        print(
            "\n[PERINGATAN] Modul 'knowledge.chunker' (milik Ika) belum tersedia.\n"
            "Skrip build_index.py membutuhkan modul chunker milik Ika dan korpus data/corpus.\n"
            "Pastikan Ika telah menyelesaikan implementasi chunker.py dan korpus."
        )
        sys.exit(1)

    chunks = load_and_chunk_corpus(
        corpus_dir=args.corpus_dir,
        chunk_size_words=args.chunk_size,
        overlap_words=args.overlap,
        prepend_title=True,
    )
    t_chunk = time.perf_counter() - t0

    if not chunks:
        print("  [ERROR] Tidak ada chunk yang dihasilkan. Periksa corpus_dir.")
        sys.exit(1)

    # Hitung statistik
    doc_ids = set()
    total_words = 0
    for c in chunks:
        doc_ids.add(c["metadata"]["doc_id"])
        total_words += len(c["text"].split())

    avg_words = total_words / len(chunks) if chunks else 0

    print(f"  Jumlah dokumen : {len(doc_ids)}")
    print(f"  Jumlah chunk   : {len(chunks)}")
    print(f"  Rata-rata kata : {avg_words:.1f} kata/chunk")
    print(f"  Waktu chunking : {t_chunk:.2f} detik")

    # 2. Inisialisasi vector store & index
    print("\n[2/3] Menginisialisasi SOPVectorStore dan mengindeks chunk...")
    t0 = time.perf_counter()

    store = SOPVectorStore(persist_dir=args.persist_dir)
    n_indexed = store.index_chunks(chunks, reset=args.reset)
    t_index = time.perf_counter() - t0

    print(f"  Chunk terindeks  : {n_indexed}")
    print(f"  Total di DB      : {store.count()}")
    print(f"  Waktu indexing   : {t_index:.2f} detik")

    # 3. Ringkasan
    print("\n" + "=" * 65)
    print("  BUILD INDEX SELESAI")
    print("=" * 65)
    print(f"  Dokumen        : {len(doc_ids)}")
    print(f"  Chunk          : {n_indexed}")
    print(f"  Rata-rata kata : {avg_words:.1f} kata/chunk")
    print(f"  Lokasi DB      : {Path(args.persist_dir).resolve()}")
    print(f"  Model          : {EMBEDDING_MODEL_NAME}")
    print(f"  Waktu total    : {t_chunk + t_index:.2f} detik")
    print("=" * 65)


if __name__ == "__main__":
    main()

