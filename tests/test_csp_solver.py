"""
QA Validation Suite - CSP Solver Module (tests/test_csp_solver.py).
Menjalankan: pytest tests/test_csp_solver.py -v
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from csp_solver import AssignmentValue, CSPSchedulingProblem, CSPSolver
from data_loader import get_default_technicians, get_official_milestone2_tickets
from models import MaintenanceTicket, SkillCategory, Technician, UrgencyLevel


def test_csp_solves_official_milestone2_tickets():
    """Menguji bahwa CSP Solver berhasil menyelesaikan 10 tiket resmi tanpa pelanggaran."""
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    problem = CSPSchedulingProblem(tickets=tickets, technicians=techs)
    solver = CSPSolver(problem)
    solution = solver.solve()

    assert solution is not None, "CSP Solver harus mengembalikan solusi."
    assert solution.is_valid, f"Solusi CSP harus valid, pelanggaran: {solution.violations}"
    assert len(solution.assignments) == 10, "Seluruh 10 tiket harus dialokasikan."
    assert solution.total_lateness_minutes == 0, "Semua tiket harus selesai sebelum batas waktu SLA."


def test_csp_satisfies_hard_priority_constraint():
    """Menguji bahwa tiket berkategori Tinggi selalu selesai sebelum tiket Sedang/Rendah pada teknisi yang sama."""
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    problem = CSPSchedulingProblem(tickets=tickets, technicians=techs)
    solver = CSPSolver(problem)
    solution = solver.solve()
    assert solution is not None

    # Kelompokkan penugasan per teknisi
    tech_tasks = {}
    for a in solution.assignments:
        tech_tasks.setdefault(a.technician.tech_id, []).append(a)

    for tech_id, tasks in tech_tasks.items():
        for i in range(len(tasks) - 1):
            cur = tasks[i]
            nxt = tasks[i + 1]
            assert cur.ticket.urgency.priority_rank >= nxt.ticket.urgency.priority_rank, (
                f"Pelanggaran prioritas pada teknisi {tech_id}: "
                f"{cur.ticket.ticket_id} ({cur.ticket.urgency.value}) sebelum {nxt.ticket.ticket_id} ({nxt.ticket.urgency.value})"
            )


def test_csp_enforces_qualification_constraint():
    """Menguji bahwa teknisi yang ditugaskan selalu memiliki keahlian yang relevan."""
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    problem = CSPSchedulingProblem(tickets=tickets, technicians=techs)
    solver = CSPSolver(problem)
    solution = solver.solve()
    assert solution is not None

    for a in solution.assignments:
        assert a.ticket.is_compatible_technician(a.technician), (
            f"Teknisi {a.technician.name} tidak berkualifikasi menangani {a.ticket.facility}"
        )


def test_ac3_pruning_detects_empty_domain_on_unsupported_ticket():
    """Menguji bahwa AC-3 memangkas domain dan mengenali over-constrained jika keahlian tidak tersedia."""
    unsupported_ticket = [
        MaintenanceTicket(
            ticket_id="TEST-FAIL",
            location="Labkom 725",
            facility="Mati Listrik",
            issue_description="MCB jebol",
            request_time=datetime(2026, 10, 2, 8, 0),
            urgency=UrgencyLevel.TINGGI,
            required_skill=SkillCategory.ELECTRICAL,
        )
    ]
    # Hanya ada teknisi Jaringan
    net_only_tech = [
        Technician(
            tech_id="T-NET",
            name="Net Only",
            skills={SkillCategory.NETWORK},
        )
    ]

    problem = CSPSchedulingProblem(tickets=unsupported_ticket, technicians=net_only_tech)
    solver = CSPSolver(problem)
    sol = solver.solve()

    assert sol is not None
    assert not sol.is_valid, "Solusi harus ditandai invalid saat domain kosong / overconstrained"
