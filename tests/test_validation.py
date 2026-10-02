"""
QA validation suite - Milestone 1 (Data & Knowledge Engineer / QA Lead deliverable).
Menjalankan: pytest tests/test_validation.py -v
"""

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from search_baseline import (  # noqa: E402
    FITE_GRAPH,
    PriorityTicketQueue,
    Ticket,
    a_star_search,
    uniform_cost_search,
)
from cli import (  # noqa: E402
    find_relevant_sop,
    generate_ticket_id,
    infer_default_urgency,
    is_duplicate,
)


# ---------------------------------------------------------------------------
# Priority Ticket Queue
# ---------------------------------------------------------------------------

def test_priority_queue_orders_by_urgency():
    q = PriorityTicketQueue()
    q.push("T1", "Saung", "Kursi rusak", "rendah")
    q.push("T2", "Lab Jaringan", "LAN mati", "kritis")
    q.push("T3", "Idea Hub", "AC mati", "sedang")

    order = [t.urgency for t in q.as_sorted_list()]
    assert order == ["kritis", "sedang", "rendah"], "Urutan prioritas tiket salah"


def test_priority_queue_pop_returns_highest_priority_first():
    q = PriorityTicketQueue()
    q.push("T1", "Ruang Kelas 301", "Infokus rusak", "tinggi")
    q.push("T2", "Lab Jaringan", "LAN mati", "kritis")

    first = q.pop()
    assert first.ticket_id == "T2"
    assert first.urgency == "kritis"


def test_priority_queue_invalid_urgency_raises():
    q = PriorityTicketQueue()
    try:
        q.push("T1", "Saung", "Kursi rusak", "urgensi_ga_valid")
        assert False, "Harus melempar ValueError untuk urgensi tidak dikenal"
    except ValueError:
        pass


def test_priority_queue_empty_pop_returns_none():
    q = PriorityTicketQueue()
    assert q.pop() is None
    assert len(q) == 0


# ---------------------------------------------------------------------------
# Uniform Cost Search
# ---------------------------------------------------------------------------

def test_ucs_finds_known_shortest_path():
    path, cost = uniform_cost_search(FITE_GRAPH, "Posko Teknisi", "Lab Jaringan")
    assert path == ["Posko Teknisi", "Lab RPL", "Lab Jaringan"]
    assert cost == 5


def test_ucs_start_equals_goal():
    path, cost = uniform_cost_search(FITE_GRAPH, "Posko Teknisi", "Posko Teknisi")
    assert path == ["Posko Teknisi"]
    assert cost == 0


def test_ucs_unreachable_goal_returns_infinite_cost():
    path, cost = uniform_cost_search(FITE_GRAPH, "Posko Teknisi", "Lokasi Tidak Ada")
    assert path is None
    assert cost == float("inf")


# ---------------------------------------------------------------------------
# A* Search - optimalitas & konsistensi heuristik
# ---------------------------------------------------------------------------

def test_a_star_matches_ucs_cost_on_all_reachable_pairs():
    """Karena heuristik admissible, A* wajib menghasilkan biaya optimal
    yang identik dengan UCS untuk setiap pasangan simpul terjangkau."""
    locations = list(FITE_GRAPH.keys())
    for goal in locations:
        ucs_path, ucs_cost = uniform_cost_search(FITE_GRAPH, "Posko Teknisi", goal)
        astar_path, astar_cost = a_star_search(FITE_GRAPH, "Posko Teknisi", goal)
        assert ucs_cost == astar_cost, f"Biaya UCS vs A* berbeda untuk goal={goal}"
        assert astar_path is not None


def test_a_star_path_is_valid_walk_on_graph():
    path, _ = a_star_search(FITE_GRAPH, "Posko Teknisi", "Toilet Lt.1")
    for a, b in zip(path, path[1:]):
        neighbors = [n for n, _ in FITE_GRAPH[a]]
        assert b in neighbors, f"Edge {a} -> {b} tidak ada di graf (path tidak valid)"


# ---------------------------------------------------------------------------
# Sanity check graf (data integrity)
# ---------------------------------------------------------------------------

def test_graph_is_symmetric_undirected():
    """Setiap edge (a -> b, w) harus punya pasangan (b -> a, w) karena graf
    lokasi gedung bersifat tak berarah (bisa dilalui dua arah)."""
    for node, edges in FITE_GRAPH.items():
        for neighbor, weight in edges:
            reverse_edges = dict(FITE_GRAPH.get(neighbor, []))
            assert node in reverse_edges, f"Graf tidak simetris: {node} <-> {neighbor}"
            assert reverse_edges[node] == weight, f"Bobot tidak konsisten: {node} <-> {neighbor}"


# ---------------------------------------------------------------------------
# CLI interaktif - logika murni (find_relevant_sop, urgensi, duplikasi, id)
# ---------------------------------------------------------------------------

def test_find_relevant_sop_matches_expected_category():
    assert find_relevant_sop("infokus tidak menyala")["id"] == "SOP-01"
    assert find_relevant_sop("AC bocor di lab")["id"] == "SOP-02"
    assert find_relevant_sop("jaringan lab mati total")["id"] == "SOP-03"
    assert find_relevant_sop("kursi saung patah")["id"] == "SOP-04"


def test_find_relevant_sop_returns_none_for_out_of_domain_query():
    assert find_relevant_sop("makanan kantin basi") is None


def test_infer_default_urgency_uses_sop_default():
    assert infer_default_urgency("proyektor mati") == "tinggi"
    assert infer_default_urgency("AC bocor") == "sedang"
    assert infer_default_urgency("kursi saung patah") == "rendah"


def test_infer_default_urgency_network_escalates_during_practicum():
    assert infer_default_urgency("jaringan lab mati", during_practicum=True) == "kritis"
    assert infer_default_urgency("jaringan lab mati", during_practicum=False) == "sedang"


def test_infer_default_urgency_unknown_issue_defaults_to_rendah():
    assert infer_default_urgency("sesuatu yang aneh dan tidak dikenal") == "rendah"


def test_is_duplicate_detects_same_location_and_issue():
    existing = [Ticket(0, "TKT-001", "Lab RPL", "AC mati", "sedang")]
    dup = is_duplicate(existing, "Lab RPL", "AC mati")
    assert dup is not None and dup.ticket_id == "TKT-001"


def test_is_duplicate_returns_none_for_different_issue():
    existing = [Ticket(0, "TKT-001", "Lab RPL", "AC mati", "sedang")]
    assert is_duplicate(existing, "Lab RPL", "infokus mati") is None


def test_generate_ticket_id_increments_sequentially():
    counter = itertools.count(1)
    assert generate_ticket_id(counter) == "TKT-001"
    assert generate_ticket_id(counter) == "TKT-002"
    assert generate_ticket_id(counter) == "TKT-003"
