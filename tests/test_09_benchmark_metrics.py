"""
Test Suite 09: Metrik Benchmark (fungsi murni, tanpa model embedding)
---------------------------------------------------------------------
Memvalidasi perhitungan Hit@k, MRR, presisi/recall penolakan OOD, rekomendasi
threshold, dan baseline kata kunci pada data sintetis dengan jawaban yang
bisa dihitung tangan.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location("benchmark_retrieval", ROOT / "scripts" / "benchmark_retrieval.py")
bm = importlib.util.module_from_spec(_spec)
sys.modules["benchmark_retrieval"] = bm
_spec.loader.exec_module(bm)


def _rec(qid, qtype, expected, ranked, top=None):
    docs = [{"doc_id": d, "title": "", "chunk_id": f"{d}-c000", "similarity": s} for d, s in ranked]
    return {"id": qid, "query": qid, "type": qtype, "expected_doc_ids": expected, "notes": "",
            "top_similarity": top if top is not None else (ranked[0][1] if ranked else 0.0), "ranked_docs": docs}


RECORDS = [
    _rec("R1", "synonym", ["A"], [("A", 0.80), ("B", 0.50), ("C", 0.40)]),   # rank 1
    _rec("R2", "synonym", ["B"], [("A", 0.60), ("B", 0.55), ("C", 0.30)]),   # rank 2
    _rec("R3", "ambiguous", ["C"], [("A", 0.50), ("B", 0.45), ("D", 0.44), ("C", 0.40)]),  # rank 4 -> miss@3
    _rec("O1", "ood_far", [], [("A", 0.10)]),
    _rec("O2", "ood_near", [], [("A", 0.45)]),
]


def test_relevant_metrics_hand_computed():
    m = bm.relevant_metrics(RECORDS, k=3)
    assert m["n"] == 3
    assert m["hit_at_1"] == 1 / 3
    assert m["hit_at_3"] == 2 / 3
    assert abs(m["mrr"] - (1 + 1 / 2 + 1 / 4) / 3) < 1e-9
    assert abs(m["mean_top1_cosine"] - (0.80 + 0.60 + 0.50) / 3) < 1e-9
    assert abs(m["mean_target_cosine"] - (0.80 + 0.55 + 0.40) / 3) < 1e-9


def test_ood_metrics_at_threshold_040():
    o = bm.ood_metrics(RECORDS, 0.40)
    # ditolak (<0.40): hanya O1 -> TP=1; O2 lolos -> FN=1; relevan semua >=0.50 -> FP=0
    assert (o["tp"], o["fp"], o["fn"], o["tn"]) == (1, 0, 1, 3)
    assert o["precision"] == 1.0 and o["recall"] == 0.5 and o["false_rejection_rate"] == 0.0
    assert o["recall_far"] == 1.0 and o["recall_near"] == 0.0


def test_ood_metrics_high_threshold_rejects_relevant_queries():
    o = bm.ood_metrics(RECORDS, 0.70)
    assert o["fp"] == 2 and o["tp"] == 2
    assert o["precision"] == 0.5 and o["recall"] == 1.0


def test_precision_is_none_when_nothing_rejected():
    assert bm.ood_metrics(RECORDS, 0.0)["precision"] is None


def test_recommend_threshold_separable_gives_gap_midpoint():
    rec = bm.recommend_threshold(RECORDS)
    assert rec["separable"] is True
    assert abs(rec["threshold"] - (0.45 + 0.50) / 2) < 1e-3


def test_recommend_threshold_overlap_case():
    recs = RECORDS + [_rec("O3", "ood_near", [], [("A", 0.62)])]  # OOD lebih tinggi dari relevan terendah
    rec = bm.recommend_threshold(recs)
    assert rec["separable"] is False
    assert rec["threshold"] is not None


def test_collapse_to_documents_keeps_best_chunk_per_doc():
    class R:  # tiruan SearchResult
        def __init__(self, i, d, s):
            self.id, self.similarity, self.metadata = i, s, {"doc_id": d, "title": d}

    ranked = bm.collapse_to_documents([R("A-c0", "A", 0.9), R("A-c1", "A", 0.8), R("B-c0", "B", 0.7)])
    assert [d["doc_id"] for d in ranked] == ["A", "B"]
    assert ranked[0]["chunk_id"] == "A-c0"


def test_quartiles_and_histogram():
    q = bm.quartiles([0.1, 0.2, 0.3, 0.4, 0.5])
    assert q["min"] == 0.1 and q["median"] == 0.3 and q["max"] == 0.5
    lines = bm.histogram_lines(RECORDS)
    assert any("R" in ln for ln in lines) and any("O" in ln for ln in lines)


def test_keyword_baseline_counts_only_keyword_matches():
    recs = [
        _rec("S1", "synonym", ["SOP-01"], [("SOP-01", 0.7)]),
        {**_rec("S2", "synonym", ["SOP-01"], [("SOP-01", 0.7)]), "query": "proyektor mati"},
        {**_rec("O9", "ood_far", [], [("SOP-01", 0.1)]), "query": "resep rendang"},
    ]
    b = bm.keyword_baseline(recs)
    assert b["by_type"]["synonym"]["keyword_hits"] == 1
    assert b["by_type"]["synonym"]["semantic_hit_at_1"] == 2
    assert b["keyword_ood_false_accept"] == 0


def test_dataset_file_is_valid_and_synonyms_avoid_keywords():
    from knowledge.sops import detect_category

    queries = bm.load_queries(ROOT / "data" / "benchmark_queries.json")
    for q in queries:
        if q["type"] == "synonym":
            assert detect_category(q["query"]) is None, f"{q['id']} memakai kata kunci SOP"
