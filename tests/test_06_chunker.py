"""
Test Suite 06: Chunker Korpus (Milestone 3)
-------------------------------------------
Memvalidasi knowledge.chunker: pemotongan tidak memutus kata/kalimat, overlap,
validasi parameter, determinisme, singkatan Indonesia, dan metadata primitif.
Tidak membutuhkan model embedding maupun ChromaDB.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from knowledge.chunker import (  # noqa: E402
    CorpusFormatError,
    _body_words,
    chunk_document,
    clean_text,
    load_and_chunk_corpus,
    parse_front_matter,
    self_check,
    split_sentences,
)

CORPUS_DIR = Path(__file__).resolve().parent.parent / "data" / "corpus"
META = {
    "doc_id": "SOP-99",
    "title": "Dokumen Uji",
    "doc_type": "sop",
    "category": "uji",
    "default_urgency": "sedang",
    "sla_hours": 24,
}


def _synthetic_text(n_sentences: int = 40, words_per_sentence: int = 6) -> str:
    """Teks sintetis: tiap kata unik agar posisi/overlap mudah diperiksa."""
    sents, k = [], 0
    for _ in range(n_sentences):
        words = [f"kata{k + j}" for j in range(words_per_sentence)]
        k += words_per_sentence
        sents.append(" ".join(words).capitalize() + ".")
    return " ".join(sents)


def _chunk(text: str, size: int = 30, overlap: int = 12, **kw):
    return chunk_document(text, "SOP-99_uji.md", dict(META), chunk_size_words=size, overlap_words=overlap, **kw)


# --- Tidak memutus kata/kalimat --------------------------------------------
def test_chunks_never_split_words():
    text = _synthetic_text()
    source_words = set(text.split())
    for c in _chunk(text):
        for w in _body_words(c):
            assert w in source_words, f"kata terpotong: {w!r}"


def test_chunks_end_at_sentence_boundary_when_sentences_fit():
    for c in _chunk(_synthetic_text()):
        assert _body_words(c)[-1].endswith("."), c["id"]


def test_chunk_body_never_exceeds_size():
    for size, overlap in [(20, 0), (30, 12), (45, 10)]:
        for c in _chunk(_synthetic_text(), size, overlap):
            assert len(_body_words(c)) <= size


def test_overlong_sentence_is_split_by_words_not_mid_word():
    long_sentence = " ".join(f"w{i}" for i in range(100)) + "."
    chunks = _chunk(long_sentence, size=30, overlap=5)
    assert len(chunks) >= 4
    source = set(long_sentence.split())
    assert all(w in source for c in chunks for w in _body_words(c))


# --- Overlap ----------------------------------------------------------------
def test_overlap_present_and_within_limit():
    chunks = _chunk(_synthetic_text(), size=30, overlap=12)
    assert len(chunks) > 2
    report = self_check(chunks, 30, 12)
    assert report["overlap_over_limit"] == []
    assert report["pairs_with_zero_overlap"] == 0
    assert 0 < report["avg_overlap_words"] <= 12


def test_zero_overlap_means_no_shared_words():
    chunks = _chunk(_synthetic_text(), size=30, overlap=0)
    for a, b in zip(chunks, chunks[1:]):
        assert not set(_body_words(a)) & set(_body_words(b))


def test_overlap_shares_tail_of_previous_chunk():
    chunks = _chunk(_synthetic_text(), size=30, overlap=12)
    prev, nxt = _body_words(chunks[0]), _body_words(chunks[1])
    k = 0
    for i in range(1, 13):
        if prev[-i:] == nxt[:i]:
            k = i
    assert k > 0


def test_all_source_words_are_covered():
    text = _synthetic_text()
    covered = {w for c in _chunk(text) for w in _body_words(c)}
    assert covered == set(text.split())


# --- Validasi parameter -----------------------------------------------------
@pytest.mark.parametrize(
    "size,overlap",
    [(0, 0), (-5, 0), (30, -1), (30, 30), (30, 45), (30.5, 5), (30, 2.5), (True, 0)],
)
def test_invalid_parameters_rejected(size, overlap):
    with pytest.raises(ValueError):
        chunk_document("Teks uji. Kalimat kedua.", "x.md", dict(META), chunk_size_words=size, overlap_words=overlap)


def test_missing_doc_id_rejected():
    with pytest.raises(ValueError):
        chunk_document("Teks.", "x.md", {"title": "Judul"})


def test_non_primitive_metadata_rejected():
    bad = dict(META, tags=["a", "b"])
    with pytest.raises(TypeError):
        chunk_document("Teks uji.", "x.md", bad)


def test_empty_text_returns_no_chunks():
    assert _chunk("   \n\n  ") == []


# --- Determinisme -----------------------------------------------------------
def test_chunking_is_deterministic():
    text = _synthetic_text()
    assert _chunk(text) == _chunk(text)


def test_clean_text_is_idempotent_and_normalises_whitespace():
    raw = "Baris  satu\t dengan   spasi\r\n\r\n\r\n\r\nBaris dua​."
    cleaned = clean_text(raw)
    assert "\r" not in cleaned and "\t" not in cleaned and "​" not in cleaned
    assert "  " not in cleaned and "\n\n\n" not in cleaned
    assert clean_text(cleaned) == cleaned


# --- Singkatan Indonesia ----------------------------------------------------
@pytest.mark.parametrize(
    "text,expected",
    [
        ("Gunakan alat bantu mis. obeng dan tang. Setelah itu uji coba.", 2),
        ("Periksa kabel, colokan, dll. Setelah itu laporkan.", 1),
        ("Ruang server ada di Lt. 2 gedung FITE. Hubungi teknisi.", 2),
        ("Sebutkan nomor ruang, no. tiket, dsb. Lalu kirim laporan.", 1),
    ],
)
def test_indonesian_abbreviations_do_not_split_sentences(text, expected):
    assert len(split_sentences(text)) == expected


def test_normal_sentence_boundary_is_detected():
    assert len(split_sentences("Matikan perangkat. Cabut kabel daya! Apakah sudah aman? Ya.")) == 4


# --- Metadata ---------------------------------------------------------------
def test_chunk_metadata_is_primitive_and_complete():
    chunks = _chunk(_synthetic_text())
    required = {"doc_id", "title", "doc_type", "category", "default_urgency", "sla_hours", "source_file", "chunk_index"}
    for i, c in enumerate(chunks):
        assert required <= set(c["metadata"])
        assert all(isinstance(v, (str, int, float, bool)) for v in c["metadata"].values())
        assert isinstance(c["metadata"]["sla_hours"], int)
        assert c["metadata"]["chunk_index"] == i
        assert c["id"] == f"SOP-99-c{i:03d}"


def test_prepend_title_toggle():
    with_title = _chunk(_synthetic_text(), prepend_title=True)
    without = _chunk(_synthetic_text(), prepend_title=False)
    assert all(c["text"].startswith("Judul: Dokumen Uji.") for c in with_title)
    assert not any(c["text"].startswith("Judul:") for c in without)


def test_front_matter_missing_field_rejected():
    raw = "---\ndoc_id: SOP-99\ntitle: Judul\n---\nIsi dokumen."
    with pytest.raises(CorpusFormatError):
        parse_front_matter(raw)


def test_front_matter_parsed_with_int_sla():
    raw = ("---\ndoc_id: SOP-99\ntitle: Judul\ndoc_type: sop\ncategory: uji\n"
           "default_urgency: tinggi\nsla_hours: 2\n---\nIsi dokumen.")
    meta, body = parse_front_matter(raw)
    assert meta["sla_hours"] == 2 and isinstance(meta["sla_hours"], int)
    assert body.strip() == "Isi dokumen."


# --- Korpus nyata -----------------------------------------------------------
def test_real_corpus_has_15_documents_with_contract_ids():
    chunks = load_and_chunk_corpus(CORPUS_DIR)
    ids = {c["metadata"]["doc_id"] for c in chunks}
    expected = {f"SOP-0{i}" for i in range(1, 9)} | {f"KB-{i:02d}" for i in range(9, 16)}
    assert ids == expected


def test_real_corpus_passes_self_check_with_default_parameters():
    chunks = load_and_chunk_corpus(CORPUS_DIR)
    report = self_check(chunks, 120, 20)
    assert report["empty_chunks"] == []
    assert report["bad_metadata"] == []
    assert report["oversize_chunks"] == []
    assert report["overlap_over_limit"] == []


def test_real_corpus_chunk_ids_are_unique():
    chunks = load_and_chunk_corpus(CORPUS_DIR)
    ids = [c["id"] for c in chunks]
    assert len(ids) == len(set(ids))
