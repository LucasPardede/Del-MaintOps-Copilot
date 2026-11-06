"""
Del-MaintOps Copilot - Chunker Korpus (Word-Aware Recursive Chunking)
---------------------------------------------------------------------
Modul prapemrosesan dan pemotongan (chunking) korpus dokumen SOP/kebijakan
FITE IT Del untuk pipeline pencarian semantik Milestone 3.

Alur:
    file Markdown + front matter  ->  parse front matter (manual, tanpa PyYAML)
    -> cleaning (Unicode NFC, normalisasi whitespace, pembuangan penanda
       markdown)  ->  blok (heading / paragraf / item daftar)
    -> kalimat (aman terhadap singkatan Indonesia)  ->  kata (hanya jika satu
       kalimat melebihi ukuran chunk)  ->  packing berukuran ``chunk_size_words``
       dengan overlap ``overlap_words``.

Prinsip pemotongan (urutan rekursif, dari satuan terbesar ke terkecil):
    1. Blok (heading + isi, paragraf, item daftar) tidak dipecah selama muat
       dalam satu chunk.
    2. Blok yang terlalu besar dipecah per kalimat.
    3. Kalimat yang masih terlalu besar baru dipecah per kata.
Dengan demikian pemotongan tidak pernah terjadi di tengah kata dan hanya
terjadi di tengah kalimat bila kalimat tunggal melebihi ukuran chunk.

Ukuran chunk dihitung dalam kata (pemisah whitespace) dan mencakup teks
overlap yang dibawa dari chunk sebelumnya. Prefiks ``"Judul: <title>. "``
(``prepend_title=True``) tidak dihitung dalam ukuran tersebut.

Pemilik: Ika Maria Manurung (12S24021)
"""

from __future__ import annotations

import argparse
import math
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from knowledge.retrieval_config import (
        DEFAULT_CHUNK_SIZE_WORDS,
        DEFAULT_OVERLAP_WORDS,
    )
except ModuleNotFoundError:  # dijalankan langsung: python src/knowledge/chunker.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from knowledge.retrieval_config import (  # type: ignore[no-redef]
        DEFAULT_CHUNK_SIZE_WORDS,
        DEFAULT_OVERLAP_WORDS,
    )

# Root repo: dua level di atas file ini (src/knowledge/chunker.py)
_REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Konstanta skema korpus
# ---------------------------------------------------------------------------
REQUIRED_FIELDS: Tuple[str, ...] = (
    "doc_id",
    "title",
    "doc_type",
    "category",
    "default_urgency",
    "sla_hours",
)
VALID_DOC_TYPES = {"sop", "kebijakan", "panduan"}
VALID_URGENCIES = {"tinggi", "sedang", "rendah", "kritis", "-"}
_PRIMITIVE_TYPES = (str, int, float, bool)

# Singkatan Indonesia yang diakhiri titik namun BUKAN akhir kalimat.
ABBREVIATIONS = frozenset(
    {
        "mis.", "dsb.", "dll.", "dst.", "dkk.", "lt.", "no.", "sdh.",
        "yg.", "dg.", "tsb.", "jl.", "bpk.", "ds.", "dr.", "ir.", "hlm.",
        "tgl.", "sbb.", "spt.", "dgn.", "kec.", "kab.", "prof.", "st.",
    }
)

_ZERO_WIDTH = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_MOJIBAKE_RE = re.compile("\ufffd|Ã[\u0080-\u00bf]|â€")


class CorpusFormatError(ValueError):
    """Kesalahan format dokumen korpus (front matter rusak, teks tidak bersih)."""


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Membersihkan teks: Unicode NFC, newline seragam, whitespace rapi.

    - Normalisasi Unicode ke bentuk NFC.
    - ``\\r\\n``/``\\r`` menjadi ``\\n``; tab dan spasi tak-pecah (NBSP)
      menjadi spasi biasa; karakter lebar-nol dibuang.
    - Spasi berlebih dalam baris dipadatkan dan spasi di ujung baris dibuang.
    - Tiga baris kosong atau lebih dipadatkan menjadi satu baris kosong.

    Fungsi ini idempoten: ``clean_text(clean_text(x)) == clean_text(x)``.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\t", " ")
    text = _ZERO_WIDTH.sub("", text)
    lines = [re.sub(r" {2,}", " ", ln).rstrip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip("\n").strip()


def _count_words(text: str) -> int:
    """Menghitung jumlah kata (pemisah whitespace)."""
    return len(text.split())


# ---------------------------------------------------------------------------
# Front matter
# ---------------------------------------------------------------------------
def parse_front_matter(raw: str, source: str = "<teks>") -> Tuple[Dict[str, Any], str]:
    """Mem-parse front matter sederhana ``key: value`` (tanpa PyYAML).

    Args:
        raw: Isi file lengkap (front matter + badan).
        source: Nama file untuk pesan error.

    Returns:
        Tuple ``(metadata, badan_dokumen)``. ``sla_hours`` sudah berupa ``int``.

    Raises:
        CorpusFormatError: Jika front matter hilang/rusak, kolom wajib kurang,
            nilai tidak valid, atau ``sla_hours`` bukan bilangan bulat >= 0.
    """
    raw = raw.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = raw.split("\n")
    if not lines or lines[0].strip() != "---":
        raise CorpusFormatError(f"{source}: front matter tidak ditemukan (baris pertama harus '---').")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise CorpusFormatError(f"{source}: front matter tidak ditutup dengan '---'.") from None

    meta: Dict[str, Any] = {}
    for offset, line in enumerate(lines[1:end], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            raise CorpusFormatError(f"{source}: baris {offset} bukan pasangan 'kunci: nilai': {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = re.split(r"\s+#", value, maxsplit=1)[0].strip()  # buang komentar inline
        if not key:
            raise CorpusFormatError(f"{source}: baris {offset} memiliki kunci kosong.")
        meta[key] = value

    missing = [f for f in REQUIRED_FIELDS if not meta.get(f, "").strip()]
    if missing:
        raise CorpusFormatError(f"{source}: kolom wajib hilang/kosong: {', '.join(missing)}.")
    if meta["doc_type"] not in VALID_DOC_TYPES:
        raise CorpusFormatError(
            f"{source}: doc_type {meta['doc_type']!r} tidak valid; harus salah satu dari {sorted(VALID_DOC_TYPES)}."
        )
    if meta["default_urgency"] not in VALID_URGENCIES:
        raise CorpusFormatError(
            f"{source}: default_urgency {meta['default_urgency']!r} tidak valid; "
            f"harus salah satu dari {sorted(VALID_URGENCIES)}."
        )
    try:
        meta["sla_hours"] = int(meta["sla_hours"])
    except ValueError:
        raise CorpusFormatError(f"{source}: sla_hours harus bilangan bulat, ditemukan {meta['sla_hours']!r}.") from None
    if meta["sla_hours"] < 0:
        raise CorpusFormatError(f"{source}: sla_hours tidak boleh negatif.")

    body = "\n".join(lines[end + 1 :])
    return meta, body


# ---------------------------------------------------------------------------
# Segmentasi: blok -> kalimat -> kata
# ---------------------------------------------------------------------------
def parse_blocks(text: str) -> List[str]:
    """Memecah teks bersih menjadi blok: heading, paragraf, dan item daftar.

    Penanda markdown (``##``, ``-``, ``1.``) dibuang. Teks heading dijadikan
    prefiks ``"<Heading>: "`` pada blok isi berikutnya agar chunk yang diawali
    bagian tersebut tetap berkonteks, dan heading tidak pernah berdiri sendiri
    di ujung chunk.
    """
    blocks: List[str] = []
    pending_heading: Optional[str] = None
    para: List[str] = []
    item: Optional[List[str]] = None

    def emit(content: str) -> None:
        nonlocal pending_heading
        content = " ".join(content.split())
        if not content:
            return
        if pending_heading:
            content = f"{pending_heading}: {content}"
            pending_heading = None
        blocks.append(content)

    def flush() -> None:
        nonlocal para, item
        if para:
            emit(" ".join(para))
            para = []
        if item is not None:
            emit(" ".join(item))
            item = None

    for line in text.split("\n"):
        if not line.strip():
            flush()
            continue
        m_head = _HEADING_RE.match(line)
        if m_head:
            flush()
            heading = m_head.group(1).strip().rstrip(":.")
            if pending_heading and heading:
                pending_heading = f"{pending_heading} - {heading}"
            elif heading:
                pending_heading = heading
            continue
        m_item = _LIST_RE.match(line)
        if m_item:
            flush()
            item = [m_item.group(1).strip()]
            continue
        if item is not None and line.startswith((" ", "\t")):
            item.append(line.strip())  # lanjutan item daftar
        else:
            if item is not None:
                flush()
            para.append(line.strip())
    flush()
    if pending_heading:  # heading tanpa isi di akhir dokumen
        blocks.append(pending_heading)
    return blocks


def split_sentences(text: str) -> List[str]:
    """Memisah teks menjadi kalimat, aman terhadap singkatan Indonesia.

    Batas kalimat adalah ``.``, ``!``, atau ``?`` yang diikuti spasi dan huruf
    besar/angka/kurung/kutip, KECUALI bila token sebelum titik adalah singkatan
    (mis. ``mis.``, ``dsb.``, ``dll.``, ``Lt.``, ``No.``, ``dst.``, ``sdh.``)
    atau satu huruf tunggal (inisial). Titik yang diikuti huruf kecil tidak
    dianggap batas kalimat.
    """
    text = " ".join(text.split())
    if not text:
        return []
    sentences: List[str] = []
    start = 0
    for m in re.finditer(r"([.!?])\s+(?=[\"'(\[A-Z0-9])", text):
        end = m.end(1)
        before = text[start:end]
        last_token = before.split()[-1] if before.split() else ""
        if m.group(1) == ".":
            token = last_token.lstrip("(\"'[").lower()
            if token in ABBREVIATIONS:
                continue
            if re.fullmatch(r"[a-z]\.", token):  # inisial tunggal, mis. "A."
                continue
        sentences.append(before.strip())
        start = m.end()
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def _split_by_words(sentence: str, size: int) -> List[str]:
    """Memecah satu kalimat panjang per kata menjadi potongan berukuran seimbang."""
    words = sentence.split()
    n_parts = math.ceil(len(words) / size)
    per_part = math.ceil(len(words) / n_parts)
    return [" ".join(words[i : i + per_part]) for i in range(0, len(words), per_part)]


def _blocks_to_atoms(blocks: List[str], size: int) -> List[List[str]]:
    """Mengubah blok menjadi atom (daftar kalimat yang tidak dipisah saat packing).

    Blok yang muat dalam ``size`` kata menjadi satu atom utuh. Blok yang lebih
    besar dipecah per kalimat; kalimat yang masih lebih besar dipecah per kata.
    """
    atoms: List[List[str]] = []
    for block in blocks:
        sentences = split_sentences(block)
        if _count_words(block) <= size:
            atoms.append(sentences)
            continue
        for sent in sentences:
            if _count_words(sent) <= size:
                atoms.append([sent])
            else:
                atoms.extend([piece] for piece in _split_by_words(sent, size))
    return atoms


# ---------------------------------------------------------------------------
# Overlap & packing
# ---------------------------------------------------------------------------
def _overlap_tail(sentences: List[str], overlap_words: int) -> List[str]:
    """Mengambil ekor chunk sebelumnya (maksimal ``overlap_words`` kata).

    Dibulatkan ke batas kalimat: kalimat utuh dari belakang diambil selama
    totalnya tidak melebihi ``overlap_words``. Jika kalimat terakhir sendiri
    lebih panjang, diambil ekor ``overlap_words`` kata (batas kata), dimajukan
    ke batas klausa (setelah koma/titik koma) bila ada.
    """
    if overlap_words <= 0 or not sentences:
        return []
    tail: List[str] = []
    total = 0
    for sent in reversed(sentences):
        n = _count_words(sent)
        if total + n > overlap_words:
            break
        tail.insert(0, sent)
        total += n
    if tail:
        return tail
    words = sentences[-1].split()[-overlap_words:]
    for i in range(1, len(words) - 3):
        if words[i - 1].endswith((",", ";")):
            words = words[i:]
            break
    return [" ".join(words)]


def _shrink_overlap(overlap: List[str], room: int) -> List[str]:
    """Memangkas overlap dari depan hingga totalnya <= ``room`` kata."""
    overlap = list(overlap)
    while overlap and sum(_count_words(s) for s in overlap) > room:
        if len(overlap) > 1:
            overlap.pop(0)
        else:
            frag = overlap[0].split()[1:]
            overlap = [" ".join(frag)] if frag else []
    return overlap


def _validate_params(chunk_size_words: int, overlap_words: int) -> None:
    if not isinstance(chunk_size_words, int) or isinstance(chunk_size_words, bool) or chunk_size_words <= 0:
        raise ValueError(f"chunk_size_words harus bilangan bulat > 0, diterima {chunk_size_words!r}.")
    if not isinstance(overlap_words, int) or isinstance(overlap_words, bool) or overlap_words < 0:
        raise ValueError(f"overlap_words harus bilangan bulat >= 0, diterima {overlap_words!r}.")
    if overlap_words >= chunk_size_words:
        raise ValueError(
            f"overlap_words ({overlap_words}) harus lebih kecil daripada chunk_size_words ({chunk_size_words})."
        )


def _title_prefix(title: str) -> str:
    return f"Judul: {title.strip().rstrip('.')}. "


def chunk_document(
    text: str,
    source_file: str,
    base_metadata: Dict[str, Any],
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
    prepend_title: bool = True,
) -> List[Dict[str, Any]]:
    """Memotong satu dokumen menjadi chunk (word-aware, recursive, ber-overlap).

    Args:
        text: Badan dokumen (tanpa front matter); dibersihkan oleh fungsi ini.
        source_file: Nama file sumber (disimpan di metadata ``source_file``).
        base_metadata: Metadata dasar dokumen; wajib memuat ``doc_id`` (dan
            ``title`` bila ``prepend_title``). Semua nilai harus bertipe
            ``str``/``int``/``float``/``bool`` (batasan ChromaDB).
        chunk_size_words: Ukuran maksimum chunk dalam kata (termasuk overlap,
            tidak termasuk prefiks judul).
        overlap_words: Jumlah maksimum kata ekor chunk sebelumnya yang dibawa.
        prepend_title: Awali tiap chunk dengan ``"Judul: <title>. "``.

    Returns:
        Daftar chunk ``{"id", "text", "metadata"}``; id ``<doc_id>-c<NNN>``.
        Hasil deterministik: input sama menghasilkan output sama.

    Raises:
        ValueError: Parameter tidak valid atau metadata tidak lengkap.
        TypeError: Nilai metadata bukan tipe primitif.
    """
    _validate_params(chunk_size_words, overlap_words)
    if "doc_id" not in base_metadata or not str(base_metadata["doc_id"]).strip():
        raise ValueError("base_metadata wajib memuat 'doc_id'.")
    if prepend_title and not str(base_metadata.get("title", "")).strip():
        raise ValueError("base_metadata wajib memuat 'title' bila prepend_title=True.")
    for key, value in base_metadata.items():
        if not isinstance(value, _PRIMITIVE_TYPES):
            raise TypeError(
                f"Metadata {key!r} bertipe {type(value).__name__}; ChromaDB hanya menerima str/int/float/bool."
            )

    blocks = parse_blocks(clean_text(text))
    atoms = _blocks_to_atoms(blocks, chunk_size_words)
    if not atoms:
        return []

    chunk_sentences: List[List[str]] = []
    overlap: List[str] = []
    current: List[str] = []  # kalimat baru (di luar overlap) pada chunk berjalan
    current_words = 0

    def flush() -> None:
        nonlocal overlap, current, current_words
        emitted = overlap + current
        chunk_sentences.append(emitted)
        overlap = _overlap_tail(emitted, overlap_words)
        current, current_words = [], 0

    for atom in atoms:
        atom_words = sum(_count_words(s) for s in atom)
        overlap_w = sum(_count_words(s) for s in overlap)
        if current and overlap_w + current_words + atom_words > chunk_size_words:
            flush()
        overlap = _shrink_overlap(overlap, chunk_size_words - atom_words - current_words)
        current.extend(atom)
        current_words += atom_words
    if current:
        flush()

    doc_id = str(base_metadata["doc_id"])
    prefix = _title_prefix(str(base_metadata["title"])) if prepend_title else ""
    chunks: List[Dict[str, Any]] = []
    for idx, sentences in enumerate(chunk_sentences):
        metadata = dict(base_metadata)
        metadata["source_file"] = str(source_file)
        metadata["chunk_index"] = idx
        chunks.append(
            {
                "id": f"{doc_id}-c{idx:03d}",
                "text": prefix + " ".join(sentences),
                "metadata": metadata,
            }
        )
    return chunks


# ---------------------------------------------------------------------------
# Pemuatan korpus
# ---------------------------------------------------------------------------
def _resolve_corpus_dir(corpus_dir: Union[str, Path]) -> Path:
    path = Path(corpus_dir)
    if path.is_absolute() or path.exists():
        return path
    return _REPO_ROOT / path


def load_and_chunk_corpus(
    corpus_dir: Union[str, Path] = "data/corpus",
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
    prepend_title: bool = True,
) -> List[Dict[str, Any]]:
    """Memuat seluruh dokumen ``*.md`` di ``corpus_dir`` lalu memotongnya.

    ``README.md`` dilewati. Dokumen diproses berurutan menurut nama file agar
    hasil deterministik. Path relatif yang tidak ada di direktori kerja dicari
    relatif terhadap root repo.

    Raises:
        FileNotFoundError: Direktori korpus tidak ada atau tidak berisi dokumen.
        CorpusFormatError: Front matter rusak, teks mengandung mojibake,
            ``doc_id`` ganda/tidak cocok dengan nama file, atau dokumen kosong.
    """
    _validate_params(chunk_size_words, overlap_words)
    directory = _resolve_corpus_dir(corpus_dir)
    if not directory.is_dir():
        raise FileNotFoundError(f"Direktori korpus tidak ditemukan: {directory}")
    files = sorted(p for p in directory.glob("*.md") if p.name.lower() != "readme.md")
    if not files:
        raise FileNotFoundError(f"Tidak ada dokumen .md pada {directory}")

    all_chunks: List[Dict[str, Any]] = []
    seen_ids: Dict[str, str] = {}
    for path in files:
        raw = path.read_text(encoding="utf-8")
        if _MOJIBAKE_RE.search(raw):
            raise CorpusFormatError(f"{path.name}: terdeteksi karakter rusak (mojibake); simpan ulang sebagai UTF-8.")
        meta, body = parse_front_matter(raw, source=path.name)
        doc_id = meta["doc_id"]
        if not path.name.startswith(f"{doc_id}_"):
            raise CorpusFormatError(f"{path.name}: nama file harus diawali '{doc_id}_' sesuai doc_id.")
        if doc_id in seen_ids:
            raise CorpusFormatError(f"{path.name}: doc_id {doc_id!r} ganda dengan {seen_ids[doc_id]}.")
        seen_ids[doc_id] = path.name
        chunks = chunk_document(
            body,
            source_file=path.name,
            base_metadata=meta,
            chunk_size_words=chunk_size_words,
            overlap_words=overlap_words,
            prepend_title=prepend_title,
        )
        if not chunks:
            raise CorpusFormatError(f"{path.name}: badan dokumen kosong, tidak menghasilkan chunk.")
        all_chunks.extend(chunks)
    return all_chunks


# ---------------------------------------------------------------------------
# Statistik & cek mandiri
# ---------------------------------------------------------------------------
def _body_words(chunk: Dict[str, Any]) -> List[str]:
    """Kata isi chunk tanpa prefiks judul."""
    text = chunk["text"]
    prefix = _title_prefix(chunk["metadata"]["title"])
    if text.startswith(prefix):
        text = text[len(prefix) :]
    return text.split()


def _measured_overlap(prev: List[str], nxt: List[str], limit: int) -> int:
    """Panjang k terbesar (<= limit) sehingga k kata akhir prev == k kata awal nxt."""
    for k in range(min(limit, len(prev), len(nxt)), 0, -1):
        if prev[-k:] == nxt[:k]:
            return k
    return 0


def self_check(chunks: List[Dict[str, Any]], chunk_size_words: int, overlap_words: int) -> Dict[str, Any]:
    """Cek mandiri kualitas chunk; mengembalikan ringkasan pelanggaran/statistik."""
    empty = [c["id"] for c in chunks if not _body_words(c)]
    bad_meta = [
        c["id"]
        for c in chunks
        if any(not isinstance(v, _PRIMITIVE_TYPES) for v in c["metadata"].values())
        or not isinstance(c["metadata"].get("sla_hours"), int)
        or not isinstance(c["metadata"].get("chunk_index"), int)
    ]
    oversize = [c["id"] for c in chunks if len(_body_words(c)) > chunk_size_words]
    not_sentence_end = [c["id"] for c in chunks if not _body_words(c)[-1].endswith((".", "!", "?"))]
    by_doc: Dict[str, List[Dict[str, Any]]] = {}
    for c in chunks:
        by_doc.setdefault(c["metadata"]["doc_id"], []).append(c)
    overlaps: List[int] = []
    overlap_violations: List[str] = []
    for doc_chunks in by_doc.values():
        for a, b in zip(doc_chunks, doc_chunks[1:]):
            k = _measured_overlap(_body_words(a), _body_words(b), chunk_size_words)
            overlaps.append(k)
            if k > overlap_words:
                overlap_violations.append(b["id"])
    return {
        "empty_chunks": empty,
        "bad_metadata": bad_meta,
        "oversize_chunks": oversize,
        "chunks_not_ending_at_sentence_boundary": not_sentence_end,
        "overlap_over_limit": overlap_violations,
        "pairs_with_zero_overlap": sum(1 for k in overlaps if k == 0),
        "n_pairs": len(overlaps),
        "avg_overlap_words": (sum(overlaps) / len(overlaps)) if overlaps else 0.0,
    }


def corpus_statistics(chunks: List[Dict[str, Any]]) -> Dict[str, float]:
    """Statistik jumlah kata isi per chunk (tanpa prefiks judul)."""
    sizes = [len(_body_words(c)) for c in chunks]
    return {
        "n_docs": len({c["metadata"]["doc_id"] for c in chunks}),
        "n_chunks": len(chunks),
        "min_words": min(sizes),
        "avg_words": sum(sizes) / len(sizes),
        "max_words": max(sizes),
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="Statistik chunking korpus FITE.")
    parser.add_argument("--corpus-dir", default="data/corpus")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE_WORDS)
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP_WORDS)
    parser.add_argument("--no-title", action="store_true", help="Nonaktifkan prepend_title.")
    args = parser.parse_args()

    chunks = load_and_chunk_corpus(
        args.corpus_dir, args.chunk_size, args.overlap, prepend_title=not args.no_title
    )
    stats = corpus_statistics(chunks)
    print(
        f"Parameter: chunk_size={args.chunk_size} kata, overlap={args.overlap} kata, "
        f"prepend_title={not args.no_title}"
    )
    print(f"Dokumen : {stats['n_docs']}")
    print(f"Chunk   : {stats['n_chunks']}")
    print(
        f"Kata/chunk (isi, tanpa prefiks judul): min={stats['min_words']} "
        f"rata-rata={stats['avg_words']:.1f} maks={stats['max_words']}"
    )
    per_doc: Dict[str, int] = {}
    for c in chunks:
        per_doc[c["metadata"]["doc_id"]] = per_doc.get(c["metadata"]["doc_id"], 0) + 1
    print("Chunk per dokumen:", ", ".join(f"{k}={v}" for k, v in per_doc.items()))
    check = self_check(chunks, args.chunk_size, args.overlap)
    print("Cek mandiri:")
    for key in (
        "empty_chunks",
        "bad_metadata",
        "oversize_chunks",
        "overlap_over_limit",
        "chunks_not_ending_at_sentence_boundary",
    ):
        print(f"  {key}: {check[key] if check[key] else 'tidak ada'}")
    print(
        f"  overlap terukur: rata-rata {check['avg_overlap_words']:.1f} kata; "
        f"{check['pairs_with_zero_overlap']} dari {check['n_pairs']} pasangan chunk tanpa overlap"
    )


if __name__ == "__main__":
    _main()
