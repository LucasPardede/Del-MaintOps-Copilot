"""
Del-MaintOps Copilot - FITE Campus Navigation & Distance Matrix
--------------------------------------------------------------
Milestone 2 (W04): Pemodelan Ruang Navigasi Gedung FITE IT Del.

Memetakan topologi ruang fisik gedung FITE:
- Lantai 1: Kelas 711, 712, Labkom 713, 714, 715, 716, Posko Teknisi, Idea Hub.
- Lantai 2: Kelas 721, 722, Labkom 723, 724, 725, 726.
- Penghubung: Tangga Utama & Koridor FITE.
Menyediakan kalkulator jarak berbasis A* dan precomputed O(1) Distance Matrix
untuk optimasi rute teknisi dalam CSP dan Algoritma Genetika.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Set, Tuple

# Graf tak berarah lengkap gedung FITE: simpul -> list (tetangga, waktu tempuh menit)
FITE_TOPOLOGY: Dict[str, List[Tuple[str, int]]] = {
    # Pusat Operasional & Penghubung Lt. 1
    "Posko Teknisi": [("Koridor Lt.1 Barat", 2), ("Koridor Lt.1 Timur", 2)],
    "Tangga Utama": [("Koridor Lt.1 Barat", 2), ("Koridor Lt.2 Barat", 3)],

    # Lantai 1 - Sayap Barat
    "Koridor Lt.1 Barat": [
        ("Posko Teknisi", 2),
        ("Tangga Utama", 2),
        ("Kelas 711", 1),
        ("Kelas 712", 1),
        ("Labkom 713", 2),
        ("Koridor Lt.1 Timur", 3),
    ],
    "Kelas 711": [("Koridor Lt.1 Barat", 1)],
    "Kelas 712": [("Koridor Lt.1 Barat", 1)],
    "Labkom 713": [("Koridor Lt.1 Barat", 2), ("Labkom 714", 1)],

    # Lantai 1 - Sayap Timur
    "Koridor Lt.1 Timur": [
        ("Posko Teknisi", 2),
        ("Koridor Lt.1 Barat", 3),
        ("Labkom 714", 2),
        ("Labkom 715", 2),
        ("Labkom 716", 2),
        ("Idea Hub", 3),
    ],
    "Labkom 714": [("Koridor Lt.1 Timur", 2), ("Labkom 713", 1), ("Labkom 715", 1)],
    "Labkom 715": [("Koridor Lt.1 Timur", 2), ("Labkom 714", 1), ("Labkom 716", 1)],
    "Labkom 716": [("Koridor Lt.1 Timur", 2), ("Labkom 715", 1)],
    "Idea Hub": [("Koridor Lt.1 Timur", 3)],

    # Lantai 2 - Sayap Barat
    "Koridor Lt.2 Barat": [
        ("Tangga Utama", 3),
        ("Kelas 721", 1),
        ("Kelas 722", 1),
        ("Labkom 723", 2),
        ("Koridor Lt.2 Timur", 3),
    ],
    "Kelas 721": [("Koridor Lt.2 Barat", 1)],
    "Kelas 722": [("Koridor Lt.2 Barat", 1)],
    "Labkom 723": [("Koridor Lt.2 Barat", 2), ("Labkom 724", 1)],

    # Lantai 2 - Sayap Timur
    "Koridor Lt.2 Timur": [
        ("Koridor Lt.2 Barat", 3),
        ("Labkom 724", 2),
        ("Labkom 725", 2),
        ("Labkom 726", 2),
    ],
    "Labkom 724": [("Koridor Lt.2 Timur", 2), ("Labkom 723", 1), ("Labkom 725", 1)],
    "Labkom 725": [("Koridor Lt.2 Timur", 2), ("Labkom 724", 1), ("Labkom 726", 1)],
    "Labkom 726": [("Koridor Lt.2 Timur", 2), ("Labkom 725", 1)],
}


def shortest_path_dijkstra(start: str, goal: str) -> Tuple[List[str], int]:
    """Menghitung rute tercepat dan bobot waktu tempuh (menit) antara dua ruangan."""
    if start == goal:
        return [start], 0
    if start not in FITE_TOPOLOGY or goal not in FITE_TOPOLOGY:
        # Fallback untuk lokasi yang belum terdaftar: default estimasi 5 menit
        return [start, goal], 5

    frontier: List[Tuple[int, int, str]] = [(0, 0, start)]
    came_from: Dict[str, str] = {}
    best_cost: Dict[str, int] = {start: 0}
    visited: Set[str] = set()
    counter = 0

    while frontier:
        cost, _, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            # Rekonstruksi rute
            path = [goal]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return path, cost

        for neighbor, weight in FITE_TOPOLOGY.get(current, []):
            new_cost = cost + weight
            if neighbor not in best_cost or new_cost < best_cost[neighbor]:
                best_cost[neighbor] = new_cost
                came_from[neighbor] = current
                counter += 1
                heapq.heappush(frontier, (new_cost, counter, neighbor))

    return [start, goal], 10


class CampusDistanceMatrix:
    """Precomputed O(1) Distance Matrix untuk akses cepat selama eksekusi solver."""

    def __init__(self, topology: Dict[str, List[Tuple[str, int]]] = FITE_TOPOLOGY) -> None:
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
                    _, cost = shortest_path_dijkstra(u, v)
                    self.matrix[(u, v)] = cost

    def get_travel_time(self, origin: str, destination: str) -> int:
        """Mengembalikan waktu tempuh dalam menit antara origin dan destination."""
        if origin == destination:
            return 0
        if (origin, destination) in self.matrix:
            return self.matrix[(origin, destination)]
        # Jika ada lokasi tak dikenal
        _, cost = shortest_path_dijkstra(origin, destination)
        self.matrix[(origin, destination)] = cost
        return cost


# Singleton instance untuk dipakai global
GLOBAL_DISTANCE_MATRIX = CampusDistanceMatrix()
