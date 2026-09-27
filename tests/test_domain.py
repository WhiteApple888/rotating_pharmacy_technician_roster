"""Tests for staff-level roster constraints."""

import unittest

from roster_audit.individual_staff_constraints import (
    Roster,
    StaffSchedule,
    audit_four_week_hours,
    audit_individual_rules,
    audit_no_after_night_shift,
    audit_night_shift_sequence,
    audit_rest_day_spacing,
    audit_weekly_rest_days,
)


class IndividualConstraintTests(unittest.TestCase):
    def test_rest_day_spacing_counts_all_rest_day_codes(self) -> None:
        shifts = ("RD+",) + ("XE1",) * 11 + ("RD++",) + ("XE1",) * 15
        failures = audit_rest_day_spacing(StaffSchedule(6, shifts))

        self.assertEqual(failures, [])

    def test_no_code_requires_a_preceding_night_shift_after_day_one(self) -> None:
        schedule = StaffSchedule(6, ("XE1", "NO") + ("RD",) * 26)

        failures = audit_no_after_night_shift(schedule)

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].day, 2)

    def test_no_code_on_day_one_is_not_checked(self) -> None:
        self.assertEqual(audit_no_after_night_shift(StaffSchedule(6, ("NO",) + ("RD",) * 27)), [])

    def test_night_shift_requires_a_valid_following_shift(self) -> None:
        schedule = StaffSchedule(6, ("D", "XE1") + ("RD",) * 26)

        failures = audit_night_shift_sequence(schedule)

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].day, 1)

    def test_individual_rules_runs_all_constraints_for_each_staff_member(self) -> None:
        roster = Roster("Roster", (StaffSchedule(6, ("XE1", "NO") + ("RD",) * 26),))

        failures = audit_individual_rules(roster)

        self.assertTrue(any(failure.category == "NO after night shift" for failure in failures))

    def test_four_week_hours_accepts_exactly_160_hours(self) -> None:
        schedule = StaffSchedule(6, ("XE1",) * 20 + ("RD",) * 8)

        self.assertEqual(audit_four_week_hours(schedule), [])

    def test_weekly_rest_days_reports_missing_and_multiple_rest_days(self) -> None:
        schedule = StaffSchedule(
            6,
            ("XE1",) * 7
            + ("RD", "RD+") + ("XE1",) * 5
            + ("RD",) + ("XE1",) * 6
            + ("RD",) + ("XE1",) * 6,
        )

        failures = audit_weekly_rest_days(schedule)

        self.assertEqual([failure.message[-7:] for failure in failures], ["Week 1.", "Week 2."])

    def test_rest_day_spacing_reports_gaps_larger_than_twelve_days(self) -> None:
        schedule = StaffSchedule(6, ("RD",) + ("XE1",) * 12 + ("RD",) + ("XE1",) * 14)

        failures = audit_rest_day_spacing(schedule)

        self.assertEqual(len(failures), 1)
        self.assertIn("13 days apart", failures[0].message)
