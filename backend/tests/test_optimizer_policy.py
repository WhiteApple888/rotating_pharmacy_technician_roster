"""Change-cost equivalence groups and constrained marker preferences."""

import unittest

from ortools.sat.python import cp_model

from roster_audit.optimization_policy import (
    allowed_shift_codes, is_new_duty_cover, prohibits_unscored_day_cover,
    valid_takeover_priority,
)
from roster_audit.optimizer import (
    DAYS, STAFF_COUNT, _change_cost, _first_stage_cost, _lost_dpw_cost, _marker_cost, _new_d_cost,
)


class OptimizerPolicyTests(unittest.TestCase):
    def test_priority_scores_are_unique_in_range_and_exclude_fixed_staff(self):
        for value in (1, 6):
            self.assertTrue(valid_takeover_priority(value, 1, set()))
        for value in (0, 7, True, 1.0, "1", None):
            with self.subTest(value=value):
                self.assertFalse(valid_takeover_priority(value, 1, set()))
        self.assertFalse(valid_takeover_priority(1, 1, {1}))
        self.assertFalse(valid_takeover_priority(1, STAFF_COUNT, set(), frozenset({STAFF_COUNT})))

    def test_repair_choices_preserve_leave_protected_codes_and_fixed_staff(self):
        for leave in ("VL", "VLOFF", "VLRD"):
            with self.subTest(leave=leave):
                self.assertEqual(set(allowed_shift_codes(leave, 1)), {"VL", "VLOFF", "VLRD"})
        for protected in ("VLPH", "VL(TO4H)", "OC"):
            with self.subTest(protected=protected):
                self.assertEqual(allowed_shift_codes(protected, 1), (protected,))
        self.assertEqual(allowed_shift_codes("RD+", STAFF_COUNT, frozenset({STAFF_COUNT})), ("RD+",))
        for original in ("OFF", "PH", "XO"):
            with self.subTest(original=original):
                choices = set(allowed_shift_codes(original, 1))
                self.assertIn(original, choices)
                self.assertFalse(({"VL", "OC", "PH", "XO"} - {original}) & choices)
                self.assertIn("Z1", choices)
                self.assertIn("Z4", choices)

    def test_priority_applies_only_to_new_duty_cover(self):
        for original, proposed, expected in (
            ("OFF", "P", True), ("D", "P", False), ("VL", "D", True),
            ("RD+", "Z1", True), ("NO++", "XE", True), ("Z", "Y", False),
            ("VL", "Z1", False), ("OFF", "RD", False), ("OFF", "Z4", True),
        ):
            with self.subTest(original=original, proposed=proposed):
                self.assertEqual(is_new_duty_cover(original, proposed), expected)

    def test_unscored_no_cannot_cover_day_duty(self):
        for original in ("NO", "NO+", "NO++"):
            with self.subTest(original=original):
                self.assertTrue(prohibits_unscored_day_cover(original, "Z1", None))
                self.assertTrue(prohibits_unscored_day_cover(original, "Z4", None))
                self.assertFalse(prohibits_unscored_day_cover(original, "Z1", 1))
                self.assertFalse(prohibits_unscored_day_cover(original, "P", None))
        self.assertFalse(prohibits_unscored_day_cover("OFF", "Z1", None))

    def solve_night_choice(self, original, *, fallback=None, priority=None, force=None,
                           return_cost=False):
        model = cp_model.CpModel()
        x = {(1, 1, code): model.new_bool_var(code) for code in ("D", "P", "W")}
        model.add_exactly_one(x.values())
        if force:
            model.add(x[1, 1, force] == 1)
        fallback = fallback or {}
        priority = priority or {}
        model.minimize(_first_stage_cost(
            _lost_dpw_cost(x, ((original,),)),
            0,
            sum(fallback.get(code, 0) * var for (_, _, code), var in x.items()),
            sum(priority.get(code, 0) * var for (_, _, code), var in x.items()),
            _new_d_cost(x, ((original,),)),
            sum(_change_cost(original, code) * var for (_, _, code), var in x.items()),
        ))
        solver = cp_model.CpSolver()
        self.assertEqual(solver.solve(model), cp_model.OPTIMAL)
        selected = next(code for (_, _, code), var in x.items() if solver.boolean_value(var))
        return (selected, solver.objective_value) if return_cost else selected

    def test_new_night_prefers_either_p_or_w_to_d(self):
        selected, optimum = self.solve_night_choice("OFF", return_cost=True)
        self.assertIn(selected, {"P", "W"})
        # Each alternative remains optimal when forced: neither is preferred.
        for code in ("P", "W"):
            self.assertEqual(self.solve_night_choice("OFF", force=code, return_cost=True),
                             (code, optimum))

    def test_new_d_cost_depends_on_original_shift(self):
        for original, expected in (("D", 0), ("W", 1), ("P", 1), ("OFF", 1)):
            with self.subTest(original=original):
                model = cp_model.CpModel()
                d = model.new_bool_var("D")
                model.add(d == 1)
                solver = cp_model.CpSolver()
                self.assertEqual(solver.solve(model), cp_model.OPTIMAL)
                self.assertEqual(
                    solver.value(_new_d_cost({(1, 1, "D"): d}, ((original,),))),
                    expected,
                )
        self.assertEqual(self.solve_night_choice("D"), "D")

    def test_new_d_outweighs_fallback_and_priority_costs(self):
        self.assertIn(self.solve_night_choice("OFF", fallback={"P": 1, "W": 1}), {"P", "W"})
        self.assertIn(self.solve_night_choice("OFF", priority={"D": 1, "P": 2, "W": 2}), {"P", "W"})
        self.assertIn(self.solve_night_choice("P", fallback={"P": 1, "W": 1}), {"P", "W"})

    def test_hard_constraint_can_require_new_d(self):
        self.assertEqual(self.solve_night_choice("OFF", force="D"), "D")

    def test_weights_cover_full_roster(self):
        cells = STAFF_COUNT * DAYS
        cost = _first_stage_cost
        self.assertGreater(cost(1, 0, 0, 0, 0, 0), cost(0, cells, cells, 6 * cells, cells, cells))
        self.assertGreater(cost(0, 1, 0, 0, 0, 0), cost(0, 0, cells, 6 * cells, cells, cells))
        self.assertGreater(cost(0, 0, 0, 0, 1, 0), cost(0, 0, cells, 6 * cells, 0, cells))
        self.assertGreater(cost(0, 0, 1, 0, 0, 0), cost(0, 0, 0, 6 * cells, 0, cells))
        self.assertGreater(cost(0, 0, 0, 1, 0, 0), cost(0, 0, 0, 0, 0, cells))

    def test_objective_is_valid_at_maximum_staff_count(self):
        model = cp_model.CpModel()
        cells = 30 * DAYS
        counts = [model.new_int_var(0, bound, name) for name, bound in (
            ("lost", cells), ("z4", cells), ("fallback", cells),
            ("priority", 6 * cells), ("new_d", cells), ("changes", cells),
        )]
        model.minimize(_first_stage_cost(*counts, staff_count=30))
        self.assertEqual(model.validate(), "")

    def test_solver_uses_z4_only_when_required(self):
        for required, expected in ((False, 0), (True, 1)):
            with self.subTest(required=required):
                model = cp_model.CpModel()
                z4 = model.new_bool_var("z4")
                alternative = model.new_bool_var("alternative")
                model.add_exactly_one(z4, alternative)
                if required:
                    model.add(z4 == 1)
                model.minimize(_first_stage_cost(0, z4, alternative, 6 * alternative, alternative, 0))
                solver = cp_model.CpSolver()
                self.assertEqual(solver.solve(model), cp_model.OPTIMAL)
                self.assertEqual(solver.value(z4), expected)

    def test_preserving_night_shift_takes_precedence_over_z4(self):
        model = cp_model.CpModel()
        x = {(1, 1, code): model.new_bool_var(code) for code in ("P", "W", "Z1")}
        model.add_exactly_one(x.values())
        z4 = model.new_bool_var("z4_elsewhere")
        model.add(z4 + x[1, 1, "Z1"] == 1)
        model.minimize(_first_stage_cost(_lost_dpw_cost(x, (("P",),)), z4, 0, 0, 0, 0))
        solver = cp_model.CpSolver()
        self.assertEqual(solver.solve(model), cp_model.OPTIMAL)
        self.assertEqual(solver.value(z4), 1)
        self.assertEqual(solver.value(x[1, 1, "Z1"]), 0)
        self.assertEqual(solver.value(_lost_dpw_cost(x, (("P",),))), 0)

    def test_lost_dpw_counts_only_night_to_non_night(self):
        for original in ("D", "P", "W", "OFF"):
            for proposed in ("D", "P", "W", "Z1", "Z4", "NO"):
                with self.subTest(original=original, proposed=proposed):
                    model = cp_model.CpModel()
                    selected = model.new_bool_var("selected")
                    model.add(selected == 1)
                    solver = cp_model.CpSolver()
                    self.assertEqual(solver.solve(model), cp_model.OPTIMAL)
                    self.assertEqual(solver.value(_lost_dpw_cost({(1, 1, proposed): selected}, ((original,),))),
                                     int(original in {"D", "P", "W"} and proposed not in {"D", "P", "W"}))

    def test_allowed_groups_and_all_marker_variants_are_free(self):
        groups = (
            ("VL", "VLOFF", "VLRD"),
            ("OFF", "OFF+", "OFF++", "RD", "RD+", "RD++"),
            ("NO", "NO+", "NO++"),
            ("Z", "Y", "Z1"),
        )
        for group in groups:
            for original in group:
                for proposed in group:
                    with self.subTest(original=original, proposed=proposed):
                        self.assertEqual(_change_cost(original, proposed), 0)

    def test_other_shift_changes_still_cost_one(self):
        for original, proposed in (("OFF+", "Z1"), ("RD++", "NO+"),
                                   ("D", "P"), ("XE", "XE1"), ("W", "OFF")):
            with self.subTest(original=original, proposed=proposed):
                self.assertEqual(_change_cost(original, proposed), 1)
                self.assertEqual(_change_cost(proposed, original), 1)

    def solve_markers(self, bases, *, priorities=None, protect_rd=False):
        model = cp_model.CpModel()
        x = {}
        for staff, base in enumerate(bases, 1):
            for suffix in ("", "+", "++"):
                x[staff, 1, base + suffix] = model.new_bool_var(f"{staff}_{suffix}")
            model.add_exactly_one(x[staff, 1, base + suffix] for suffix in ("", "+", "++"))
            if protect_rd and base == "RD":
                # An RD at the spacing limit must remain unmarked.
                model.add(x[staff, 1, "RD"] == 1)
        for suffix in ("+", "++"):
            model.add(sum(x[staff, 1, base + suffix] for staff, base in enumerate(bases, 1)) == 1)
        model.minimize(_marker_cost(x, (priorities or {},)))
        solver = cp_model.CpSolver()
        self.assertEqual(solver.solve(model), cp_model.OPTIMAL)
        return {staff: code for (staff, _, code), variable in x.items()
                if solver.boolean_value(variable)}

    def test_both_markers_prefer_off_over_rd_and_no(self) -> None:
        selected = self.solve_markers(("OFF", "OFF", "RD", "NO")).values()
        self.assertCountEqual(selected, ["OFF+", "OFF++", "RD", "NO"])

    def test_rd_is_preferred_to_no_when_off_is_insufficient(self) -> None:
        selected = self.solve_markers(("OFF", "RD", "NO")).values()
        self.assertIn("NO", selected)
        self.assertNotIn("OFF", selected)
        self.assertNotIn("RD", selected)

    def test_individual_rd_constraint_allows_no_marker(self) -> None:
        selected = self.solve_markers(("OFF", "RD", "NO"), protect_rd=True).values()
        self.assertIn("RD", selected)
        self.assertNotIn("OFF", selected)
        self.assertNotIn("NO", selected)

    def test_first_on_call_gets_better_base_even_without_priority(self):
        selected = self.solve_markers(("OFF", "RD", "NO"), priorities={2: 1, 3: 2})
        self.assertEqual(selected[1], "OFF+")
        self.assertEqual(selected[2], "RD++")

    def test_scores_break_ties_for_each_role(self):
        selected = self.solve_markers(("OFF", "OFF", "OFF"), priorities={1: 5, 2: 1})
        self.assertEqual(selected, {1: "OFF++", 2: "OFF+", 3: "OFF"})

    def test_second_on_call_prefers_base_to_priority(self):
        selected = self.solve_markers(("OFF", "OFF", "RD"), priorities={1: 1, 3: 2})
        self.assertEqual(selected, {1: "OFF+", 2: "OFF++", 3: "RD"})


if __name__ == "__main__":
    unittest.main()
