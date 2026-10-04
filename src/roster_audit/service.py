"""Application workflow for a roster audit."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .individual_staff_constraints import AuditFailure, audit_individual_rules, audit_rest_day_spacing
from .daily_constraints import audit_daily_rules
from .report import write_report
from .workbook import load_last_roster_rest_days, load_roster


@dataclass(frozen=True)
class AuditResult:
    """The outcome of auditing and reporting on one roster workbook."""

    failures: list[AuditFailure]
    report_path: Path

    @property
    def passed(self) -> bool:
        return not self.failures

def audit_roster(source: Path, sheet_name: str | None, ph_days: set[int], start_date: date | None = None, report_path: Path | None = None,) -> AuditResult:
    """Load, audit, and report on a roster workbook including RD history checks."""
    if start_date is None:
        raise ValueError("--start_date is required to audit lastRosterRD and RD work stretches.")

    roster = load_roster(source, sheet_name)
    prior_rest_days = load_last_roster_rest_days(source, start_date)

    boundary_spacing_failures = [
        failure
        for schedule, previous_rest_day in zip(roster.staff, prior_rest_days.dates)
        for failure in audit_rest_day_spacing(
            schedule, previous_rest_day, start_date, include_schedule_gaps=False,
        )
    ]
    failures = (
        audit_individual_rules(roster, start_date)
        + audit_daily_rules(roster, ph_days, start_date)
        + boundary_spacing_failures
    )
    resolved_report_path = report_path or source.with_name(f"{source.stem}_audit.xlsx")
    write_report(resolved_report_path, failures, source, roster, ph_days)
    return AuditResult(failures=failures, report_path=resolved_report_path)
