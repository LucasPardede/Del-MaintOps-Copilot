"""
Del-MaintOps Copilot - Root Alias for solver.py
-----------------------------------------------
Memungkinkan eksekusi langsung dari root repositori:
    python solver.py
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from solver import (
    main,
    run_csp_solver,
    run_ga_solver,
    solve_maintenance_schedule,
)

if __name__ == "__main__":
    main()
