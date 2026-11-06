"""
Test Suite 07: SOPVectorStore (ChromaDB persisten + cosine + OOD) - Milestone 3
-------------------------------------------------------------------------------
Memakai model embedding asli (dimuat sekali per modul) dan korpus nyata.
Dilewati otomatis bila chromadb / sentence-transformers belum terpasang.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("chromadb")
pytest.importorskip("sentence_transformers")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import chromadb  # noqa: E402

from knowledge.chunker import load_and_chunk_corpus  # noqa: E402
from knowledge.retrieval_config import OOD_SIMILARITY_THRESHOLD  # noqa: E402
from knowledge.vector_store import SOPVectorStore  # noqa: E402

COLLECTION = "test_sop_fite"
# Harus sama dengan pengaturan SOPVectorStore; Chroma menolak dua klien ber-path sama dengan settings berbeda.
CHROMA_SETTINGS = chromadb.Settings(anonymized_telemetry=False)


@pytest.fixture(scope="module")
def shared_model(tmp_path_factory):
    """Model dimuat sekali untuk seluruh modul (hemat waktu)."""
    holder = SOPVectorStore(persist_dir=tmp_path_factory.mktemp("model_holder"), collection_name="holder")
    return holder._get_model()


@pytest.fixture(scope="module")
def make_store(shared_model):
    def _make(path, name=COLLECTION):
        store = SOPVectorStore(persist_dir=path, collection_name=name)
        store._model = shared_model  # reuse model; hindari muat ulang
        return store

    return _make


@pytest.fixture(scope="module")
def chunks():
    return load_and_chunk_corpus()


@pytest.fixture(scope="module")
def indexed_dir(tmp_path_factory, make_store, chunks):
    path = tmp_path_factory.mktemp("chroma_indexed")
    assert make_store(path).index_chunks(chunks, reset=True) == len(chunks)
    return path


# --- Persistensi ------------------------------------------------------------
def test_index_persists_across_store_instances(indexed_dir, make_store, chunks):
    reopened = make_store(indexed_dir)  # objek baru, path sama
    assert reopened.count() == len(chunks)
    resp = reopened.search("proyektor tidak menyala di ruang kelas")
    assert resp.results, "indeks yang dibuka ulang harus tetap bisa dicari"


def test_persisted_files_exist_on_disk(indexed_dir):
    assert any(indexed_dir.iterdir())
    assert (indexed_dir / "chroma.sqlite3").exists()


# --- Metrik cosine ----------------------------------------------------------
def test_collection_uses_cosine_metric(indexed_dir):
    coll = chromadb.PersistentClient(path=str(indexed_dir), settings=CHROMA_SETTINGS).get_collection(COLLECTION)
    assert (coll.metadata or {}).get("hnsw:space") == "cosine"


def test_similarity_is_one_minus_distance_and_sorted(indexed_dir, make_store):
    resp = make_store(indexed_dir).search("AC bocor meneteskan air", k=5)
    sims = [r.similarity for r in resp.results]
    assert sims == sorted(sims, reverse=True)
    for r in resp.results:
        assert r.similarity == pytest.approx(1.0 - r.distance)
    assert resp.top_similarity == pytest.approx(sims[0])


def test_identical_text_has_near_perfect_similarity(indexed_dir, make_store, chunks):
    target = chunks[0]
    resp = make_store(indexed_dir).search(target["text"], k=1)
    assert resp.results[0].id == target["id"]
    assert resp.results[0].similarity > 0.98


# --- Filter metadata (hybrid search) ----------------------------------------
def test_where_filter_restricts_results(indexed_dir, make_store):
    store = make_store(indexed_dir)
    resp = store.search("prosedur penanganan kerusakan", k=10, where={"category": "listrik"})
    assert resp.results
    assert all(r.metadata["category"] == "listrik" for r in resp.results)


def test_where_filter_on_doc_type(indexed_dir, make_store):
    resp = make_store(indexed_dir).search("aturan prioritas tiket", k=10, where={"doc_type": "kebijakan"})
    assert resp.results
    assert all(r.metadata["doc_type"] == "kebijakan" for r in resp.results)


def test_metadata_is_complete_on_results(indexed_dir, make_store):
    resp = make_store(indexed_dir).search("proyektor mati", k=3)
    required = {"doc_id", "title", "doc_type", "category", "default_urgency", "sla_hours", "source_file", "chunk_index"}
    for r in resp.results:
        assert required <= set(r.metadata)
        assert isinstance(r.metadata["sla_hours"], int)


# --- Penolakan OOD ----------------------------------------------------------
def test_ood_far_query_is_rejected_at_default_threshold(indexed_dir, make_store):
    resp = make_store(indexed_dir).search("resep rendang yang enak")
    assert resp.rejected is True
    assert resp.top_similarity < OOD_SIMILARITY_THRESHOLD
    assert resp.results, "results tetap diisi walau rejected (untuk analisis benchmark)"


def test_rejected_flag_follows_threshold(indexed_dir, make_store):
    store = make_store(indexed_dir)
    q = "proyektor mati total saat kelas berlangsung"
    assert store.search(q, threshold=1.01).rejected is True
    assert store.search(q, threshold=-1.0).rejected is False


def test_relevant_query_not_rejected_at_default_threshold(indexed_dir, make_store):
    resp = make_store(indexed_dir).search("proyektor mati total saat kelas berlangsung")
    assert resp.rejected is False
    assert resp.results[0].metadata["doc_id"] == "SOP-01"


def test_k_larger_than_collection_is_clamped(indexed_dir, make_store, chunks):
    resp = make_store(indexed_dir).search("proyektor", k=10_000)
    assert len(resp.results) == len(chunks)


# --- Upsert idempoten & reset -----------------------------------------------
def test_reindexing_same_chunks_is_idempotent(tmp_path, make_store, chunks):
    store = make_store(tmp_path, "idem")
    store.index_chunks(chunks)
    first = store.count()
    store.index_chunks(chunks)
    assert store.count() == first == len(chunks)


def test_upsert_updates_existing_chunk_text(tmp_path, make_store):
    store = make_store(tmp_path, "upd")
    meta = {"doc_id": "X-01", "title": "Uji", "doc_type": "sop", "category": "uji",
            "default_urgency": "-", "sla_hours": 0, "source_file": "x.md", "chunk_index": 0}
    store.index_chunks([{"id": "X-01-c000", "text": "teks lama tentang proyektor", "metadata": meta}])
    store.index_chunks([{"id": "X-01-c000", "text": "teks baru tentang jaringan", "metadata": meta}])
    assert store.count() == 1
    assert "baru" in store.search("jaringan", k=1, threshold=-1.0).results[0].text


def test_reset_empties_collection(tmp_path, make_store, chunks):
    store = make_store(tmp_path, "rst")
    store.index_chunks(chunks[:5])
    assert store.count() == 5
    store.reset()
    assert store.count() == 0


def test_search_on_empty_collection_is_rejected(tmp_path, make_store):
    resp = make_store(tmp_path, "empty").search("apa saja")
    assert resp.rejected is True and resp.results == [] and resp.top_similarity == 0.0


# --- Validasi masukan -------------------------------------------------------
def test_invalid_metadata_type_gives_clear_error(tmp_path, make_store):
    store = make_store(tmp_path, "bad1")
    bad = {"id": "B-c000", "text": "isi", "metadata": {"doc_id": "B", "tags": ["a", "b"]}}
    with pytest.raises(ValueError, match="tags"):
        store.index_chunks([bad])
    assert store.count() == 0, "validasi harus terjadi sebelum ada data yang tertulis"


def test_missing_required_key_gives_clear_error(tmp_path, make_store):
    store = make_store(tmp_path, "bad2")
    with pytest.raises(ValueError, match="text"):
        store.index_chunks([{"id": "B-c000", "metadata": {"doc_id": "B"}}])


def test_wrong_metric_collection_is_refused(tmp_path, make_store):
    client = chromadb.PersistentClient(path=str(tmp_path), settings=CHROMA_SETTINGS)
    client.create_collection("l2_coll", metadata={"hnsw:space": "l2"})
    with pytest.raises(ValueError, match="cosine"):
        SOPVectorStore(persist_dir=tmp_path, collection_name="l2_coll")
