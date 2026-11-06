"""
Test Suite 10: Menu CLI "Cari SOP (Semantic Search)" (Milestone 3)
------------------------------------------------------------------
Memakai vector store tiruan (tanpa model/ChromaDB) agar cepat dan deterministik:
mengecek tampilan hasil relevan, pesan di luar cakupan, dan penanganan indeks
belum dibangun. Integrasi dengan indeks asli diuji manual (lihat README).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from interfaces import cli_app  # noqa: E402
from interfaces.cli_app import DelMaintOpsAppCLI  # noqa: E402


def _result(doc_id, title, sim, category="proyektor", sla=2, text="Langkah penanganan proyektor. " * 20):
    return SimpleNamespace(
        id=f"{doc_id}-c000", text=text, similarity=sim, distance=1 - sim,
        metadata={"doc_id": doc_id, "title": title, "category": category, "sla_hours": sla},
    )


class FakeStore:
    def __init__(self, results, rejected, top, threshold=0.35):
        self._resp = SimpleNamespace(query="q", results=results, top_similarity=top, threshold=threshold, rejected=rejected)
        self.queries = []

    def search(self, query, *a, **kw):
        self.queries.append(query)
        return self._resp

    def count(self):
        return len(self._resp.results)


def _run(monkeypatch, capsys, app, typed):
    answers = iter(typed)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    app.flow_semantic_search()
    return capsys.readouterr().out


def test_relevant_query_shows_title_docid_similarity_and_metadata(monkeypatch, capsys):
    app = DelMaintOpsAppCLI()
    app._vector_store = FakeStore([_result("SOP-01", "Penanganan Proyektor", 0.71), _result("KB-13", "Perangkat Cadangan", 0.55, "inventaris", 0)], False, 0.71)
    out = _run(monkeypatch, capsys, app, ["alat penyorot slide mati"])
    assert "[SOP-01] Penanganan Proyektor" in out
    assert "0.710" in out and "proyektor" in out and "2 jam" in out
    assert "tidak berlaku" in out  # sla_hours = 0
    assert "..." in out  # cuplikan dipotong
    assert app._vector_store.queries == ["alat penyorot slide mati"]


def test_rejected_query_shows_out_of_scope_message_without_results(monkeypatch, capsys):
    app = DelMaintOpsAppCLI()
    app._vector_store = FakeStore([_result("SOP-01", "Penanganan Proyektor", 0.12)], True, 0.12)
    out = _run(monkeypatch, capsys, app, ["resep rendang"])
    assert "di luar cakupan" in out
    assert "[SOP-01]" not in out


def test_empty_query_is_refused_without_searching(monkeypatch, capsys):
    app = DelMaintOpsAppCLI()
    store = FakeStore([], False, 0.0)
    app._vector_store = store
    out = _run(monkeypatch, capsys, app, ["   "])
    assert "tidak boleh kosong" in out and store.queries == []


def test_missing_index_shows_build_hint_and_does_not_crash(monkeypatch, capsys, tmp_path):
    app = DelMaintOpsAppCLI()
    monkeypatch.setattr("knowledge.retrieval_config.PERSIST_DIR", str(tmp_path / "tidak_ada"), raising=True)
    out = _run(monkeypatch, capsys, app, ["proyektor mati"])
    assert "scripts/build_index.py" in out


def test_menu_lists_semantic_search_and_exit_is_10():
    assert "Cari SOP (Semantic Search" in cli_app.MENU
    assert "10. Keluar" in cli_app.MENU


def test_main_loop_routes_9_then_10(monkeypatch, capsys):
    app = DelMaintOpsAppCLI()
    app._vector_store = FakeStore([_result("SOP-05", "Kelistrikan", 0.6, "listrik", 2)], False, 0.6)
    answers = iter(["9", "listrik padam di server", "10"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    app.run()
    out = capsys.readouterr().out
    assert "[SOP-05] Kelistrikan" in out and "Sampai jumpa" in out
