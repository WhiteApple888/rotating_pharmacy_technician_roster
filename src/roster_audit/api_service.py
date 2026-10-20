"""In-memory application service used by the HTTP API.

This module deliberately knows nothing about FastAPI.  It converts uploaded
workbook bytes into the domain model and applies the existing audit policies.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO

from .individual_staff_constraints import AuditFailure
from .service import audit_loaded_roster
from .workbook import load_last_roster_rest_days, load_roster


def audit_uploaded_roster(
    workbook_bytes: bytes,
    *,
    start_date: date,
    public_holiday_days: set[int],
    num_staff: int,
) -> tuple[str, list[AuditFailure]]:
    """Audit an uploaded workbook without writing files to the server.

    The uploaded workbook uses the same per-person ``lastRosterRD`` history
    sheet as the command-line workflow.
    """
    roster = load_roster(BytesIO(workbook_bytes), sheet_name=None, num_staff=num_staff)
    prior_rest_days = load_last_roster_rest_days(
        BytesIO(workbook_bytes), start_date, num_staff=num_staff,
    )
    failures = audit_loaded_roster(
        roster,
        public_holiday_days,
        start_date,
        prior_rest_days.dates,
    )
    return roster.worksheet, failures
