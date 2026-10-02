"""
QA Validation Suite - Genetic Algorithm Solver Module (tests/test_ga_solver.py).
Menjalankan: pytest tests/test_ga_solver.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from data_loader import get_default_technicians, get_official_milestone2_tickets
from ga_solver import GeneticAlgorithmSolver


def test_ga_solves_official_tickets():
    """Menguji bahwa GA Solver berhasil mengonvergen ke solusi valid pada 10 tiket resmi."""
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

    assert solution.is_valid, f"Solusi GA harus valid, violations: {solution.violations}"
    assert len(solution.assignments) == 10, "Semua 10 tiket harus dialokasikan."
    assert solution.total_lateness_minutes == 0, "Semua tiket harus selesai dalam batas SLA."


def test_ga_elitism_preserves_best_fitness():
    """Menguji bahwa elitisme menjamin kualitas solusi tidak memburuk antargenerasi."""
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    solver = GeneticAlgorithmSolver(
        tickets=tickets,
        technicians=techs,
        population_size=30,
        generations=20,
        elite_count=3,
        random_seed=123,
    )
    solver.solve()

    history = solver.convergence_history
    assert len(history) == 20
    # Cek bahwa best_cost monoton tidak naik (karena cost diminimalkan)
    for i in range(len(history) - 1):
        assert history[i + 1]["best_cost"] <= history[i]["best_cost"] + 1e-6
