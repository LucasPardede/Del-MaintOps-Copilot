"""
Del-MaintOps Copilot - Constraint Satisfaction Problem (CSP) Solver
-------------------------------------------------------------------
Milestone 2 (W04): Modul Pemecahan Batasan Keputusan Bisnis Formal.

Implementasi Algoritmik:
1. Pemodelan Matematis Variabel, Domain, dan Batasan (Hard & Soft Constraints).
2. AC-3 (Arc Consistency 3) Constraint Propagation untuk pemangkasan domain.
3. Backtracking Search dengan:
   - MRV (Minimum Remaining Values) Variable Ordering.
   - Degree Heuristic untuk pemecah kebuntuan (tie-breaker).
   - LCV (Least Constraining Value) Value Ordering.
   - MAC (Maintaining Arc Consistency / Forward Checking).
4. Penanganan Biaya Soft Constraints (SLA Lateness, FIFO, dan Waktu Tempuh Graf FITE).
"""

from __future__ import annotations

import copy
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from fite_graph import GLOBAL_DISTANCE_MATRIX
from models import (
    MaintenanceTicket,
    ScheduleSolution,
    SkillCategory,
    TaskAssignment,
    Technician,
    UrgencyLevel,
)


@dataclass(frozen=True)
class AssignmentValue:
    """Nilai dalam domain variabel keputusan: (teknisi, urutan tugas pada teknisi tersebut)."""
    technician_id: str
    order_position: int  # Posisi urutan pengerjaan pada antrean teknisi (0, 1, 2, ...)


class CSPSchedulingProblem:
    """Formalisasi representasi CSP untuk Penjadwalan Pemeliharaan Fasilitas FITE."""

    def __init__(
        self,
        tickets: List[MaintenanceTicket],
        technicians: List[Technician],
        distance_matrix=GLOBAL_DISTANCE_MATRIX,
    ) -> None:
        self.tickets = tickets
        self.technicians = {t.tech_id: t for t in technicians}
        self.distance_matrix = distance_matrix

        # Variabel X: Setiap tiket adalah variabel keputusan yang harus diberi nilai AssignmentValue
        self.variables: List[str] = [t.ticket_id for t in tickets]
        self.ticket_by_id: Dict[str, MaintenanceTicket] = {t.ticket_id: t for t in tickets}

        # Domain D(X_i): Himpunan nilai yang mungkin untuk setiap variabel
        self.domains: Dict[str, List[AssignmentValue]] = {}
        self._initialize_domains()

        # Tetangga batasan (Neighbors dalam Constraint Graph)
        self.neighbors: Dict[str, Set[str]] = {var: set() for var in self.variables}
        self._build_constraint_graph()

    def _initialize_domains(self) -> None:
        """Inisialisasi domain awal berdasarkan filter kualifikasi (Unary Constraints)."""
        max_slots = len(self.tickets)

        for ticket in self.tickets:
            valid_values: List[AssignmentValue] = []
            for tech_id, tech in self.technicians.items():
                # Unary Constraint: Kualifikasi teknisi
                if ticket.is_compatible_technician(tech):
                    for slot in range(max_slots):
                        valid_values.append(AssignmentValue(technician_id=tech_id, order_position=slot))
            self.domains[ticket.ticket_id] = valid_values

    def _build_constraint_graph(self) -> None:
        """Membangun graf batasan: setiap pasang tiket memiliki batasan biner (binary constraints)."""
        for i, var_i in enumerate(self.variables):
            for j, var_j in enumerate(self.variables):
                if i != j:
                    self.neighbors[var_i].add(var_j)

    def is_consistent_binary(
        self,
        var1: str,
        val1: AssignmentValue,
        var2: str,
        val2: AssignmentValue,
    ) -> bool:
        """Memeriksa apakah penugasan (var1=val1) dan (var2=val2) konsisten secara batasan biner."""
        # Jika kedua tiket ditugaskan ke teknisi berbeda, tidak ada konflik alokasi teknisi
        if val1.technician_id != val2.technician_id:
            return True

        # Jika teknisi sama:
        # 1. Hard Constraint: Tidak boleh ada 2 tiket dengan nomor urutan yang sama (No-Collision)
        if val1.order_position == val2.order_position:
            return False

        t1 = self.ticket_by_id[var1]
        t2 = self.ticket_by_id[var2]

        # 2. Hard Constraint: Hierarki Prioritas Absolut (Tinggi > Sedang > Rendah)
        # Jika t1 lebih prioritas dari t2, maka order t1 HARUS sebelum order t2
        if t1.urgency.priority_rank > t2.urgency.priority_rank:
            if val1.order_position >= val2.order_position:
                return False
        elif t1.urgency.priority_rank < t2.urgency.priority_rank:
            if val1.order_position <= val2.order_position:
                return False

        # 3. Soft Constraint as Pruning: Urutan FIFO kronologis untuk tiket dengan tingkat urgensi sama
        # Tiket yang masuk lebih awal harus berada di urutan lebih awal bila pada teknisi yang sama
        if t1.urgency == t2.urgency:
            if t1.request_time < t2.request_time and val1.order_position > val2.order_position:
                return False
            if t1.request_time > t2.request_time and val1.order_position < val2.order_position:
                return False

        return True


class CSPSolver:
    """Solver CSP berbasis AC-3 dan Backtracking dengan Heuristik MRV, Degree, dan LCV."""

    def __init__(self, problem: CSPSchedulingProblem) -> None:
        self.problem = problem
        self.backtrack_count: int = 0
        self.ac3_pruned_count: int = 0
        self.start_time: float = 0.0

    def ac3(self, domains: Optional[Dict[str, List[AssignmentValue]]] = None) -> bool:
        """Algoritma AC-3 (Arc Consistency #3) untuk memangkas inkonsistensi domain."""
        if domains is None:
            domains = self.problem.domains

        # Inisialisasi antrean busur dengan semua busur biner (Xi, Xj)
        queue: deque[Tuple[str, str]] = deque()
        for xi in self.problem.variables:
            for xj in self.problem.neighbors[xi]:
                queue.append((xi, xj))

        while queue:
            xi, xj = queue.popleft()
            if self._revise(domains, xi, xj):
                if len(domains[xi]) == 0:
                    return False  # Inkonsistensi terdeteksi (domain kosong)
                for xk in self.problem.neighbors[xi]:
                    if xk != xj:
                        queue.append((xk, xi))

        return True

    def _revise(
        self,
        domains: Dict[str, List[AssignmentValue]],
        xi: str,
        xj: str,
    ) -> bool:
        """Memeriksa dan merevisi domain Xi terhadap Xj."""
        revised = False
        surviving_values: List[AssignmentValue] = []

        for x in domains[xi]:
            # Cari setidaknya satu nilai y di domain Xj yang konsisten dengan x
            has_support = any(
                self.problem.is_consistent_binary(xi, x, xj, y)
                for y in domains[xj]
            )
            if has_support:
                surviving_values.append(x)
            else:
                revised = True
                self.ac3_pruned_count += 1

        if revised:
            domains[xi] = surviving_values
        return revised

    def select_unassigned_variable(
        self,
        assignment: Dict[str, AssignmentValue],
        domains: Dict[str, List[AssignmentValue]],
    ) -> str:
        """MRV (Minimum Remaining Values) dengan Degree Heuristic sebagai tie-breaker."""
        unassigned = [v for v in self.problem.variables if v not in assignment]

        # Cari nilai minimum ukuran domain (MRV)
        min_domain_size = min(len(domains[v]) for v in unassigned)
        candidates = [v for v in unassigned if len(domains[v]) == min_domain_size]

        if len(candidates) == 1:
            return candidates[0]

        # Degree Heuristic: Pilih kandidat yang memiliki batasan terbanyak ke unassigned variables
        def degree(var: str) -> int:
            return sum(1 for neighbor in self.problem.neighbors[var] if neighbor not in assignment)

        return max(candidates, key=degree)

    def order_domain_values(
        self,
        var: str,
        assignment: Dict[str, AssignmentValue],
        domains: Dict[str, List[AssignmentValue]],
    ) -> List[AssignmentValue]:
        """LCV (Least Constraining Value): Mengurutkan nilai yang memangkas nilai tetangga paling sedikit."""
        if len(domains[var]) <= 1:
            return domains[var]

        def count_conflicts(val: AssignmentValue) -> int:
            conflicts = 0
            for neighbor in self.problem.neighbors[var]:
                if neighbor not in assignment:
                    for neighbor_val in domains[neighbor]:
                        if not self.problem.is_consistent_binary(var, val, neighbor, neighbor_val):
                            conflicts += 1
            return conflicts

        # Nilai dengan konflik tersedikit diuji terlebih dahulu
        return sorted(domains[var], key=count_conflicts)

    def solve(self) -> Optional[ScheduleSolution]:
        """Menjalankan proses pemecahan CSP lengkap (Pre-AC3 + Backtracking MAC)."""
        self.backtrack_count = 0
        self.ac3_pruned_count = 0
        self.start_time = time.perf_counter()

        # Salin domain untuk menjaga isolasi
        working_domains = copy.deepcopy(self.problem.domains)

        # 1. Jalankan AC-3 di awal
        if not self.ac3(working_domains):
            elapsed_ms = (time.perf_counter() - self.start_time) * 1000
            return ScheduleSolution(
                assignments=[],
                is_valid=False,
                total_makespan_minutes=0,
                total_travel_time_minutes=0,
                total_lateness_minutes=0,
                total_penalty=float("inf"),
                violations=["Domain awal inkonsisten (AC-3 gagal memangkas - overconstrained)"],
                algorithm_name="CSP (AC-3 + Backtracking MRV/LCV)",
                computation_time_ms=elapsed_ms,
                explored_states_or_generations=self.backtrack_count,
            )

        # 2. Backtracking Search dengan MAC (Maintaining Arc Consistency)
        raw_assignment: Dict[str, AssignmentValue] = {}
        result = self._backtrack(raw_assignment, working_domains)

        elapsed_ms = (time.perf_counter() - self.start_time) * 1000

        if result is None:
            return ScheduleSolution(
                assignments=[],
                is_valid=False,
                total_makespan_minutes=0,
                total_travel_time_minutes=0,
                total_lateness_minutes=0,
                total_penalty=float("inf"),
                violations=["Tidak ditemukan penugasan yang memenuhi seluruh batasan bisnis"],
                algorithm_name="CSP (AC-3 + Backtracking MRV/LCV)",
                computation_time_ms=elapsed_ms,
                explored_states_or_generations=self.backtrack_count,
            )

        # 3. Konversi hasil penugasan diskret ke jadwal operasional nyata dengan timeline
        return self._build_schedule_solution(result, elapsed_ms)

    def _backtrack(
        self,
        assignment: Dict[str, AssignmentValue],
        domains: Dict[str, List[AssignmentValue]],
    ) -> Optional[Dict[str, AssignmentValue]]:
        """Fungsi rekursif backtracking dengan forward checking / arc consistency."""
        if len(assignment) == len(self.problem.variables):
            return assignment

        self.backtrack_count += 1
        var = self.select_unassigned_variable(assignment, domains)

        for val in self.order_domain_values(var, assignment, domains):
            # Cek konsistensi lokal dengan penugasan yang sudah ada
            consistent = True
            for assigned_var, assigned_val in assignment.items():
                if not self.problem.is_consistent_binary(var, val, assigned_var, assigned_val):
                    consistent = False
                    break

            if consistent:
                assignment[var] = val
                saved_domains = copy.deepcopy(domains)

                # Forward Checking / MAC: Batasi domain tetangga
                domains[var] = [val]
                inference_ok = self._forward_check(var, val, assignment, domains)

                if inference_ok:
                    result = self._backtrack(assignment, domains)
                    if result is not None:
                        return result

                # Backtrack: batalkan penugasan & kembalikan domain
                del assignment[var]
                domains = saved_domains

        return None

    def _forward_check(
        self,
        var: str,
        val: AssignmentValue,
        assignment: Dict[str, AssignmentValue],
        domains: Dict[str, List[AssignmentValue]],
    ) -> bool:
        """Forward checking sederhana untuk memangkas nilai domain tetangga."""
        for neighbor in self.problem.neighbors[var]:
            if neighbor not in assignment:
                surviving = [
                    n_val for n_val in domains[neighbor]
                    if self.problem.is_consistent_binary(var, val, neighbor, n_val)
                ]
                domains[neighbor] = surviving
                if len(surviving) == 0:
                    return False
        return True

    def _build_schedule_solution(
        self,
        assignment: Dict[str, AssignmentValue],
        computation_time_ms: float,
    ) -> ScheduleSolution:
        """Mengonversi penugasan urutan menjadi timeline jadwal detail dengan waktu tempuh dan SLA."""
        # Kelompokkan tiket per teknisi dan urutkan berdasarkan order_position
        tech_queues: Dict[str, List[MaintenanceTicket]] = {t_id: [] for t_id in self.problem.technicians}
        for ticket_id, val in assignment.items():
            ticket = self.problem.ticket_by_id[ticket_id]
            tech_queues[val.technician_id].append(ticket)

        # Urutkan per teknisi berdasarkan urutan hasil solver
        for t_id in tech_queues:
            tech_queues[t_id].sort(key=lambda t: assignment[t.ticket_id].order_position)

        assignments: List[TaskAssignment] = []
        total_travel_minutes = 0
        total_lateness_minutes = 0
        total_penalty = 0.0
        makespan = 0.0
        tech_workloads: Dict[str, int] = {t_id: 0 for t_id in self.problem.technicians}
        violations: List[str] = []

        base_start = datetime(2026, 10, 2, 8, 0)

        for t_id, queue in tech_queues.items():
            tech = self.problem.technicians[t_id]
            current_location = tech.base_location
            current_time = base_start

            for ticket in queue:
                # 1. Hitung waktu tempuh navigasi gedung FITE
                travel_time = self.problem.distance_matrix.get_travel_time(current_location, ticket.location)
                arrival_time = current_time + timedelta(minutes=travel_time)

                # Teknisi mulai bekerja setelah tiba di lokasi (atau saat request tiket jika request lebih lambat)
                start_work_time = max(arrival_time, ticket.request_time)
                wait_time = max(0, int((start_work_time - ticket.request_time).total_seconds() / 60))

                finish_work_time = start_work_time + timedelta(minutes=ticket.estimated_duration_minutes)

                # Evaluasi SLA
                deadline = ticket.deadline
                sla_violated = finish_work_time > deadline
                lateness = max(0, int((finish_work_time - deadline).total_seconds() / 60))

                # Formulasi Penalti Bisnis
                # Penalti = Bobot Urgensi x Keterlambatan + Biaya Tempuh
                urgency_multiplier = ticket.urgency.priority_rank * 2.0
                task_penalty = (lateness * urgency_multiplier) + (travel_time * 0.5)

                if sla_violated:
                    violations.append(
                        f"Tiket {ticket.ticket_id} ({ticket.urgency.value}) melampaui SLA sebesar {lateness} menit!"
                    )

                assignments.append(
                    TaskAssignment(
                        ticket=ticket,
                        technician=tech,
                        start_time=start_work_time,
                        finish_time=finish_work_time,
                        travel_time_minutes=travel_time,
                        wait_time_minutes=wait_time,
                        sla_violated=sla_violated,
                        lateness_minutes=lateness,
                        penalty=task_penalty,
                    )
                )

                total_travel_minutes += travel_time
                total_lateness_minutes += lateness
                total_penalty += task_penalty
                tech_workloads[t_id] += ticket.estimated_duration_minutes + travel_time

                # Update status pergerakan teknisi
                current_location = ticket.location
                current_time = finish_work_time

            duration_since_base = (current_time - base_start).total_seconds() / 60
            if duration_since_base > makespan:
                makespan = duration_since_base

        # Urutkan penugasan global berdasarkan waktu mulai pengerjaan
        assignments.sort(key=lambda a: a.start_time)

        return ScheduleSolution(
            assignments=assignments,
            is_valid=(len(violations) == 0),
            total_makespan_minutes=makespan,
            total_travel_time_minutes=float(total_travel_minutes),
            total_lateness_minutes=float(total_lateness_minutes),
            total_penalty=total_penalty,
            violations=violations,
            technician_workloads=tech_workloads,
            algorithm_name="CSP Solver (AC-3 + Backtracking MRV/Degree/LCV)",
            computation_time_ms=computation_time_ms,
            explored_states_or_generations=self.backtrack_count,
        )
