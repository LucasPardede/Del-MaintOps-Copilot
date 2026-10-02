"""
Del-MaintOps Copilot - Unified Constraint Optimization Engine (solver.py)
-------------------------------------------------------------------------
Facade utama modul optimasi alokasi & penjadwalan multi-teknisi FITE IT Del:
- solve_maintenance_schedule (Fungsi orkestrator terpadu)
- run_csp_solver (AC-3 + Backtracking MRV/Degree/LCV/MAC)
- run_ga_solver (Algoritma Genetika dengan Elitisme & Turnamen)
"""

from __future__ import annotations

from typing import List, Optional

from core.models import MaintenanceTicket, ScheduleSolution, Technician
from knowledge.data_loader import (
    get_default_technicians,
    get_official_milestone2_tickets,
)
from optimization.csp_solver import CSPSchedulingProblem, CSPSolver
from optimization.ga_solver import GeneticAlgorithmSolver


def solve_maintenance_schedule(
    tickets: Optional[List[MaintenanceTicket]] = None,
    technicians: Optional[List[Technician]] = None,
    algorithm: str = "csp",
    **kwargs,
) -> ScheduleSolution:
    """Memecahkan masalah keputusan alokasi dan urutan pengerjaan tiket fasilitas.

    Args:
        tickets: Daftar tiket kerusakan (default: 10 tiket resmi Milestone 2).
        technicians: Daftar teknisi yang bertugas (default: 3 teknisi standar FITE).
        algorithm: 'csp' (default, exact constraint satisfaction) atau 'ga' (genetic algorithm).
        kwargs: Parameter tambahan untuk solver (population_size, generations, seed).

    Returns:
        ScheduleSolution yang memuat timeline penugasan, durasi pengerjaan,
        waktu tempuh, dan status validitas batasan (hard & soft).
    """
    if tickets is None:
        tickets = get_official_milestone2_tickets()
    if technicians is None:
        technicians = get_default_technicians()

    algo = algorithm.lower().strip()
    if algo == "csp":
        problem = CSPSchedulingProblem(tickets=tickets, technicians=technicians)
        solver = CSPSolver(problem=problem)
        return solver.solve()
    elif algo in ("ga", "genetic", "genetic_algorithm"):
        pop_size = kwargs.get("population_size", 60)
        gens = kwargs.get("generations", 100)
        solver = GeneticAlgorithmSolver(
            tickets=tickets,
            technicians=technicians,
            population_size=pop_size,
            generations=gens,
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
