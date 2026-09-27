"""Tests for daily coverage rule evaluation."""

import unittest
from datetime import date

from roster_audit.daily_constraints import CoverageRule, audit_coverage_rule, audit_daily_rules
from roster_audit.individual_staff_constraints import Roster, StaffSchedule


class DailyConstraintTests(unittest.TestCase):
    def test_coverage_rule_accepts_each_comparison_boundary(self) -> None:
        cases = (
            ("at least", 2, ("Z1", "D")),
            ("exactly", 2, ("Z1", "D")),
            ("at most", 2, ("Z1", "D")),
        )

        for comparison, target, shifts in cases:
            with self.subTest(comparison=comparison):
                rule = CoverageRule("Z1/D", frozenset({"Z1", "D"}), target, comparison, frozenset({"Monday"}))
                self.assertIsNone(audit_coverage_rule(rule, shifts, 1, "Monday", None))

    def test_coverage_failure_includes_the_calendar_date(self) -> None:
        rule = CoverageRule("Z1/D", frozenset({"Z1", "D"}), 2, "exactly", frozenset({"Monday"}))

        failure = audit_coverage_rule(rule, ("Z1",), 1, "Monday", date(2026, 4, 13))

        self.assertIsNotNone(failure)
        self.assertIn("13 April 2026", failure.message)
        self.assertIn("required exactly 2", failure.message)

    def test_weekdays_repeat_for_each_roster_week(self) -> None:
        roster = Roster("Roster", tuple(StaffSchedule(row, ("XE1",) * 28) for row in range(6, 22)))

        failures = audit_daily_rules(roster, set())

        self.assertTrue(any(failure.day == 1 for failure in failures))
        self.assertTrue(any(failure.day == 8 for failure in failures))
