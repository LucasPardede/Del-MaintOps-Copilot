"""
Del-MaintOps Copilot - Baseline Search & Priority Queue Module
-----------------------------------------------------------------
Milestone 1 (W02) - AI Architect deliverable.

Implementasi:
1. PriorityTicketQueue  -> antrean prioritas tiket kerusakan berbasis heapq.
2. uniform_cost_search  -> UCS pada graf lokasi gedung FITE.
3. a_star_search        -> A* dengan heuristik admissible (estimasi jarak minimum).

Representasi ruang keadaan mengacu pada docs/state_space.md.
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 1. Priority Ticket Queue (heapq)
# ---------------------------------------------------------------------------

@dataclass(order=True)
class Ticket:
    """Representasi satu tiket laporan kerusakan fasilitas."""
    priority_score: float
    ticket_id: str = field(compare=False)
    location: str = field(compare=False)
    issue_type: str = field(compare=False)
    urgency: str = field(compare=False)  # "kritis" | "tinggi" | "sedang" | "rendah"


URGENCY_WEIGHT = {"kritis": 0, "tinggi": 1, "sedang": 2, "rendah": 3}


class PriorityTicketQueue:
    """Antrean prioritas tiket kerusakan menggunakan heapq (min-heap).

    Skor prioritas lebih kecil => ditangani lebih dulu. Skor dihitung dari
    bobot urgensi kategori (lihat URGENCY_WEIGHT) sehingga tiket "kritis"
    selalu keluar sebelum tiket "rendah".
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[float, int, Ticket]] = []
        self._counter = itertools.count()  # tie-breaker agar heap stabil

    def push(self, ticket_id: str, location: str, issue_type: str, urgency: str) -> None:
        if urgency not in URGENCY_WEIGHT:
            raise ValueError(f"Urgensi tidak dikenal: {urgency!r}")
        score = URGENCY_WEIGHT[urgency]
        ticket = Ticket(score, ticket_id, location, issue_type, urgency)
        heapq.heappush(self._heap, (score, next(self._counter), ticket))

    def pop(self) -> Optional[Ticket]:
        if not self._heap:
            return None
        _, _, ticket = heapq.heappop(self._heap)
        return ticket

    def __len__(self) -> int:
        return len(self._heap)

    def as_sorted_list(self) -> List[Ticket]:
        """Kembalikan salinan tiket terurut tanpa mengubah heap asli."""
        return [t for _, _, t in sorted(self._heap)]


# ---------------------------------------------------------------------------
# 2. Graf lokasi gedung FITE (State Space)
# ---------------------------------------------------------------------------

# Graf tak berarah: lokasi -> daftar (tetangga, bobot waktu tempuh dalam menit)
FITE_GRAPH: Dict[str, List[Tuple[str, int]]] = {
    "Posko Teknisi": [("Lab RPL", 3), ("Idea Hub", 5)],
    "Lab RPL": [("Posko Teknisi", 3), ("Lab Jaringan", 2)],
    "Lab Jaringan": [("Lab RPL", 2), ("Ruang Kelas 301", 3)],
    "Idea Hub": [("Posko Teknisi", 5), ("Ruang Kelas 301", 4), ("Toilet Lt.1", 6)],
    "Ruang Kelas 301": [("Idea Hub", 4), ("Lab Jaringan", 3), ("Saung", 2)],
    "Saung": [("Ruang Kelas 301", 2)],
    "Toilet Lt.1": [("Idea Hub", 6)],
}


def _reconstruct_path(came_from: Dict[str, str], start: str, goal: str) -> List[str]:
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# 3. Uniform Cost Search (UCS)
# ---------------------------------------------------------------------------

def uniform_cost_search(graph: Dict[str, List[Tuple[str, int]]], start: str, goal: str):
    """Mengembalikan (path, total_cost) rute termurah dari start ke goal."""
    frontier: List[Tuple[int, int, str]] = [(0, 0, start)]
    counter = itertools.count(1)
    came_from: Dict[str, str] = {}
    best_cost: Dict[str, int] = {start: 0}
    visited = set()

    while frontier:
        cost, _, node = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            return _reconstruct_path(came_from, start, goal), cost

        for neighbor, weight in graph.get(node, []):
            new_cost = cost + weight
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = node
                heapq.heappush(frontier, (new_cost, next(counter), neighbor))

    return None, float("inf")  # goal tidak terjangkau


# ---------------------------------------------------------------------------
# 4. A* Search dengan heuristik admissible
# ---------------------------------------------------------------------------

def _min_edge_lower_bound(graph: Dict[str, List[Tuple[str, int]]]) -> int:
    """Bobot edge minimum di seluruh graf -> dipakai sebagai basis heuristik
    admissible (estimasi tidak pernah melebihi biaya riil)."""
    weights = [w for edges in graph.values() for _, w in edges]
    return min(weights) if weights else 0


def heuristic(graph: Dict[str, List[Tuple[str, int]]], node: str, goal: str,
              hop_estimate: Dict[str, int]) -> int:
    """h(node) = jumlah minimum hop (perkiraan, dari BFS) x bobot edge minimum
    di graf. Karena bobot edge minimum <= bobot edge riil manapun, estimasi
    ini tidak pernah overestimate -> admissible."""
    min_edge = _min_edge_lower_bound(graph)
    return hop_estimate.get(node, 0) * min_edge


def _bfs_hop_count(graph: Dict[str, List[Tuple[str, int]]], goal: str) -> Dict[str, int]:
    """Hitung jumlah hop minimum dari setiap simpul menuju goal (BFS mundur)."""
    from collections import deque

    hops = {goal: 0}
    queue = deque([goal])
    while queue:
        current = queue.popleft()
        for neighbor, _ in graph.get(current, []):
            if neighbor not in hops:
                hops[neighbor] = hops[current] + 1
                queue.append(neighbor)
    return hops


def a_star_search(graph: Dict[str, List[Tuple[str, int]]], start: str, goal: str):
    """Mengembalikan (path, total_cost) rute termurah dari start ke goal
    menggunakan A* dengan heuristik admissible & konsisten."""
    hop_estimate = _bfs_hop_count(graph, goal)

    counter = itertools.count(1)
    frontier: List[Tuple[int, int, int, str]] = [
        (heuristic(graph, start, goal, hop_estimate), 0, 0, start)
    ]
    came_from: Dict[str, str] = {}
    best_cost: Dict[str, int] = {start: 0}
    visited = set()

    while frontier:
        _, cost, _, node = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            return _reconstruct_path(came_from, start, goal), cost

        for neighbor, weight in graph.get(node, []):
            new_cost = cost + weight
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = node
                priority = new_cost + heuristic(graph, neighbor, goal, hop_estimate)
                heapq.heappush(frontier, (priority, new_cost, next(counter), neighbor))

    return None, float("inf")


# ---------------------------------------------------------------------------
# 5. Demo end-to-end
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Del-MaintOps Copilot | Baseline Search Demo ===\n")

    # --- Priority Ticket Queue ---
    queue = PriorityTicketQueue()
    queue.push("TKT-001", "Lab Jaringan", "Jaringan LAN mati", "kritis")
    queue.push("TKT-002", "Ruang Kelas 301", "Infokus tidak menyala", "tinggi")
    queue.push("TKT-003", "Saung", "Kursi rusak", "rendah")
    queue.push("TKT-004", "Idea Hub", "AC tidak dingin", "sedang")

    print("Urutan prioritas tiket (heapq):")
    for t in queue.as_sorted_list():
        print(f"  [{t.urgency.upper():6}] {t.ticket_id} - {t.location}: {t.issue_type}")

    # --- UCS & A* dari Posko Teknisi ke tiket paling prioritas ---
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
