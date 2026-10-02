"""
Del-MaintOps Copilot - CLI Interface Adapter
--------------------------------------------
Membungkus DelMaintOpsAppCLI untuk kompatibilitas penuh dengan test suite M1 & M2.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.models import MaintenanceTicket, Ticket
from interfaces.cli_app import DelMaintOpsAppCLI, STATUS_FLOW
from knowledge.sops import (
    SOP_KB,
    classify_urgency,
    detect_category,
    find_sop,
)


@dataclass
class TicketRecord:
    """Rekaman status tiket interaktif CLI."""
    ticket: Any
    sop_id: Optional[str]
    status: str = "Reported"
    reported_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    route_ucs: Optional[List[str]] = None
    route_astar: Optional[List[str]] = None
    route_cost: Optional[float] = None


class DelMaintOpsCopilotCLI(DelMaintOpsAppCLI):
    """Subclass dengan kompatibilitas eksplisit atribut Milestone 1."""
    pass


def main() -> None:
    app = DelMaintOpsCopilotCLI()
    app.run()


if __name__ == "__main__":
    main()
