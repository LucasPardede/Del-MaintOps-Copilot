"""
Del-MaintOps Copilot - SOPVectorStore (ChromaDB Persistent Vector Store)
------------------------------------------------------------------------
Modul penyimpanan vektor persisten berbasis ChromaDB untuk pipeline
pencarian semantik SOP/kebijakan fasilitas FITE. Mendukung:
- Dense embedding via Sentence-Transformers (model dikonfigurasi di
  retrieval_config.py).
- Penyimpanan persisten di disk (bukan in-memory).
- Pencarian cosine similarity dengan penolakan kueri out-of-domain (OOD).
- Filter metadata untuk hybrid search (parameter ``where``).

Pemilik: Lucas Pardede (12S24015)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from knowledge.retrieval_config import (
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL_NAME,
    OOD_SIMILARITY_THRESHOLD,
    PASSAGE_PREFIX,
    PERSIST_DIR,
    QUERY_PREFIX,
)

logger = logging.getLogger(__name__)

# Tipe metadata yang diperbolehkan ChromaDB
_ALLOWED_META_TYPES = (str, int, float, bool)

# Root repo: dua level di atas file ini (src/knowledge/vector_store.py)
_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Data-classes hasil pencarian
# ---------------------------------------------------------------------------


@dataclass
class SearchResult:
    """Satu hasil pencarian vektor beserta skor kesamaan.

    Attributes:
        id: Identifier unik chunk (mis. ``SOP-01-c000``).
        text: Isi teks chunk.
        metadata: Metadata chunk (doc_id, title, category, dll.).
        similarity: Skor kesamaan kosinus (1 = identik, 0 = ortogonal).
        distance: Jarak kosinus mentah dari ChromaDB (``similarity = 1 - distance``).
    """

    id: str
    text: str
    metadata: Dict[str, Any]
    similarity: float
    distance: float


@dataclass
class SearchResponse:
    """Respons pencarian lengkap, termasuk flag penolakan OOD.

    Attributes:
        query: Kueri asli pengguna.
        results: Daftar :class:`SearchResult` terurut menurun berdasarkan
            similarity. Tetap diisi meskipun ``rejected=True`` (untuk
            keperluan analisis benchmark).
        top_similarity: Similarity tertinggi di antara semua hasil.
        threshold: Ambang batas OOD yang digunakan.
        rejected: ``True`` jika ``top_similarity < threshold``, menandakan
            kueri dianggap out-of-domain.
    """

    query: str
    results: List[SearchResult]
    top_similarity: float
    threshold: float
    rejected: bool


# ---------------------------------------------------------------------------
# Vector Store utama
# ---------------------------------------------------------------------------


class SOPVectorStore:
    """Penyimpanan vektor persisten ChromaDB untuk chunk SOP/kebijakan FITE.

    Parameters:
        persist_dir: Path direktori penyimpanan ChromaDB. Jika relatif,
            di-resolve terhadap root repo (dua level di atas modul ini).
        collection_name: Nama collection ChromaDB.
        model_name: Nama model Sentence-Transformers untuk embedding.

    Contoh penggunaan::

        store = SOPVectorStore()
        n = store.index_chunks(chunks, reset=True)
        response = store.search("proyektor mati di ruang kelas")
        if not response.rejected:
            for r in response.results:
                print(r.id, r.similarity)
    """

    def __init__(
        self,
        persist_dir: str | Path = PERSIST_DIR,
        collection_name: str = COLLECTION_NAME,
        model_name: str = EMBEDDING_MODEL_NAME,
    ) -> None:
        # Resolve path relatif terhadap root repo
        persist_path = Path(persist_dir)
        if not persist_path.is_absolute():
            persist_path = _REPO_ROOT / persist_path
        self._persist_dir = persist_path

        self._collection_name = collection_name
        self._model_name = model_name

        # Lazy-loaded: model SentenceTransformer dimuat saat pertama kali dibutuhkan
        self._model = None

        # Inisialisasi ChromaDB PersistentClient
        import chromadb

        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        # Verifikasi bahwa collection menggunakan metrik cosine
        coll_meta = self._collection.metadata or {}
        space = coll_meta.get("hnsw:space", "l2")
        if space != "cosine":
            raise ValueError(
                f"Collection '{self._collection_name}' menggunakan metrik "
                f"'{space}', bukan 'cosine'. Hapus direktori "
                f"'{self._persist_dir}' lalu buat ulang, atau gunakan "
                f"collection baru."
            )

        logger.info(
            "SOPVectorStore diinisialisasi: persist_dir=%s, collection=%s, "
            "model=%s, jumlah_chunk=%d",
            self._persist_dir,
            self._collection_name,
            self._model_name,
            self._collection.count(),
        )

    # -- Private helpers ------------------------------------------------------

    def _get_model(self):
        """Memuat model SentenceTransformer secara lazy (saat pertama dibutuhkan)."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)
            dim_func = getattr(self._model, "get_embedding_dimension", None) or getattr(
                self._model, "get_sentence_embedding_dimension"
            )
            logger.info(
                "Model '%s' dimuat (dimensi=%d).",
                self._model_name,
                dim_func(),
            )
        return self._model

    def _encode(
        self,
        texts: list[str],
        *,
        is_query: bool = False,
    ) -> list[list[float]]:
        """Encode teks menjadi embedding vektor ternormalisasi.

        Parameters:
            texts: Daftar teks yang akan di-encode.
            is_query: Jika ``True``, tambahkan ``QUERY_PREFIX``; jika
                ``False``, tambahkan ``PASSAGE_PREFIX``.

        Returns:
            Daftar vektor embedding (list of list of float).
        """
        prefix = QUERY_PREFIX if is_query else PASSAGE_PREFIX
        if prefix:
            texts = [prefix + t for t in texts]

        model = self._get_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        # Konversi numpy array ke list of list of float
        return embeddings.tolist()

    @staticmethod
    def _validate_chunk(chunk: dict) -> None:
        """Validasi bahwa chunk memenuhi kontrak C.

        Raises:
            ValueError: Jika chunk tidak memiliki kunci wajib atau
                metadata mengandung tipe data yang tidak diperbolehkan.
        """
        for key in ("id", "text", "metadata"):
            if key not in chunk:
                raise ValueError(
                    f"Chunk harus memiliki kunci '{key}'. "
                    f"Kunci yang ditemukan: {list(chunk.keys())}"
                )

        if not isinstance(chunk["metadata"], dict):
            raise ValueError(
                f"Chunk '{chunk['id']}': metadata harus bertipe dict, "
                f"ditemukan {type(chunk['metadata']).__name__}."
            )

        for mk, mv in chunk["metadata"].items():
            if not isinstance(mv, _ALLOWED_META_TYPES):
                raise ValueError(
                    f"Chunk '{chunk['id']}': metadata['{mk}'] bertipe "
                    f"{type(mv).__name__} (nilai: {mv!r}). "
                    f"ChromaDB hanya menerima str/int/float/bool."
                )

    # -- Indexing -------------------------------------------------------------

    def index_chunks(self, chunks: list[dict], *, reset: bool = False) -> int:
        """Indeks (upsert) daftar chunk ke dalam collection ChromaDB.

        Parameters:
            chunks: Daftar chunk dengan kunci ``id``, ``text``, dan
                ``metadata`` (sesuai kontrak C).
            reset: Jika ``True``, kosongkan collection sebelum mengindeks.

        Returns:
            Jumlah chunk yang berhasil di-indeks.

        Raises:
            ValueError: Jika chunk tidak memiliki kunci wajib atau
                metadata mengandung tipe data selain str/int/float/bool.
        """
        if reset:
            self.reset()

        if not chunks:
            logger.warning("index_chunks dipanggil dengan daftar chunk kosong.")
            return 0

        # Validasi semua chunk dulu sebelum proses apapun
        for chunk in chunks:
            self._validate_chunk(chunk)

        # Siapkan data untuk upsert
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict] = []

        for chunk in chunks:
            ids.append(chunk["id"])
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"])

        # Hitung embedding untuk semua dokumen sekaligus (batch)
        embeddings = self._encode(documents, is_query=False)

        # Upsert ke ChromaDB dalam batch (ChromaDB mendukung batch besar)
        # Bagi menjadi batch 5000 untuk menghindari batasan memori
        batch_size = 5000
        for i in range(0, len(ids), batch_size):
            end = min(i + batch_size, len(ids))
            self._collection.upsert(
                ids=ids[i:end],
                embeddings=embeddings[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end],
            )

        indexed_count = len(ids)
        logger.info(
            "Berhasil mengindeks %d chunk ke collection '%s'.",
            indexed_count,
            self._collection_name,
        )
        return indexed_count

    # -- Search ---------------------------------------------------------------

    def search(
        self,
        query: str,
        k: int = DEFAULT_TOP_K,
        where: dict | None = None,
        threshold: float | None = None,
    ) -> SearchResponse:
        """Cari chunk paling relevan terhadap kueri menggunakan cosine similarity.

        Parameters:
            query: Teks kueri pencarian.
            k: Jumlah hasil teratas yang dikembalikan.
            where: Filter metadata ChromaDB (opsional). Contoh:
                ``{"category": "listrik"}``.
            threshold: Ambang batas similarity OOD. Jika ``None``,
                menggunakan ``OOD_SIMILARITY_THRESHOLD`` dari config.

        Returns:
            :class:`SearchResponse` berisi hasil pencarian dan flag OOD.
            Hasil tetap diisi walau ``rejected=True`` agar dapat
            digunakan untuk analisis benchmark.
        """
        if threshold is None:
            threshold = OOD_SIMILARITY_THRESHOLD

        current_count = self._collection.count()

        # Tangani collection kosong
        if current_count == 0:
            logger.warning(
                "search() dipanggil pada collection kosong '%s'.",
                self._collection_name,
            )
            return SearchResponse(
                query=query,
                results=[],
                top_similarity=0.0,
                threshold=threshold,
                rejected=True,
            )

        # Pastikan k tidak melebihi jumlah data
        n_results = min(k, current_count)

        # Encode kueri
        query_embedding = self._encode([query], is_query=True)[0]

        # Bangun argumen query
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where is not None:
            query_kwargs["where"] = where

        # Eksekusi query
        raw = self._collection.query(**query_kwargs)

        # Parse hasil — ChromaDB mengembalikan list of lists
        result_ids: list[str] = raw["ids"][0] if raw["ids"] else []
        result_docs: list[str] = raw["documents"][0] if raw["documents"] else []
        result_metas: list[dict] = raw["metadatas"][0] if raw["metadatas"] else []
        result_dists: list[float] = raw["distances"][0] if raw["distances"] else []

        results: list[SearchResult] = []
        for rid, doc, meta, dist in zip(
            result_ids, result_docs, result_metas, result_dists
        ):
            similarity = 1.0 - dist
            results.append(
                SearchResult(
                    id=rid,
                    text=doc,
                    metadata=meta,
                    similarity=similarity,
                    distance=dist,
                )
            )

        # Hitung top_similarity
        top_similarity = results[0].similarity if results else 0.0

        # Tentukan apakah kueri ditolak (OOD)
        rejected = top_similarity < threshold

        return SearchResponse(
            query=query,
            results=results,
            top_similarity=top_similarity,
            threshold=threshold,
            rejected=rejected,
        )

    # -- Utility --------------------------------------------------------------

    def count(self) -> int:
        """Mengembalikan jumlah chunk dalam collection saat ini."""
        return self._collection.count()

    def reset(self) -> None:
        """Mengosongkan seluruh isi collection (delete lalu recreate)."""
        self._client.delete_collection(name=self._collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Collection '%s' berhasil di-reset.", self._collection_name
        )
