"""
QA Validation Suite - Edge Cases & Stress Scenarios (tests/test_edge_cases.py).
Menjalankan: pytest tests/test_edge_cases.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_loader import get_edge_case_scenarios
from solver import run_csp_solver, run_ga_solver


def test_edge_case_over_constrained_unqualified_technician():
    """Menguji respons sistem ketika tidak ada teknisi yang memiliki kualifikasi yang cocok."""
    edge_scenarios = get_edge_case_scenarios()
    tickets, techs = edge_scenarios["over_constrained_no_skill"]

    # CSP Solver harus secara elegan mendeteksi inkonsistensi
    csp_sol = run_csp_solver(tickets, techs)
    assert not csp_sol.is_valid, "CSP Solver harus menolak skenario over-constrained kualifikasi"

    # GA Solver harus mendeteksi pelanggaran batasan fatal
    ga_sol = run_ga_solver(tickets, techs, generations=20, population_size=30)
    assert not ga_sol.is_valid, "GA Solver harus menandai pelanggaran kualifikasi teknisi"
    assert len(ga_sol.violations) > 0


def test_edge_case_emergency_surge():
    """Menguji respons sistem saat terjadi lonjakan serentak tiket darurat tingkat Tinggi."""
    edge_scenarios = get_edge_case_scenarios()
    tickets, techs = edge_scenarios["emergency_surge"]

    csp_sol = run_csp_solver(tickets, techs)
    assert csp_sol is not None
    assert len(csp_sol.assignments) == len(tickets)
    # Semua tiket yang masuk harus dijadwalkan secara teratur
    for a in csp_sol.assignments:
        assert a.ticket.is_compatible_technician(a.technician)


def test_edge_case_single_technician_heavy_load():
    """Menguji skenario ketika hanya 1 teknisi serba bisa yang harus menangani 10 tiket."""
    edge_scenarios = get_edge_case_scenarios()
    tickets, techs = edge_scenarios["single_technician"]

    csp_sol = run_csp_solver(tickets, techs)
    assert csp_sol is not None
    assert len(csp_sol.assignments) == 10

    # Pastikan urutan prioritas absolut terjaga ketat pada teknisi tunggal
    for i in range(len(csp_sol.assignments) - 1):
        cur = csp_sol.assignments[i]
        nxt = csp_sol.assignments[i + 1]
        assert cur.ticket.urgency.priority_rank >= nxt.ticket.urgency.priority_rank
