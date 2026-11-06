"""
Del-MaintOps Copilot - Konfigurasi Pipeline Retrieval & Vector Store
--------------------------------------------------------------------
Modul konstanta terpusat untuk pipeline embedding, chunking, dan
pencarian semantik berbasis ChromaDB. Semua parameter default
didefinisikan di sini agar mudah dikalibrasi tanpa mengubah logika
bisnis di modul lain.

Pemilik: Lucas Pardede (12S24015)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Penyimpanan ChromaDB
# ---------------------------------------------------------------------------
PERSIST_DIR: str = "chroma_db"
"""Direktori penyimpanan persisten ChromaDB (relatif terhadap root repo)."""

COLLECTION_NAME: str = "sop_fite"
"""Nama collection ChromaDB untuk seluruh chunk SOP/kebijakan FITE."""

# ---------------------------------------------------------------------------
# Model Embedding
# ---------------------------------------------------------------------------
EMBEDDING_MODEL_NAME: str = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
"""Nama model Sentence-Transformers yang digunakan untuk dense embedding."""

QUERY_PREFIX: str = ""
"""Prefix yang ditambahkan ke kueri sebelum encoding (kosong untuk model
paraphrase-multilingual; diisi 'query: ' jika memakai model E5)."""

PASSAGE_PREFIX: str = ""
"""Prefix yang ditambahkan ke dokumen/passage sebelum encoding."""

# ---------------------------------------------------------------------------
# Parameter Chunking (default untuk chunker Ika)
# ---------------------------------------------------------------------------
DEFAULT_CHUNK_SIZE_WORDS: int = 120
"""Jumlah kata per chunk (word-aware chunking)."""

DEFAULT_OVERLAP_WORDS: int = 20
"""Jumlah kata overlap antar chunk berurutan."""

# ---------------------------------------------------------------------------
# Parameter Pencarian
# ---------------------------------------------------------------------------
DEFAULT_TOP_K: int = 3
"""Jumlah hasil teratas yang dikembalikan oleh search()."""

OOD_SIMILARITY_THRESHOLD: float = 0.35
"""Ambang batas similarity minimum. Kueri dengan top_similarity di bawah
nilai ini dianggap out-of-domain (OOD) dan ditolak.
PLACEHOLDER — dikalibrasi oleh Geralda setelah benchmark."""

