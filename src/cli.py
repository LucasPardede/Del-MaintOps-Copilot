"""
Del-MaintOps Copilot - CLI Helpers & Entry Point
------------------------------------------------
Menyediakan fungsi logika murni untuk CLI dan kompatibilitas modul Milestone 1.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.models import PriorityTicketQueue, Ticket
from knowledge.sops import SOP_CATALOG, SOP_KB, classify_urgency, detect_category, find_sop
from navigation.graph import FITE_GRAPH
from navigation.router import a_star_search, uniform_cost_search


def find_relevant_sop(query: str) -> Optional[Dict[str, object]]:
    """Mencari entitas SOP yang cocok dengan kueri bebas (untuk pengujian M1)."""
    sop_id = detect_category(query)
    if not sop_id:
        hits = find_sop(query)
        if hits:
            sop_id = hits[0]
    if not sop_id or sop_id not in SOP_KB:
        return None

    sop = SOP_KB[sop_id]
    return {
        "id": sop_id,
        "judul": sop["title"],
        "kata_kunci": sop["keywords"],
        "urgensi_default": sop["default_urgency"],
        "sla": sop["sla"],
        "ringkasan": " ".join(sop["procedure"][:2]),
    }


def generate_ticket_id(counter: itertools.count) -> str:
    """Menghasilkan ID tiket berurutan."""
    return f"TKT-{next(counter):03d}"


def infer_default_urgency(
    issue_type: str,
    during_practicum: bool = False,
    practicum_active: bool = False,
    **kwargs,
) -> str:
    """Menginferensi urgensi berdasarkan SOP."""
    sop_id = detect_category(issue_type)
    if not sop_id:
        return "rendah"
    is_practicum = during_practicum or practicum_active
    return classify_urgency(sop_id, practicum_active=is_practicum)


def is_duplicate(
    active_tickets: Any,
    location: Optional[str] = None,
    issue_type: Optional[str] = None,
) -> Optional[Any]:
    """Mengecek apakah laporan duplikat pada lokasi dan kategori yang sama.
    Mendukung signature:
      is_duplicate(active_tickets, location, issue_type)
      is_duplicate(location, issue_type, active_tickets)
    """
    if isinstance(active_tickets, str):
        # Dipanggil dengan signature is_duplicate(location, issue_type, active_tickets)
        loc = active_tickets
        iss = location
        tickets = issue_type if isinstance(issue_type, list) else []
    else:
        tickets = active_tickets if isinstance(active_tickets, list) else []
        loc = location
        iss = issue_type

    if not loc or not iss:
        return None

    cat = detect_category(iss)
    for t in tickets:
        t_loc = getattr(t, "location", None) or (t.get("location") if isinstance(t, dict) else None)
        t_iss = (
            getattr(t, "issue_type", None)
            or getattr(t, "issue_description", None)
            or (t.get("issue_type") if isinstance(t, dict) else None)
        )
        if t_loc == loc:
            existing_cat = detect_category(str(t_iss))
            if existing_cat and cat and existing_cat == cat:
                return t
            if str(t_iss).strip().lower() == iss.strip().lower():
                return t
    return None


def main() -> None:
    from interfaces.cli_app import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
