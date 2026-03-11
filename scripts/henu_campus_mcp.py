#!/usr/bin/env python3
"""
HENU Campus Skill API Wrapper.
Expose the same functional surface as mcp_server.py for CLI/Skill usage.
"""

from __future__ import annotations

import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from mcp_server import (  # noqa: E402
    current_course,
    latest_schedule,
    latest_schedule_current_week,
    library_cancel,
    library_locations,
    library_records,
    library_reserve,
    set_calibration_source,
    setup_account,
    sync_schedule,
    system_status,
)

__all__ = [
    "setup_account",
    "sync_schedule",
    "current_course",
    "latest_schedule",
    "latest_schedule_current_week",
    "library_locations",
    "library_reserve",
    "library_records",
    "library_cancel",
    "set_calibration_source",
    "system_status",
]

