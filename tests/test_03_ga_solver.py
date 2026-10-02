"""
Test Suite 03: Genetic Algorithm Solver (Milestone 2 Optimization)
------------------------------------------------------------------
Memvalidasi:
- Solusi GA pada 10 tiket resmi FITE (100% Valid & 0 SLA lateness)
- Kepatuhan elitisme (best cost monoton tidak meningkat antargenerasi)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from knowledge.data_loader import get_default_technicians, get_official_milestone2_tickets
from optimization.ga_solver import GeneticAlgorithmSolver


def test_ga_official_10_tickets():
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    solver = GeneticAlgorithmSolver(
        tickets=tickets,
        technicians=techs,
        population_size=50,
        generations=60,
        random_seed=42,
    )
    solution = solver.solve()

    assert solution.is_valid
    assert len(solution.assignments) == 10
    assert solution.total_lateness_minutes == 0.0


def test_ga_elitism_monotonicity():
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    solver = GeneticAlgorithmSolver(
        tickets=tickets,
        technicians=techs,
        population_size=30,
        generations=25,
        elite_count=3,
        random_seed=123,
    )
    solver.solve()

    history = solver.convergence_history
    for i in range(len(history) - 1):
        assert history[i + 1]["best_cost"] <= history[i]["best_cost"] + 1e-6
