"""Command-line interface for the roster auditor."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .parsing import parse_ph_days
from .service import audit_roster


def main() -> int:
    """Run the roster audit command and return its process exit status."""
    parser = argparse.ArgumentParser(description="Audit a 16-staff, 28-day Excel roster.")
    parser.add_argument("roster", type=Path, help="Input .xlsx roster file")
    parser.add_argument("--sheet", help="Worksheet to audit (default: active worksheet)")
    parser.add_argument(
        "--start_date", type=date.fromisoformat, required=True,
        help="Roster Day 1 date; required for lastRosterRD and RD-stretch validation",
    )
    parser.add_argument("--ph", action="append", default=[], metavar="DAYS", help="Comma-separated PH day numbers and/or ISO dates; may be repeated")
    parser.add_argument("--report", type=Path, help="Output report (default: <roster>_audit.xlsx)")
    args = parser.parse_args()

    if args.roster.suffix.lower() != ".xlsx":
        parser.error("The roster must be an .xlsx file.")
    if not args.roster.is_file():
        parser.error(f"Roster file not found: {args.roster}")
    try:
        ph_days = parse_ph_days(args.ph, args.start_date)
        result = audit_roster(args.roster, args.sheet, ph_days, args.start_date, args.report)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    print("STATUS: PASS" if result.passed else "STATUS: FAIL")
    for failure in result.failures:
        print(failure.message)
    print(f"Audit report: {result.report_path}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
