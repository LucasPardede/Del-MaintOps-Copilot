"""
Del-MaintOps Copilot - Unified FITE Campus Navigation Graph
----------------------------------------------------------
Graf Terpadu Kanonikal Gedung Fakultas Informatika dan Teknik Elektro (FITE)
Institut Teknologi Del, menggabungkan:
1. Simpul & rute Milestone 1 (Posko Teknisi, Lab RPL, Lab Jaringan, Kelas 301, Idea Hub, Toilet Lt.1, Saung).
2. Simpul perkuliahan resmi Milestone 2:
   - Lantai 1: Kelas 711, 712, Labkom 713, 714, 715, 716.
   - Lantai 2: Kelas 721, 722, Labkom 723, 724, 725, 726.
   - Penghubung: Tangga Utama & Koridor Antarlantai.

Graf bersifat tak-berarah (undirected), simetris, dan setiap edge merepresentasikan
waktu tempuh aktual dalam menit.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Graf terpadu kanonikal gedung FITE: simpul -> list of (tetangga, waktu_menit)
FITE_UNIFIED_GRAPH: Dict[str, List[Tuple[str, int]]] = {
    # --- PUSAT OPERASIONAL & AREA KONEKSI LT. 1 ---
    "Posko Teknisi": [
        ("Lab RPL", 3),
        ("Idea Hub", 5),
        ("Koridor Lt.1 Barat", 2),
        ("Koridor Lt.1 Timur", 2),
    ],
    "Koridor Lt.1 Barat": [
        ("Posko Teknisi", 2),
        ("Tangga Utama", 2),
        ("Kelas 711", 1),
        ("Kelas 712", 1),
        ("Ruang Kelas 301", 2),
        ("Labkom 713", 2),
        ("Koridor Lt.1 Timur", 3),
    ],
    "Koridor Lt.1 Timur": [
        ("Posko Teknisi", 2),
        ("Koridor Lt.1 Barat", 3),
        ("Labkom 714", 2),
        ("Labkom 715", 2),
        ("Labkom 716", 2),
        ("Idea Hub", 3),
    ],

    # --- SIMPUL WARISAN MILESTONE 1 & RUANG LT. 1 ---
    "Lab RPL": [
        ("Posko Teknisi", 3),
        ("Lab Jaringan", 2),
        ("Labkom 714", 1),
    ],
    "Lab Jaringan": [
        ("Lab RPL", 2),
        ("Ruang Kelas 301", 3),
        ("Labkom 716", 1),
    ],
    "Ruang Kelas 301": [
        ("Idea Hub", 4),
        ("Lab Jaringan", 3),
        ("Saung", 2),
        ("Kelas 711", 1),
        ("Koridor Lt.1 Barat", 2),
    ],
    "Saung": [
        ("Ruang Kelas 301", 2),
    ],
    "Idea Hub": [
        ("Posko Teknisi", 5),
        ("Ruang Kelas 301", 4),
        ("Toilet Lt.1", 6),
        ("Koridor Lt.1 Timur", 3),
    ],
    "Toilet Lt.1": [
        ("Idea Hub", 6),
    ],

    # --- KELAS & LABKOM LANTAI 1 (MILESTONE 2) ---
    "Kelas 711": [
        ("Koridor Lt.1 Barat", 1),
        ("Ruang Kelas 301", 1),
        ("Kelas 712", 1),
    ],
    "Kelas 712": [
        ("Koridor Lt.1 Barat", 1),
        ("Kelas 711", 1),
    ],
    "Labkom 713": [
        ("Koridor Lt.1 Barat", 2),
        ("Labkom 714", 1),
    ],
    "Labkom 714": [
        ("Koridor Lt.1 Timur", 2),
        ("Labkom 713", 1),
        ("Labkom 715", 1),
        ("Lab RPL", 1),
    ],
    "Labkom 715": [
        ("Koridor Lt.1 Timur", 2),
        ("Labkom 714", 1),
        ("Labkom 716", 1),
    ],
    "Labkom 716": [
        ("Koridor Lt.1 Timur", 2),
        ("Labkom 715", 1),
        ("Lab Jaringan", 1),
    ],

    # --- KONEKTOR VERTIKAL ANTAR-LANTAI ---
    "Tangga Utama": [
        ("Koridor Lt.1 Barat", 2),
        ("Koridor Lt.2 Barat", 3),
    ],

    # --- LANTAI 2 - KELAS & LABKOM (MILESTONE 2) ---
    "Koridor Lt.2 Barat": [
        ("Tangga Utama", 3),
        ("Kelas 721", 1),
        ("Kelas 722", 1),
        ("Labkom 723", 2),
        ("Koridor Lt.2 Timur", 3),
    ],
    "Kelas 721": [
        ("Koridor Lt.2 Barat", 1),
        ("Kelas 722", 1),
    ],
    "Kelas 722": [
        ("Koridor Lt.2 Barat", 1),
        ("Kelas 721", 1),
    ],
    "Labkom 723": [
        ("Koridor Lt.2 Barat", 2),
        ("Labkom 724", 1),
    ],
    "Koridor Lt.2 Timur": [
        ("Koridor Lt.2 Barat", 3),
        ("Labkom 724", 2),
        ("Labkom 725", 2),
        ("Labkom 726", 2),
    ],
    "Labkom 724": [
        ("Koridor Lt.2 Timur", 2),
        ("Labkom 723", 1),
        ("Labkom 725", 1),
    ],
    "Labkom 725": [
        ("Koridor Lt.2 Timur", 2),
        ("Labkom 724", 1),
        ("Labkom 726", 1),
    ],
    "Labkom 726": [
        ("Koridor Lt.2 Timur", 2),
        ("Labkom 725", 1),
    ],
}

# Alias kanonikal untuk kompatibilitas Milestone 1
FITE_GRAPH = FITE_UNIFIED_GRAPH
