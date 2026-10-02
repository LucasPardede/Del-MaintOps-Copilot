"""
Test Suite 01: Baseline Search & Priority Queue (Milestone 1 Core)
------------------------------------------------------------------
Memvalidasi:
- PriorityTicketQueue dengan min-heap heapq & FIFO tie-breaker
- Uniform Cost Search (UCS) pada graf FITE
- A* Search dengan heuristik admissible
- Kesetaraan matematis biaya rute UCS == A*
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.models import PriorityTicketQueue, Ticket
from navigation.graph import FITE_UNIFIED_GRAPH
from navigation.router import a_star_search, uniform_cost_search


def test_priority_queue_ordering():
    q = PriorityTicketQueue()
    q.push("T1", "Saung", "Kursi retak", "rendah")
    q.push("T2", "Lab Jaringan", "LAN mati", "kritis")
    q.push("T3", "Idea Hub", "AC tidak dingin", "sedang")
    q.push("T4", "Kelas 711", "Proyektor mati", "tinggi")

    order = [t.urgency for t in q.as_sorted_list()]
    assert order == ["kritis", "tinggi", "sedang", "rendah"]


def test_ucs_and_a_star_optimality():
    start = "Posko Teknisi"
    goal = "Lab Jaringan"
    ucs_path, ucs_cost = uniform_cost_search(FITE_UNIFIED_GRAPH, start, goal)
    astar_path, astar_cost = a_star_search(FITE_UNIFIED_GRAPH, start, goal)

    assert ucs_cost == astar_cost == 5.0
    assert ucs_path is not None and astar_path is not None
    assert ucs_path[0] == astar_path[0] == start
    assert ucs_path[-1] == astar_path[-1] == goal
