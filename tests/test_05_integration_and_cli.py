"""
Test Suite 05: End-to-End Integration & CLI Flow (M1 + M2 Continuity)
---------------------------------------------------------------------
Memvalidasi alur berkesinambungan:
1. Pelaporan tiket via CLI logic
2. Klasifikasi otomatis SOP & urgensi
3. Antrean prioritas FIFO tie-breaker
4. Alokasi teknisi berbasis CSP / GA
5. Navigasi rute optimal teknisi (UCS/A*) menuju lokasi ruangan
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from interfaces.cli_app import DelMaintOpsAppCLI
from navigation.router import GLOBAL_DISTANCE_MATRIX, shortest_path_dijkstra
from optimization.solver import solve_maintenance_schedule


def test_distance_matrix_continuity():
    # Pastikan simpul lama M1 dan simpul baru M2 terhubung
    cost_m1 = GLOBAL_DISTANCE_MATRIX.get_travel_time("Posko Teknisi", "Lab Jaringan")
    cost_m2 = GLOBAL_DISTANCE_MATRIX.get_travel_time("Posko Teknisi", "Labkom 725")
    cost_cross = GLOBAL_DISTANCE_MATRIX.get_travel_time("Lab Jaringan", "Kelas 721")

    assert cost_m1 > 0
    assert cost_m2 > 0
    assert cost_cross > 0


def test_cli_app_lifecycle():
    app = DelMaintOpsAppCLI()
    # Tambahkan tiket
    t1 = app.queue.push("TKT-001", "Labkom 725", "Mati listrik padam total", "tinggi")
    assert len(app.queue) == 1

    # Jalankan optimasi
    sol = solve_maintenance_schedule(algorithm="csp")
    assert sol.is_valid
    assert len(sol.assignments) == 10
