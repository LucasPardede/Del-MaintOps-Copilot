"""
Del-MaintOps Copilot - Sensitivity Analysis & Edge Case Benchmarking Module
--------------------------------------------------------------------------
Milestone 2 (W04): Eksperimen Empiris, Analisis Sensitivitas, dan Pengujian Kasus Ekstrem.

Mengukur performa solver (CSP dan GA) terhadap:
1. Variasi Skala Masalah:
   - Skala Kecil (5 Tiket)
   - Skala Sedang (10 Tiket Resmi Dummy)
   - Skala Besar (25 Tiket)
   - Skala Sangat Besar (50 Tiket)
2. Analisis Konvergensi:
   - CSP: Runtime (ms) dan node/backtrack ratio.
   - GA: Kurva penurunan penalti / peningkatan fitness tiap generasi.
3. Kasus Ekstrem (Edge Cases):
   - Over-Constrained (Ketiadaan teknisi berkompeten).
   - Emergency Surge (Lonjakan tiket tingkat Tinggi secara simultan).
   - Single Technician (Beban kerja ekstrem pada 1 teknisi).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from data_loader import (
    generate_synthetic_tickets,
    get_default_technicians,
    get_edge_case_scenarios,
    get_official_milestone2_tickets,
)
from ga_solver import GeneticAlgorithmSolver
from models import MaintenanceTicket, Technician
from solver import run_csp_solver, run_ga_solver


def run_scaling_benchmark() -> List[Dict[str, Any]]:
    """Menjalankan pengujian sensitivitas terhadap variasi ukuran masalah."""
    techs = get_default_technicians()

    # Tambahkan teknisi ekstra untuk skala besar (50 tiket) agar rasio kapasitas realistis
    extended_techs = techs + [
        Technician(
            tech_id="TECH-04",
            name="Hotman (All-Rounder)",
            skills=set(techs[0].skills | techs[1].skills | techs[2].skills),
            base_location="Posko Teknisi",
        )
    ]

    scenarios = [
        ("Skala Kecil (5 Tiket)", get_official_milestone2_tickets()[:5], techs),
        ("Skala Sedang (10 Tiket Dummy)", get_official_milestone2_tickets(), techs),
        ("Skala Besar (25 Tiket)", generate_synthetic_tickets(25, seed=101), extended_techs),
        ("Skala Sangat Besar (50 Tiket)", generate_synthetic_tickets(50, seed=202), extended_techs),
    ]

    results = []

    for name, tickets, tech_pool in scenarios:
        # Benchmark CSP
        t0 = time.perf_counter()
        csp_sol = run_csp_solver(tickets, tech_pool)
        csp_time_ms = (time.perf_counter() - t0) * 1000

        # Benchmark GA
        t0 = time.perf_counter()
        ga_sol = run_ga_solver(tickets, tech_pool, generations=80, population_size=50)
        ga_time_ms = (time.perf_counter() - t0) * 1000

        results.append({
            "scenario": name,
            "ticket_count": len(tickets),
            "tech_count": len(tech_pool),
            # Metrik CSP
            "csp_time_ms": csp_time_ms,
            "csp_valid": csp_sol.is_valid,
            "csp_penalty": csp_sol.total_penalty,
            "csp_travel": csp_sol.total_travel_time_minutes,
            "csp_lateness": csp_sol.total_lateness_minutes,
            "csp_backtracks": csp_sol.explored_states_or_generations,
            # Metrik GA
            "ga_time_ms": ga_time_ms,
            "ga_valid": ga_sol.is_valid,
            "ga_penalty": ga_sol.total_penalty,
            "ga_travel": ga_sol.total_travel_time_minutes,
            "ga_lateness": ga_sol.total_lateness_minutes,
            "ga_generations": ga_sol.explored_states_or_generations,
        })

    return results


def run_ga_convergence_experiment() -> List[Dict[str, float]]:
    """Merekam evolusi konvergensi kebugaran GA generasi per generasi pada 10 tiket resmi."""
    tickets = get_official_milestone2_tickets()
    techs = get_default_technicians()

    solver = GeneticAlgorithmSolver(
        tickets=tickets,
        technicians=techs,
        population_size=60,
        generations=60,
        random_seed=42,
    )
    solver.solve()
    return solver.convergence_history


def run_edge_case_benchmark() -> List[Dict[str, Any]]:
    """Menjalankan pengujian ketahanan terhadap skenario kasus ekstrem."""
    edge_scenarios = get_edge_case_scenarios()
    results = []

    for name, (tickets, techs) in edge_scenarios.items():
        # Uji CSP
        csp_sol = run_csp_solver(tickets, techs)
        # Uji GA
        ga_sol = run_ga_solver(tickets, techs, generations=50, population_size=40)

        results.append({
            "edge_case_name": name,
            "ticket_count": len(tickets),
            "tech_count": len(techs),
            "csp_is_valid": csp_sol.is_valid,
            "csp_violations": csp_sol.violations,
            "csp_time_ms": csp_sol.computation_time_ms,
            "ga_is_valid": ga_sol.is_valid,
            "ga_violations": ga_sol.violations,
            "ga_time_ms": ga_sol.computation_time_ms,
        })

    return results


def print_sensitivity_report() -> None:
    """Menampilkan laporan visual teks hasil pengujian sensitivitas dan kasus ekstrem."""
    print("=" * 110)
    print("LAPORAN PENGUJIAN SENSITIVITAS & ANALISIS KONVERGENSI (MILESTONE 2)")
    print("Del-MaintOps Copilot - FITE IT Del")
    print("=" * 110)

    # 1. Tabel Skalabilitas
    print("\n1. PENGUJIAN SKALABILITAS (Ukuran Masalah Kecil vs Besar)")
    print("-" * 110)
    print(
        f"{'Skenario Masalah':<30} | {'CSP Waktu (ms)':<15} | {'CSP Status':<12} | "
        f"{'GA Waktu (ms)':<15} | {'GA Status':<12} | {'CSP Penalti':<12} | {'GA Penalti':<12}"
    )
    print("-" * 110)

    scale_results = run_scaling_benchmark()
    for r in scale_results:
        csp_stat = "VALID" if r["csp_valid"] else "PELANGGARAN"
        ga_stat = "VALID" if r["ga_valid"] else "PELANGGARAN"
        print(
            f"{r['scenario']:<30} | {r['csp_time_ms']:>12.2f} ms | {csp_stat:<12} | "
            f"{r['ga_time_ms']:>12.2f} ms | {ga_stat:<12} | {r['csp_penalty']:>12.1f} | {r['ga_penalty']:>12.1f}"
        )
    print("-" * 110)

    # 2. Tabel Analisis Konvergensi GA
    print("\n2. ANALISIS KONVERGENSI GENETIKA (Generasi 1 s/d 60 pada 10 Tiket Resmi)")
    print("-" * 80)
    print(f"{'Generasi':<12} | {'Best Fitness':<16} | {'Best Cost/Penalti':<18} | {'Pelanggaran':<12}")
    print("-" * 80)

    history = run_ga_convergence_experiment()
    sample_gens = [1, 5, 10, 20, 30, 40, 50, 60]
    for h in history:
        if h["generation"] in sample_gens:
            print(
                f"{h['generation']:<12} | {h['best_fitness']:>14.2f} | "
                f"{h['best_cost']:>16.2f} | {int(h['violations_count']):<12}"
            )
    print("-" * 80)

    # 3. Tabel Kasus Ekstrem
    print("\n3. PENGUJIAN KASUS EKSTREM (EDGE CASES)")
    print("-" * 110)
    print(f"{'Nama Kasus Ekstrem':<32} | {'Tiket':<6} | {'Teknisi':<8} | {'Respon CSP':<25} | {'Respon GA':<25}")
    print("-" * 110)

    edge_results = run_edge_case_benchmark()
    for e in edge_results:
        csp_resp = "Solusi Ditemukan" if e["csp_is_valid"] else f"Menolak (Overconstrained)"
        ga_resp = "Valid (Teroptimasi)" if e["ga_is_valid"] else f"Pelanggaran Terdeteksi"
        print(
            f"{e['edge_case_name']:<32} | {e['ticket_count']:<6} | {e['tech_count']:<8} | "
            f"{csp_resp:<25} | {ga_resp:<25}"
        )
    print("-" * 110)


if __name__ == "__main__":
    print_sensitivity_report()
