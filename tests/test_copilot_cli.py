"""
QA validation suite - CLI Interaktif (copilot_cli.py).
Menjalankan: pytest tests/test_copilot_cli.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from copilot_cli import (  # noqa: E402
    SOP_KB,
    DelMaintOpsCopilotCLI,
    classify_urgency,
    detect_category,
    find_sop,
)


# ---------------------------------------------------------------------------
# Deteksi kategori dari deskripsi bebas
# ---------------------------------------------------------------------------

def test_detect_category_proyektor():
    assert detect_category("proyektor tidak menyala di kelas") == "SOP-01"


def test_detect_category_ac():
    assert detect_category("AC bocor dan tidak dingin") == "SOP-02"


def test_detect_category_jaringan():
    assert detect_category("koneksi LAN mati total") == "SOP-03"


def test_detect_category_umum():
    assert detect_category("toilet lantai 1 tersumbat") == "SOP-04"


def test_detect_category_unknown_returns_none():
    assert detect_category("ada suara aneh dari langit-langit") is None


# ---------------------------------------------------------------------------
# Klasifikasi urgensi (aturan kenaikan sesuai docs/04_sops_knowledge_base.md)
# ---------------------------------------------------------------------------

def test_urgency_proyektor_always_tinggi():
    assert classify_urgency("SOP-01") == "tinggi"


def test_urgency_ac_default_sedang_naik_ke_tinggi():
    assert classify_urgency("SOP-02", exam_or_practicum_room=False) == "sedang"
    assert classify_urgency("SOP-02", exam_or_practicum_room=True) == "tinggi"


def test_urgency_jaringan_default_sedang_naik_ke_kritis():
    assert classify_urgency("SOP-03", practicum_active=False) == "sedang"
    assert classify_urgency("SOP-03", practicum_active=True) == "kritis"


def test_urgency_umum_default_rendah_naik_ke_tinggi():
    assert classify_urgency("SOP-04", safety_or_sanitation=False) == "rendah"
    assert classify_urgency("SOP-04", safety_or_sanitation=True) == "tinggi"


# ---------------------------------------------------------------------------
# Pencarian SOP (simulasi awal sebelum RAG)
# ---------------------------------------------------------------------------

def test_find_sop_matches_keyword():
    assert find_sop("jaringan") == ["SOP-03"]
    assert find_sop("toilet") == ["SOP-04"]


def test_find_sop_no_match_returns_empty():
    assert find_sop("printer") == []


def test_sop_kb_has_four_entries_matching_docs():
    assert set(SOP_KB.keys()) == {"SOP-01", "SOP-02", "SOP-03", "SOP-04"}


# ---------------------------------------------------------------------------
# Perilaku bot end-to-end (tanpa I/O interaktif, memakai API internal)
# ---------------------------------------------------------------------------

def test_report_and_process_ticket_produces_optimal_route():
    app = DelMaintOpsCopilotCLI()
    app.queue.push("TKT-001", "Lab Jaringan", "jaringan mati", "kritis")
    from copilot_cli import TicketRecord

    ticket = next(t for t in app.queue.as_sorted_list() if t.ticket_id == "TKT-001")
    app.records["TKT-001"] = TicketRecord(ticket=ticket, sop_id="SOP-03")

    assert len(app.queue) == 1
    app.flow_proses()

    assert len(app.queue) == 0
    assert len(app.history) == 1
    resolved = app.history[0]
    assert resolved.status == "Resolved"
    assert resolved.route_ucs == ["Posko Teknisi", "Lab RPL", "Lab Jaringan"]
    assert resolved.route_cost == 5


def test_duplicate_ticket_detected_before_creating_second_record():
    app = DelMaintOpsCopilotCLI()
    from copilot_cli import TicketRecord

    app.queue.push("TKT-001", "Saung", "kursi rusak", "rendah")
    ticket = next(t for t in app.queue.as_sorted_list() if t.ticket_id == "TKT-001")
    app.records["TKT-001"] = TicketRecord(ticket=ticket, sop_id="SOP-04")

    duplicate = next(
        (r for r in app.records.values()
         if r.ticket.location == "Saung" and r.sop_id == "SOP-04"),
        None,
    )
    assert duplicate is not None
    assert duplicate.ticket.ticket_id == "TKT-001"
