"""
Del-MaintOps Copilot - Baseline Search & Priority Queue Module (M1 Interface)
----------------------------------------------------------------------------
Modul pembungkus backward-compatibility yang menghubungkan panggilan Milestone 1
ke implementasi terpadu di paket core dan navigation.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Pastikan sub-package terbaca
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.models import PriorityTicketQueue, Ticket
from navigation.graph import FITE_GRAPH, FITE_UNIFIED_GRAPH
from navigation.router import a_star_search, heuristic, uniform_cost_search

URGENCY_WEIGHT = {"kritis": 0, "tinggi": 1, "sedang": 2, "rendah": 3}


def main() -> None:
    print("=== Del-MaintOps Copilot | Baseline Search Demo (M1) ===\n")
    queue = PriorityTicketQueue()
    queue.push("TKT-001", "Lab Jaringan", "Jaringan LAN mati", "kritis")
    queue.push("TKT-002", "Ruang Kelas 301", "Infokus tidak menyala", "tinggi")
    queue.push("TKT-003", "Saung", "Kursi rusak", "rendah")
    queue.push("TKT-004", "Idea Hub", "AC tidak dingin", "sedang")

    print("Urutan prioritas tiket (heapq):")
    for t in queue.as_sorted_list():
        urg_str = getattr(t.urgency, "value", str(t.urgency)).upper()
        print(f"  [{urg_str:6}] {t.ticket_id} - {t.location}: {t.issue_description}")

    top_ticket = queue.pop()
    print(f"\nTiket berikutnya yang ditangani: {top_ticket.ticket_id} @ {top_ticket.location}\n")

    start, goal = "Posko Teknisi", top_ticket.location
    ucs_path, ucs_cost = uniform_cost_search(FITE_GRAPH, start, goal)
    print(f"UCS  : {' -> '.join(ucs_path)}  | total cost = {ucs_cost} menit")

    astar_path, astar_cost = a_star_search(FITE_GRAPH, start, goal)
    print(f"A*   : {' -> '.join(astar_path)}  | total cost = {astar_cost} menit")

    assert ucs_cost == astar_cost, "A* dengan heuristik admissible harus optimal seperti UCS"
    print("\n[OK] Biaya UCS dan A* identik -> heuristik terbukti admissible & optimal.")


if __name__ == "__main__":
    main()
