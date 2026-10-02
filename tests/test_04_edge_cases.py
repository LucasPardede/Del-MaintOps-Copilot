"""
Test Suite 04: Edge Cases & Stress Scenarios
--------------------------------------------
Memvalidasi:
- Over-constrained: ketiadaan kualifikasi teknisi ditolak secara elegan
- Emergency Surge: pembagian beban tiket darurat serentak
- Single Technician: penjadwalan sekuensial hierarki prioritas
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from knowledge.data_loader import get_edge_case_scenarios
from optimization.solver import run_csp_solver, run_ga_solver


def test_edge_case_unqualified_rejection():
    scenarios = get_edge_case_scenarios()
    tickets, techs = scenarios["over_constrained_no_skill"]

    csp_sol = run_csp_solver(tickets, techs)
    assert not csp_sol.is_valid, "CSP harus menolak ketiadaan kualifikasi teknisi"

    ga_sol = run_ga_solver(tickets, techs, generations=20, population_size=30)
    assert not ga_sol.is_valid, "GA harus menandai pelanggaran kualifikasi teknisi"


def test_edge_case_emergency_surge():
    scenarios = get_edge_case_scenarios()
    tickets, techs = scenarios["emergency_surge"]

    csp_sol = run_csp_solver(tickets, techs)
    assert csp_sol.is_valid
    assert len(csp_sol.assignments) == len(tickets)


def test_edge_case_single_technician():
    scenarios = get_edge_case_scenarios()
    tickets, techs = scenarios["single_technician"]

    csp_sol = run_csp_solver(tickets, techs)
    assert csp_sol.is_valid
    assert len(csp_sol.assignments) == 10
