"""Check audit and solver agreement for hours and night-shift policies."""

import unittest

from ortools.sat.python import cp_model

from roster_audit.individual_staff_constraints import (
    StaffSchedule, audit_consecutive_night_shifts, audit_four_week_hours,
    audit_night_shift_sequence, audit_no_after_night_shift,
)
from roster_audit.optimizer import _add_hours_constraint, _add_night_shift_constraints


def fixed_model(shifts):
    model = cp_model.CpModel()
    variables = {}
    for day, code in enumerate(shifts, 1):
        variable = model.new_bool_var(f"day_{day}_{code}")
        model.add(variable == 1)
        variables[1, day, code] = variable
    return model, variables


def feasible(model):
    return cp_model.CpSolver().solve(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)


class IndividualPolicyParityTests(unittest.TestCase):
    def assert_hours(self, shifts, expected):
        schedule = StaffSchedule(6, tuple(shifts))
        model, variables = fixed_model(schedule.shifts)
        _add_hours_constraint(model, variables, 1, set(shifts))
        self.assertEqual(not audit_four_week_hours(schedule), expected, "audit")
        self.assertEqual(feasible(model), expected, "solver")

    def assert_nights(self, entries, expected):
        shifts = tuple(entries.get(day, "OFF") for day in range(1, 29))
        schedule = StaffSchedule(6, shifts)
        model, variables = fixed_model(shifts)

        def shift(staff, day, accepted):
            return sum(variables[staff, day, code] for code in accepted
                       if (staff, day, code) in variables)

        _add_night_shift_constraints(model, shift, 1)
        failures = (audit_no_after_night_shift(schedule)
                    + audit_night_shift_sequence(schedule)
                    + audit_consecutive_night_shifts(schedule))
        self.assertEqual(not failures, expected, "audit")
        self.assertEqual(feasible(model), expected, "solver")

    def test_four_week_hours_at_and_around_target(self):
        self.assert_hours(["XE1"] * 20 + ["OFF"] * 8, True)
        self.assert_hours(["XE1"] * 19 + ["OFF"] * 9, False)
        self.assert_hours(["XE1"] * 21 + ["OFF"] * 7, False)
        self.assert_hours(["D", "P"] + ["XE1"] * 17 + ["RD"] * 9, True)
        self.assert_hours(["XE"] * 2 + ["XE1"] * 19 + ["VLRD"] * 7, True)

    def test_nights_followed_by_nights_or_each_no_variant(self):
        for night in ("D", "P", "W"):
            for no in ("NO", "NO+", "NO++"):
                with self.subTest(night=night, no=no):
                    self.assert_nights({5: night, 6: no}, True)
        self.assert_nights({5: "P", 6: "W", 7: "NO"}, True)
        self.assert_nights({5: "P", 6: "OFF"}, False)
        self.assert_nights({5: "OFF", 6: "NO"}, False)

    def test_consecutive_nights_across_week_boundary(self):
        self.assert_nights({7: "P", 8: "W", 9: "NO"}, True)
        self.assert_nights({6: "P", 7: "W", 8: "D", 9: "NO"}, False)

    def test_roster_edges_do_not_require_adjacent_roster_data(self):
        self.assert_nights({1: "NO", 28: "D"}, True)
        self.assert_nights({1: "NO+", 27: "P", 28: "W"}, True)
        self.assert_nights({26: "D", 27: "P", 28: "W"}, False)


if __name__ == "__main__":
    unittest.main()
