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
    library_auto_signin,
    library_cancel,
    library_current,
    library_locations,
    library_records,
    library_reserve,
    seminar_filters,
    seminar_cancel,
    seminar_group_delete,
    seminar_group_save,
    seminar_groups,
    seminar_signin,
    seminar_auto_signin,
    seminar_signin_tasks,
    seminar_records,
    seminar_reserve,
    seminar_room_detail,
    seminar_rooms,
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
    "library_current",
    "library_auto_signin",
    "library_locations",
    "library_reserve",
    "library_records",
    "library_cancel",
    "seminar_groups",
    "seminar_group_save",
    "seminar_group_delete",
    "seminar_signin",
    "seminar_auto_signin",
    "seminar_signin_tasks",
    "seminar_filters",
    "seminar_records",
    "seminar_rooms",
    "seminar_room_detail",
    "seminar_reserve",
    "seminar_cancel",
    "set_calibration_source",
    "system_status",
]
