"""Audit and solver agree on daily coverage for normal and public holidays."""

import unittest

from ortools.sat.python import cp_model

from roster_audit.daily_constraints import audit_daily_rules
from roster_audit.daily_policy import coverage_rules_for_day
from roster_audit.individual_staff_constraints import Roster, StaffSchedule
from roster_audit.optimizer import _add_daily_coverage_constraints


class DailyPolicyParityTests(unittest.TestCase):
    def test_weekday_and_holiday_policy_selection(self):
        for day, weekday in enumerate(("Monday", "Tuesday", "Wednesday", "Thursday",
                                       "Friday", "Saturday", "Sunday"), 1):
            for holidays in (set(), {day}):
                with self.subTest(day=day, holiday=bool(holidays)):
                    rules = coverage_rules_for_day(day, holidays)
                    self.assertTrue(rules)
                    self.assertTrue(all(weekday in rule.weekdays for rule in rules))
                    night = [rule for rule in rules if rule.label == "D/P/W"]
                    self.assertEqual([rule.target for rule in night], [4 if day <= 2 else 3])
                    if holidays:
                        z_rule = next(rule for rule in rules if rule.label == "Z1/Y/Z")
                        self.assertEqual(z_rule.target, 5 if day in (5, 6) else 4)
                        self.assertTrue(any(rule.label == "XE/XE1" for rule in rules))

    def assert_coverage(self, day, day_shifts, public_holidays, expected):
        shifts = tuple(day_shifts) + ("OFF",) * (16 - len(day_shifts))
        schedules = []
        model = cp_model.CpModel()
        variables = {}
        for staff, code in enumerate(shifts, 1):
            schedule = ["OFF"] * 28
            schedule[day - 1] = code
            schedules.append(StaffSchedule(staff + 5, tuple(schedule)))
            variable = model.new_bool_var(f"staff_{staff}")
            model.add(variable == 1)
            variables[staff, day, code] = variable

        def shift(staff, roster_day, accepted):
            return sum(variables[staff, roster_day, code] for code in accepted
                       if (staff, roster_day, code) in variables)

        _add_daily_coverage_constraints(model, shift, day, public_holidays, len(shifts))
        failures = audit_daily_rules(Roster("Roster", tuple(schedules)), public_holidays)
        audit_passes = not any(failure.day == day for failure in failures)
        solver_passes = cp_model.CpSolver().solve(model) in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        self.assertEqual(audit_passes, expected, "audit")
        self.assertEqual(solver_passes, expected, "solver")

    def test_normal_monday_targets_and_boundaries(self):
        monday = ["D", "D", "P", "W", "Z1", "Z1", "Z1", "Z1", "OFF+", "OFF++"]
        self.assert_coverage(1, monday, set(), True)
        self.assert_coverage(8, monday, set(), True)  # Weekday selection repeats.
        self.assert_coverage(1, monday[:7] + monday[8:], set(), False)  # Too few Z1/D.
        self.assert_coverage(1, monday + ["RD+"], set(), False)  # Two single-plus markers.
        self.assert_coverage(1, monday + ["VL", "OC"], set(), True)
        self.assert_coverage(1, monday + ["VL", "OC", "VLRD"], set(), False)

    def test_weekend_coverage(self):
        saturday = ["D", "P", "W", "Z1", "Z1", "Z1", "Z1", "Z", "Y", "OFF+", "OFF++"]
        sunday = ["D", "P", "W", "Z1", "Z1", "Y", "Y", "XE", "XE1", "OFF+", "OFF++"]
        self.assert_coverage(6, saturday, set(), True)
        self.assert_coverage(6, saturday + ["Z"], set(), False)
        self.assert_coverage(7, sunday, set(), True)
        self.assert_coverage(7, sunday + ["Y"], set(), False)

    def test_public_holiday_rules_replace_normal_rules(self):
        monday_holiday = ["D", "D", "P", "W", "Z1", "Z1", "Z", "Y", "XE", "XE1", "OFF+", "OFF++"]
        self.assert_coverage(1, monday_holiday, {1}, True)
        self.assert_coverage(1, monday_holiday, set(), False)
        self.assert_coverage(1, monday_holiday[:9] + monday_holiday[10:], {1}, False)

        friday_holiday = ["D", "P", "W", "Z1", "Z1", "Z1", "Z", "Y", "XE", "XE1", "OFF+", "OFF++"]
        self.assert_coverage(5, friday_holiday, {5}, True)
        self.assert_coverage(5, friday_holiday[:7] + friday_holiday[8:], {5}, False)


if __name__ == "__main__":
    unittest.main()
