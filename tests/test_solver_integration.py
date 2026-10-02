"""
QA Validation Suite - Solver Integration (tests/test_solver_integration.py).
Menjalankan: pytest tests/test_solver_integration.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fite_graph import GLOBAL_DISTANCE_MATRIX, shortest_path_dijkstra
from solver import run_csp_solver, run_ga_solver, solve_maintenance_schedule


def test_distance_matrix_and_dijkstra():
    """Menguji konsistensi matriks jarak dan Dijkstra pada topologi FITE."""
    path, cost = shortest_path_dijkstra("Posko Teknisi", "Labkom 725")
    assert cost > 0
    assert path[0] == "Posko Teknisi"
    assert path[-1] == "Labkom 725"

    matrix_cost = GLOBAL_DISTANCE_MATRIX.get_travel_time("Posko Teknisi", "Labkom 725")
    assert matrix_cost == cost
    assert GLOBAL_DISTANCE_MATRIX.get_travel_time("Kelas 711", "Kelas 711") == 0


def test_solve_maintenance_schedule_facade():
    """Menguji facade solve_maintenance_schedule untuk kedua algoritma."""
    sol_csp = solve_maintenance_schedule(algorithm="csp")
    assert sol_csp.is_valid
    assert len(sol_csp.assignments) == 10

    sol_ga = solve_maintenance_schedule(algorithm="ga", generations=30, population_size=30)
    assert sol_ga.is_valid
    assert len(sol_ga.assignments) == 10


def test_invalid_algorithm_name_raises():
    """Menguji bahwa algoritma tak dikenal melempar ValueError."""
    try:
        solve_maintenance_schedule(algorithm="unknown_algo")
        assert False, "Harus melempar ValueError untuk algoritma tidak dikenal"
    except ValueError:
        pass
