"""
Del-MaintOps Copilot - Unified Constraint Solver Module (solver.py)
-------------------------------------------------------------------
Milestone 2 (W04): Main Entry Point untuk Mesin Inferensi Batasan Bisnis.

Menyediakan fungsi terpadu untuk memecahkan masalah keputusan alokasi teknisi
dan penjadwalan pemeliharaan fasilitas FITE IT Del:
- solve_maintenance_schedule (Facade utama)
- run_csp_solver (AC-3 + Backtracking MRV/Degree/LCV)
- run_ga_solver (Algoritma Genetika dengan Turnamen & Elitisme)
- Visualisasi tabel jadwal dan verifikasi pemenuhan batasan (hard & soft)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Tambahkan src ke sys.path jika dijalankan langsung
sys.path.insert(0, str(Path(__file__).resolve().parent))

from csp_solver import CSPSchedulingProblem, CSPSolver
from data_loader import (
    get_default_technicians,
    get_edge_case_scenarios,
    get_official_milestone2_tickets,
)
from fite_graph import GLOBAL_DISTANCE_MATRIX
from ga_solver import GeneticAlgorithmSolver
from models import MaintenanceTicket, ScheduleSolution, Technician


def solve_maintenance_schedule(
    tickets: Optional[List[MaintenanceTicket]] = None,
    technicians: Optional[List[Technician]] = None,
    algorithm: str = "csp",
    **kwargs,
) -> ScheduleSolution:
    """Fungsi utama untuk memecahkan masalah penjadwalan tiket fasilitas.

    Args:
        tickets: Daftar tiket kerusakan (default: 10 tiket resmi Milestone 2).
        technicians: Daftar teknisi FITE yang bertugas (default: 3 teknisi standar FITE).
        algorithm: 'csp' (default, exact constraint satisfaction) atau
                   'ga' (metaheuristic genetic optimization).
        kwargs: Parameter tambahan untuk solver (misal: population_size, generations).

    Returns:
        ScheduleSolution yang berisi daftar alokasi, timeline pengerjaan,
        waktu tempuh, status validitas batasan, dan penalti keterlambatan SLA.
    """
    if tickets is None:
        tickets = get_official_milestone2_tickets()
    if technicians is None:
        technicians = get_default_technicians()

    algo = algorithm.lower().strip()
    if algo == "csp":
        problem = CSPSchedulingProblem(tickets=tickets, technicians=technicians)
        solver = CSPSolver(problem=problem)
        solution = solver.solve()
        if solution is None:
            raise RuntimeError("CSP Solver gagal menghasilkan solusi valid.")
        return solution
    elif algo in ("ga", "genetic", "genetic_algorithm"):
        pop_size = kwargs.get("population_size", 60)
        generations = kwargs.get("generations", 100)
        solver = GeneticAlgorithmSolver(
            tickets=tickets,
            technicians=technicians,
            population_size=pop_size,
            generations=generations,
            random_seed=kwargs.get("random_seed", 42),
        )
        return solver.solve()
    else:
        raise ValueError(f"Algoritma tidak dikenal: {algorithm!r}. Gunakan 'csp' atau 'ga'.")


def run_csp_solver(
    tickets: Optional[List[MaintenanceTicket]] = None,
    technicians: Optional[List[Technician]] = None,
) -> ScheduleSolution:
    """Helper langsung untuk mengeksekusi CSP Solver."""
    return solve_maintenance_schedule(tickets, technicians, algorithm="csp")


def run_ga_solver(
    tickets: Optional[List[MaintenanceTicket]] = None,
    technicians: Optional[List[Technician]] = None,
    generations: int = 100,
    population_size: int = 60,
) -> ScheduleSolution:
    """Helper langsung untuk mengeksekusi GA Solver."""
    return solve_maintenance_schedule(
        tickets,
        technicians,
        algorithm="ga",
        generations=generations,
        population_size=population_size,
    )


def main() -> None:
    """Demo eksekusi solver pada 10 tiket resmi Milestone 2."""
    print("=" * 105)
    print("DEL-MAINTOPS COPILOT | MILESTONE 2: CONSTRAINT SOLVER DEMO")
    print("Fakultas Informatika dan Teknik Elektro (FITE) - Institut Teknologi Del")
    print("=" * 105)

    tickets = get_official_milestone2_tickets()
    technicians = get_default_technicians()

    print(f"\n[INFO] Memuat {len(tickets)} tiket kerusakan dummy resmi:")
    for t in tickets:
        print(f"  - {t.ticket_id} | {t.urgency.value:<7} | {t.facility:<12} | {t.location:<12} | {t.issue_description}")

    print(f"\n[INFO] Tim Teknisi FITE yang bertugas:")
    for tech in technicians:
        skills_str = ", ".join(s.value for s in tech.skills)
        print(f"  - {tech.tech_id}: {tech.name} (Keahlian: {skills_str})")

    # 1. Jalankan CSP Solver
    print("\n" + "=" * 50 + " 1. SOLUSI CSP (AC-3 + BACKTRACKING MRV/LCV) " + "=" * 50)
    csp_sol = run_csp_solver(tickets, technicians)
    print(csp_sol.summary_table())

    # 2. Jalankan GA Solver
    print("\n" + "=" * 50 + " 2. SOLUSI GA (GENETIC ALGORITHM WITH ELITISM) " + "=" * 50)
    ga_sol = run_ga_solver(tickets, technicians, generations=100, population_size=60)
    print(ga_sol.summary_table())

    # 3. Perbandingan Komparatif Singkat
    print("\n" + "=" * 35 + " PERBANDINGAN KOMPARATIF ALGORITMA " + "=" * 35)
    print(f"{'Metrik':<30} | {'CSP Solver':<25} | {'GA Solver':<25}")
    print("-" * 85)
    print(f"{'Validitas Batasan (Legalitas)':<30} | {'100% VALID' if csp_sol.is_valid else 'TIDAK VALID':<25} | {'100% VALID' if ga_sol.is_valid else 'TIDAK VALID':<25}")
    print(f"{'Waktu Komputasi':<30} | {f'{csp_sol.computation_time_ms:.2f} ms':<25} | {f'{ga_sol.computation_time_ms:.2f} ms':<25}")
    print(f"{'Total Travel Time (Jarak FITE)':<30} | {f'{csp_sol.total_travel_time_minutes:.1f} menit':<25} | {f'{ga_sol.total_travel_time_minutes:.1f} menit':<25}")
    print(f"{'Total SLA Lateness':<30} | {f'{csp_sol.total_lateness_minutes:.1f} menit':<25} | {f'{ga_sol.total_lateness_minutes:.1f} menit':<25}")
    print(f"{'Total Penalti Bisnis':<30} | {f'{csp_sol.total_penalty:.2f}':<25} | {f'{ga_sol.total_penalty:.2f}':<25}")
    print(f"{'Total Makespan Selesai':<30} | {f'{csp_sol.total_makespan_minutes:.1f} menit':<25} | {f'{ga_sol.total_makespan_minutes:.1f} menit':<25}")
    print("=" * 85)


if __name__ == "__main__":
    main()
