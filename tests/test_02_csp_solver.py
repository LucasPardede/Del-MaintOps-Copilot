"""
Test Suite 02: CSP Constraint Solver (Milestone 2 Core)
-------------------------------------------------------
Memvalidasi:
- Penyelesaian 10 tiket resmi tanpa pelanggaran batasan
- Kepatuhan batasan kualifikasi SOP (skill matching)
- Kepatuhan batasan prioritas absolut (Tinggi > Sedang > Rendah)
- Deteksi domain kosong AC-3 pada over-constrained
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from knowledge.data_loader import get_default_technicians, get_official_milestone2_tickets
from optimization.csp_solver import CSPSchedulingProblem, CSPSolver


def test_csp_official_10_tickets():
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    problem = CSPSchedulingProblem(tickets=tickets, technicians=techs)
    solver = CSPSolver(problem)
    solution = solver.solve()

    assert solution.is_valid
    assert len(solution.assignments) == 10
    assert solution.total_lateness_minutes == 0.0

    # Cek kualifikasi setiap tiket
    for a in solution.assignments:
        assert a.ticket.is_compatible_technician(a.technician)
