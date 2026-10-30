"""Tests for staff-level roster constraints."""

import unittest
from datetime import date

from roster_audit.individual_staff_constraints import (
    Roster,
    StaffSchedule,
    audit_consecutive_night_shifts,
    audit_four_week_hours,
    audit_individual_rules,
    audit_no_after_night_shift,
    audit_night_shift_sequence,
    audit_rest_day_spacing,
    audit_weekly_rest_days,
)


class IndividualConstraintTests(unittest.TestCase):
    def test_three_consecutive_nights_are_rejected_across_a_week_boundary(self) -> None:
        shifts = ("Z1",) * 5 + ("P", "W", "D", "NO") + ("Z1",) * 19

        failures = audit_consecutive_night_shifts(StaffSchedule(6, shifts))

        self.assertEqual([(failure.category, failure.day) for failure in failures], [
            ("Consecutive night shifts", 8),
        ])

    def test_two_consecutive_nights_are_allowed(self) -> None:
        shifts = ("P", "W", "NO") + ("Z1",) * 25

        self.assertEqual(audit_consecutive_night_shifts(StaffSchedule(6, shifts)), [])

    def test_rest_day_spacing_uses_rd_and_vlrd_for_work_stretches(self) -> None:
        shifts = ("RD",) + ("XE1",) * 11 + ("VLRD",) + ("XE1",) * 11 + ("RD",) * 4
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
        schedule = StaffSchedule(6, ("RD",) + ("Z1",) * 13 + ("RD",) + ("XE1",) * 13)

        failures = audit_rest_day_spacing(schedule, start_date=date(2026, 4, 13))

        self.assertEqual(len(failures), 2)
        self.assertIn("13 days apart", failures[0].message)

    def test_rest_day_spacing_includes_the_prior_roster_rd_boundary(self) -> None:
        schedule = StaffSchedule(6, ("XE1",) * 12 + ("RD",) + ("RD",) * 15)

        failures = audit_rest_day_spacing(
            schedule, date(2026, 4, 11), date(2026, 4, 13), include_schedule_gaps=False,
        )

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].day, 13)
        self.assertIn("25 April 2026", failures[0].message)
        self.assertIn("13 consecutive working days", failures[0].message)

    def test_rest_day_spacing_flags_a_roster_that_ends_with_more_than_twelve_work_days(self) -> None:
        schedule = StaffSchedule(6, ("RD",) + ("XE1",) * 27)

        failures = audit_rest_day_spacing(
            schedule, date(2026, 4, 12), date(2026, 4, 13), include_schedule_gaps=False,
        )

        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0].day, 28)
        self.assertIn("27 consecutive working days", failures[0].message)
