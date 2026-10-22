"""Tests for the application workflow."""

import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from roster_audit.individual_staff_constraints import AuditFailure, Roster, StaffSchedule
from roster_audit.service import AuditResult, audit_roster
from roster_audit.workbook import LastRosterRestDays


class ServiceTests(unittest.TestCase):
    def test_result_passed_reflects_failures(self) -> None:
        self.assertTrue(AuditResult([], Path("report.xlsx")).passed)
        self.assertFalse(AuditResult([AuditFailure("test", "failed")], Path("report.xlsx")).passed)

    def test_audit_roster_requires_a_start_date(self) -> None:
        with self.assertRaisesRegex(ValueError, "--start_date is required"):
            audit_roster(Path("roster.xlsx"), None, set())

    def test_audit_roster_uses_each_staff_members_history_for_boundary_checks(self) -> None:
        roster = Roster("Roster", (StaffSchedule(6, ("XE1",) * 28),))
        history = LastRosterRestDays((date(2026, 4, 12),))
        boundary_failure = AuditFailure("Rest day spacing", "boundary failure", staff_row=6)

        with (
            patch("roster_audit.service.load_roster", return_value=roster),
            patch("roster_audit.service.load_last_roster_rest_days", return_value=history),
            patch("roster_audit.service.audit_individual_rules", return_value=[]),
            patch("roster_audit.service.audit_daily_rules", return_value=[]),
            patch("roster_audit.service.audit_rest_day_spacing", return_value=[boundary_failure]) as spacing,
            patch("roster_audit.service.write_report") as write_report,
        ):
            result = audit_roster(Path("roster.xlsx"), None, set(), date(2026, 4, 13))

        self.assertEqual(result.failures, [boundary_failure])
        spacing.assert_called_once_with(
            roster.staff[0], history.dates[0], date(2026, 4, 13), include_schedule_gaps=False,
        )
        write_report.assert_called_once()
