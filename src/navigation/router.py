"""
Del-MaintOps Copilot - Navigation & Routing Engine (UCS & A*)
------------------------------------------------------------
Modul ini mengimplementasikan algoritma pencarian rute terpendek:
1. Uniform Cost Search (UCS) berbasis min-heap heapq.
2. A* Search dengan fungsi heuristik admissible & konsisten.
3. Precomputed Campus Distance Matrix untuk komputasi jarak O(1) pada solver CSP/GA.
"""

from __future__ import annotations

import heapq
import itertools
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from navigation.graph import FITE_UNIFIED_GRAPH


def _reconstruct_path(came_from: Dict[str, str], start: str, goal: str) -> List[str]:
    """Rekonstruksi jalur dari titik awal ke tujuan."""
    path = [goal]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# 1. Uniform Cost Search (UCS)
# ---------------------------------------------------------------------------

def uniform_cost_search(
    graph: Dict[str, List[Tuple[str, int]]],
    start: str,
    goal: str,
) -> Tuple[Optional[List[str]], float]:
    """Mengembalikan (path, total_cost) rute termurah dari start ke goal menggunakan UCS."""
    if start == goal:
        return [start], 0.0

    frontier: List[Tuple[int, int, str]] = [(0, 0, start)]
    counter = itertools.count(1)
    came_from: Dict[str, str] = {}
    best_cost: Dict[str, int] = {start: 0}
    visited: Set[str] = set()

    while frontier:
        cost, _, node = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            return _reconstruct_path(came_from, start, goal), float(cost)

        for neighbor, weight in graph.get(node, []):
            new_cost = cost + weight
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = node
                heapq.heappush(frontier, (new_cost, next(counter), neighbor))

    return None, float("inf")


# Alias shortest_path_dijkstra untuk kompatibilitas
shortest_path_dijkstra = uniform_cost_search


# ---------------------------------------------------------------------------
# 2. A* Search dengan Heuristik Admissible & Konsisten
# ---------------------------------------------------------------------------

def _min_edge_lower_bound(graph: Dict[str, List[Tuple[str, int]]]) -> int:
    """Bobot edge minimum di seluruh graf (basis batas bawah heuristik)."""
    weights = [w for edges in graph.values() for _, w in edges]
    return min(weights) if weights else 0


def _bfs_hop_count(graph: Dict[str, List[Tuple[str, int]]], goal: str) -> Dict[str, int]:
    """Hitung jumlah hop minimum dari setiap simpul menuju goal (BFS mundur)."""
    hops = {goal: 0}
    queue = deque([goal])
    while queue:
        current = queue.popleft()
        for neighbor, _ in graph.get(current, []):
            if neighbor not in hops:
                hops[neighbor] = hops[current] + 1
                queue.append(neighbor)
    return hops


def heuristic(
    graph: Dict[str, List[Tuple[str, int]]],
    node: str,
    goal: str,
    hop_estimate: Dict[str, int],
) -> int:
    """h(node) = minimum hop ke goal x bobot edge minimum graf.
    
    Karena bobot edge minimum <= bobot edge riil manapun di graf,
    h(node) tidak pernah overestimate biaya sesungguhnya -> Admissible & Optimal.
    """
    min_edge = _min_edge_lower_bound(graph)
    return hop_estimate.get(node, 0) * min_edge


def a_star_search(
    graph: Dict[str, List[Tuple[str, int]]],
    start: str,
    goal: str,
) -> Tuple[Optional[List[str]], float]:
    """Mengembalikan (path, total_cost) rute termurah dari start ke goal menggunakan A*."""
    if start == goal:
        return [start], 0.0

    hop_estimate = _bfs_hop_count(graph, goal)
    counter = itertools.count(1)
    frontier: List[Tuple[int, int, int, str]] = [
        (heuristic(graph, start, goal, hop_estimate), 0, 0, start)
    ]
    came_from: Dict[str, str] = {}
    best_cost: Dict[str, int] = {start: 0}
    visited: Set[str] = set()

    while frontier:
        _, cost, _, node = heapq.heappop(frontier)
        if node in visited:
            continue
        visited.add(node)

        if node == goal:
            return _reconstruct_path(came_from, start, goal), float(cost)

        for neighbor, weight in graph.get(node, []):
            new_cost = cost + weight
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = node
                priority = new_cost + heuristic(graph, neighbor, goal, hop_estimate)
                heapq.heappush(frontier, (priority, new_cost, next(counter), neighbor))

    return None, float("inf")


# ---------------------------------------------------------------------------
# 3. Precomputed Distance Matrix untuk Solvers
# ---------------------------------------------------------------------------

class CampusDistanceMatrix:
    """Tabel pencarian jarak precomputed O(1) untuk optimasi kecepatan solver."""

    def __init__(self, topology: Dict[str, List[Tuple[str, int]]] = FITE_UNIFIED_GRAPH) -> None:
        self.topology = topology
        self.matrix: Dict[Tuple[str, str], int] = {}
        self._precompute()

    def _precompute(self) -> None:
        nodes = list(self.topology.keys())
        for u in nodes:
            for v in nodes:
                if u == v:
                    self.matrix[(u, v)] = 0
                elif (v, u) in self.matrix:
                    self.matrix[(u, v)] = self.matrix[(v, u)]
                else:
                    _, cost = uniform_cost_search(self.topology, u, v)
                    self.matrix[(u, v)] = int(cost) if cost != float("inf") else 10

    def get_travel_time(self, origin: str, destination: str) -> int:
        """Mengembalikan waktu tempuh dalam menit."""
        if origin == destination:
            return 0
        if (origin, destination) in self.matrix:
            return self.matrix[(origin, destination)]
        # Fallback jika ada lokasi dinamis
        _, cost = uniform_cost_search(self.topology, origin, destination)
        c = int(cost) if cost != float("inf") else 5
        self.matrix[(origin, destination)] = c
        return c


GLOBAL_DISTANCE_MATRIX = CampusDistanceMatrix()
