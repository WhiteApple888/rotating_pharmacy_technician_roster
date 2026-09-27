"""Application workflow for a roster audit."""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .individual_staff_constraints import AuditFailure, audit_individual_rules
from .daily_constraints import audit_daily_rules
from .report import write_report
from .workbook import load_roster


@dataclass(frozen=True)
class AuditResult:
    """The outcome of auditing and reporting on one roster workbook."""

    failures: list[AuditFailure]
    report_path: Path

    @property
    def passed(self) -> bool:
        return not self.failures


def audit_roster(source: Path, sheet_name: str | None, ph_days: set[int], start_date: date | None = None, report_path: Path | None = None,) -> AuditResult:
    """Load, audit, and report on a roster workbook."""
    roster = load_roster(source, sheet_name)
    failures = audit_individual_rules(roster) + audit_daily_rules(roster, ph_days, start_date)
    resolved_report_path = report_path or source.with_name(f"{source.stem}_audit.xlsx")
    write_report(resolved_report_path, failures, source, roster, ph_days)
    return AuditResult(failures=failures, report_path=resolved_report_path)
