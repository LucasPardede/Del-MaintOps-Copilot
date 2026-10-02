"""
Del-MaintOps Copilot - Unified Constraint Solver Module (solver.py)
-------------------------------------------------------------------
Modul entry point utama untuk mesin inferensi batasan bisnis (Milestone 2).
Mendelegasikan ke modul implementasi di src/optimization dan src/knowledge.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.models import MaintenanceTicket, ScheduleSolution, Technician
from knowledge.data_loader import (
    get_default_technicians,
    get_edge_case_scenarios,
    get_official_milestone2_tickets,
)
from optimization.csp_solver import CSPSchedulingProblem, CSPSolver
from optimization.ga_solver import GeneticAlgorithmSolver
from optimization.solver import (
    run_csp_solver,
    run_ga_solver,
    solve_maintenance_schedule,
)


def main() -> None:
    print("=" * 105)
    print("DEL-MAINTOPS COPILOT | MILESTONE 2: CONSTRAINT SOLVER DEMO")
    print("Fakultas Informatika dan Teknik Elektro (FITE) - Institut Teknologi Del")
    print("=" * 105)

    tickets = get_official_milestone2_tickets()
    technicians = get_default_technicians()

    print(f"\n[INFO] Memuat {len(tickets)} tiket kerusakan dummy resmi:")
    for t in tickets:
        print(f"  - {t.ticket_id} | {t.urgency.value.capitalize():<7} | {t.facility:<12} | {t.location:<12} | {t.issue_description}")

    print("\n" + "=" * 50 + " 1. SOLUSI CSP (AC-3 + BACKTRACKING MRV/LCV) " + "=" * 50)
    csp_sol = run_csp_solver(tickets, technicians)
    print(csp_sol.summary_table())

    print("\n" + "=" * 50 + " 2. SOLUSI GA (GENETIC ALGORITHM WITH ELITISM) " + "=" * 50)
    ga_sol = run_ga_solver(tickets, technicians, generations=100, population_size=60)
    print(ga_sol.summary_table())


if __name__ == "__main__":
    main()
