"""The audit and CP-SAT interpretations agree on rest-day examples."""

import unittest
from datetime import date, timedelta

from ortools.sat.python import cp_model

from roster_audit.individual_staff_constraints import (
    StaffSchedule, audit_rest_day_spacing, audit_weekly_rest_days,
)
from roster_audit.optimizer import NoFeasibleRosterError, _add_rest_day_constraints


START = date(2026, 4, 13)


def schedule_with_rest_days(rest_days):
    return StaffSchedule(6, tuple(rest_days.get(day, "OFF") for day in range(1, 29)))


class RestDayParityTests(unittest.TestCase):
    def assert_policy(self, rest_days, previous_days, expected):
        schedule = schedule_with_rest_days(rest_days)
        previous = START - timedelta(days=previous_days)
        audit_passes = not (
            audit_weekly_rest_days(schedule)
            + audit_rest_day_spacing(schedule, previous, START)
        )

        model = cp_model.CpModel()

        def fixed_shift(staff, day, accepted):
            return int(schedule.shifts[day - 1] in accepted)

        try:
            _add_rest_day_constraints(model, fixed_shift, 1, previous, START)
            solver_passes = cp_model.CpSolver().solve(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        except NoFeasibleRosterError:
            solver_passes = False

        self.assertEqual(audit_passes, expected, "audit")
        self.assertEqual(solver_passes, expected, "solver")

    def test_spacing_between_rest_days(self):
        self.assert_policy({1: "RD", 14: "VLRD", 21: "RD", 28: "RD"}, 1, True)
        for marker in ("RD+", "RD++"):
            with self.subTest(marker=marker):
                self.assert_policy({2: "RD", 14: marker, 15: "RD", 22: "RD"}, 1, True)
                # The marked day meets the weekly rule but does not reset spacing.
                self.assert_policy({1: "RD", 8: marker, 15: "RD", 22: "RD"}, 1, False)

    def test_previous_roster_boundary(self):
        rests = {6: "RD", 8: "RD", 15: "RD", 22: "RD"}
        self.assert_policy(rests, 8, True)   # 12 days between previous RD and day 6.
        self.assert_policy(rests, 9, False)  # 13 days between them.
        self.assert_policy(rests, 14, False)  # Already overdue at the start.

    def test_trailing_roster_boundary(self):
        self.assert_policy({1: "RD", 8: "RD", 16: "VLRD", 22: "RD+"}, 1, True)
        self.assert_policy({1: "RD", 8: "RD", 15: "RD", 22: "RD++"}, 1, False)

    def test_weekly_rest_day_count(self):
        self.assert_policy({1: "RD", 8: "RD", 15: "RD", 22: "RD"}, 1, True)
        self.assert_policy({1: "RD", 8: "RD", 15: "RD", 22: "RD", 23: "RD+"}, 1, False)
        self.assert_policy({1: "RD", 8: "RD", 15: "RD"}, 1, False)


if __name__ == "__main__":
    unittest.main()
