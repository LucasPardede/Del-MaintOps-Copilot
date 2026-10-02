"""
Del-MaintOps Copilot - Genetic Algorithm (GA) Solver
---------------------------------------------------
Modul optimasi evolusioner:
- Representasi kromosom (teknisi, bobot urutan)
- Formulasi penalti kebugaran (Hard: Kualifikasi, Urgensi | Soft: SLA, Travel, Makespan)
- Seleksi Turnamen (Tournament Selection, k=3)
- Two-Point Crossover & Mutasi Terarah
- Elitisme (E=3) untuk jaminan konvergensi monoton
"""

from __future__ import annotations

import copy
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from core.models import (
    MaintenanceTicket,
    ScheduleSolution,
    SkillCategory,
    TaskAssignment,
    Technician,
    UrgencyLevel,
)
from navigation.router import GLOBAL_DISTANCE_MATRIX, CampusDistanceMatrix


@dataclass
class Chromosome:
    """Individu solusi genetika: list of (technician_index, priority_weight)."""
    genes: List[Tuple[int, float]]
    fitness: float = 0.0
    cost: float = float("inf")
    raw_schedule: Optional[ScheduleSolution] = None


class GeneticAlgorithmSolver:
    """Solver penjadwalan berbasis Algoritma Genetika dengan Elitisme."""

    def __init__(
        self,
        tickets: List[MaintenanceTicket],
        technicians: List[Technician],
        population_size: int = 60,
        generations: int = 100,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.20,
        tournament_size: int = 3,
        elite_count: int = 3,
        distance_matrix: CampusDistanceMatrix = GLOBAL_DISTANCE_MATRIX,
        random_seed: Optional[int] = 42,
    ) -> None:
        self.tickets = tickets
        self.technicians = technicians
        self.tech_count = len(technicians)
        self.ticket_count = len(tickets)
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elite_count = elite_count
        self.distance_matrix = distance_matrix

        if random_seed is not None:
            random.seed(random_seed)

        self.valid_tech_indices: List[List[int]] = []
        for ticket in self.tickets:
            indices = [
                idx for idx, tech in enumerate(self.technicians)
                if ticket.is_compatible_technician(tech)
            ]
            if not indices:
                indices = list(range(self.tech_count))
            self.valid_tech_indices.append(indices)

        self.convergence_history: List[Dict[str, float]] = []

    def _initialize_population(self) -> List[Chromosome]:
        population: List[Chromosome] = []

        for _ in range(self.population_size):
            genes: List[Tuple[int, float]] = []
            for t_idx, ticket in enumerate(self.tickets):
                valid_pool = self.valid_tech_indices[t_idx]
                selected_tech = random.choice(valid_pool) if valid_pool else random.randint(0, self.tech_count - 1)
                base_weight = ticket.urgency.priority_rank * 100.0 - (t_idx * 2.0)
                random_noise = random.uniform(-15.0, 15.0)
                genes.append((selected_tech, base_weight + random_noise))

            chrom = Chromosome(genes=genes)
            self._evaluate_fitness(chrom)
            population.append(chrom)

        return population

    def _decode_chromosome(self, chrom: Chromosome) -> ScheduleSolution:
        base_start = datetime(2026, 10, 2, 8, 0)
        tech_queues: Dict[int, List[Tuple[int, MaintenanceTicket, float]]] = {
            i: [] for i in range(self.tech_count)
        }

        for t_idx, (tech_idx, weight) in enumerate(chrom.genes):
            ticket = self.tickets[t_idx]
            tech_queues[tech_idx].append((t_idx, ticket, weight))

        for tech_idx in tech_queues:
            tech_queues[tech_idx].sort(key=lambda item: -item[2])

        assignments: List[TaskAssignment] = []
        total_travel_minutes = 0
        total_lateness_minutes = 0
        total_penalty = 0.0
        makespan = 0.0
        tech_workloads: Dict[str, int] = {tech.tech_id: 0 for tech in self.technicians}
        violations: List[str] = []

        for tech_idx, queue in tech_queues.items():
            tech = self.technicians[tech_idx]
            current_location = tech.base_location
            current_time = base_start
            prev_ticket_urgency: Optional[UrgencyLevel] = None

            for t_idx, ticket, _ in queue:
                # Cek Hard Constraint 1: Kualifikasi
                if not ticket.is_compatible_technician(tech):
                    violations.append(
                        f"Kualifikasi Ilegal: {ticket.ticket_id} ({ticket.facility}) -> {tech.name}"
                    )
                    total_penalty += 50000.0

                # Cek Hard Constraint 2: Urutan Prioritas Absolut
                if prev_ticket_urgency is not None:
                    if prev_ticket_urgency.priority_rank < ticket.urgency.priority_rank:
                        violations.append(
                            f"Inversi Prioritas: {ticket.ticket_id} ({ticket.urgency.value}) sesudah urgensi lebih rendah pada {tech.name}"
                        )
                        total_penalty += 10000.0

                prev_ticket_urgency = ticket.urgency

                travel_time = self.distance_matrix.get_travel_time(current_location, ticket.location)
                arrival_time = current_time + timedelta(minutes=travel_time)

                start_work_time = max(arrival_time, ticket.request_time)
                wait_time = max(0, int((start_work_time - ticket.request_time).total_seconds() / 60))
                finish_work_time = start_work_time + timedelta(minutes=ticket.estimated_duration_minutes)

                deadline = ticket.deadline
                sla_violated = finish_work_time > deadline
                lateness = max(0, int((finish_work_time - deadline).total_seconds() / 60))

                urgency_multiplier = ticket.urgency.priority_rank * 2.0
                task_penalty = (lateness * urgency_multiplier) + (travel_time * 0.5)

                if sla_violated:
                    violations.append(
                        f"SLA Overrun: {ticket.ticket_id} telat {lateness} mnt."
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
                tech_workloads[tech.tech_id] += ticket.estimated_duration_minutes + travel_time

                current_location = ticket.location
                current_time = finish_work_time

            duration_since_base = (current_time - base_start).total_seconds() / 60
            if duration_since_base > makespan:
                makespan = duration_since_base

        workloads = list(tech_workloads.values())
        if workloads:
            workload_variance = max(workloads) - min(workloads)
            total_penalty += workload_variance * 0.1

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
            algorithm_name="Genetic Algorithm (GA with Elitism & Tournament)",
            computation_time_ms=0.0,
            explored_states_or_generations=0,
        )

    def _evaluate_fitness(self, chrom: Chromosome) -> None:
        schedule = self._decode_chromosome(chrom)
        chrom.cost = schedule.total_penalty + (schedule.total_travel_time_minutes * 0.2) + (schedule.total_makespan_minutes * 0.1)
        chrom.fitness = 100000.0 / (1.0 + chrom.cost)
        chrom.raw_schedule = schedule

    def _select_parent(self, population: List[Chromosome]) -> Chromosome:
        tournament = random.sample(population, self.tournament_size)
        return max(tournament, key=lambda c: c.fitness)

    def _crossover(self, parent1: Chromosome, parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        if random.random() > self.crossover_rate or self.ticket_count <= 2:
            return copy.deepcopy(parent1), copy.deepcopy(parent2)

        pt1 = random.randint(0, self.ticket_count - 2)
        pt2 = random.randint(pt1 + 1, self.ticket_count - 1)

        c1_genes = parent1.genes[:pt1] + parent2.genes[pt1:pt2] + parent1.genes[pt2:]
        c2_genes = parent2.genes[:pt1] + parent1.genes[pt1:pt2] + parent2.genes[pt2:]

        return Chromosome(genes=c1_genes), Chromosome(genes=c2_genes)

    def _mutate(self, chrom: Chromosome) -> None:
        for t_idx in range(self.ticket_count):
            if random.random() < self.mutation_rate:
                tech_idx, weight = chrom.genes[t_idx]
                if random.random() < 0.5:
                    valid_pool = self.valid_tech_indices[t_idx]
                    if len(valid_pool) > 1:
                        new_tech = random.choice([idx for idx in valid_pool if idx != tech_idx])
                        chrom.genes[t_idx] = (new_tech, weight)
                else:
                    new_weight = weight + random.uniform(-25.0, 25.0)
                    chrom.genes[t_idx] = (tech_idx, new_weight)

    def solve(self) -> ScheduleSolution:
        start_time = time.perf_counter()
        population = self._initialize_population()
        self.convergence_history = []
        best_individual = max(population, key=lambda c: c.fitness)

        for gen in range(self.generations):
            population.sort(key=lambda c: c.fitness, reverse=True)
            current_best = population[0]

            if current_best.fitness > best_individual.fitness:
                best_individual = copy.deepcopy(current_best)

            avg_fitness = sum(c.fitness for c in population) / len(population)
            self.convergence_history.append({
                "generation": gen + 1,
                "best_fitness": current_best.fitness,
                "best_cost": current_best.cost,
                "avg_fitness": avg_fitness,
                "violations_count": len(current_best.raw_schedule.violations) if current_best.raw_schedule else 0,
            })

            new_pop: List[Chromosome] = []
            for e in range(self.elite_count):
                new_pop.append(copy.deepcopy(population[e]))

            while len(new_pop) < self.population_size:
                p1 = self._select_parent(population)
                p2 = self._select_parent(population)
                c1, c2 = self._crossover(p1, p2)
                self._mutate(c1)
                self._mutate(c2)
                self._evaluate_fitness(c1)
                self._evaluate_fitness(c2)
                new_pop.append(c1)
                if len(new_pop) < self.population_size:
                    new_pop.append(c2)

            population = new_pop

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        final_schedule = self._decode_chromosome(best_individual)
        final_schedule.computation_time_ms = elapsed_ms
        final_schedule.explored_states_or_generations = self.generations
        return final_schedule
