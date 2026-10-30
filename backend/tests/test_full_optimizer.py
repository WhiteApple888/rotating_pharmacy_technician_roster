"""End-to-end checks for repairing the uploaded roster without a pattern."""

from datetime import date
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from ortools.sat.python import cp_model

from openpyxl import load_workbook

from roster_audit.individual_staff_constraints import DPW_CODES
from roster_audit.optimizer import (
    NoFeasibleRosterError, _change_cost, _count_changes, _marker,
    optimize_full_roster,
)
from roster_audit.repair_workbook import PRIORITY_COLUMNS, _load_priorities, write_repaired_roster
from roster_audit.service import audit_loaded_roster
from roster_audit.workbook import load_last_roster_rest_days, load_roster


SOURCE = Path(__file__).resolve().parents[2] / "sample" / "13Apr-10May_26.xlsx"
SHEET = "13Aprto10May"
START = date(2026, 4, 13)


def workbook_with_changes(changes: dict[str, str]) -> bytes:
    workbook = load_workbook(SOURCE)
    for cell, value in changes.items():
        workbook[SHEET][cell] = value
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def full_roster_with_leave() -> bytes:
    return workbook_with_changes({"Z6": "VL"})  # Staff 1, Day 15.


def full_roster_with_rest_day_leave() -> bytes:
    return workbook_with_changes({"AC6": "VL"})  # Staff 1, Day 18.


class FullOptimizerTests(unittest.TestCase):
    def optimize(self, contents):
        return optimize_full_roster(
            contents, start_date=START, public_holiday_days={19},
            worksheet_name=SHEET, max_time_seconds=30,
        )

    def assert_audited_export(self, result):
        exported = load_roster(BytesIO(result.workbook_bytes), SHEET)
        prior = load_last_roster_rest_days(BytesIO(result.workbook_bytes), START)
        self.assertEqual(exported, result.roster)
        self.assertEqual(audit_loaded_roster(exported, {19}, START, prior.dates), [])

    def test_change_log_records_marker_and_base_changes(self):
        from roster_audit.individual_staff_constraints import Roster, StaffSchedule

        contents = workbook_with_changes({"D6": "OFF", "E6": "RD+", "F6": "NO+",
                                          "G6": "OFF+", "H6": "VL"})
        workbook = load_workbook(BytesIO(contents))
        workbook.create_sheet("Change Log")["A1"] = "obsolete"
        source = BytesIO()
        workbook.save(source)
        workbook.close()
        original = load_roster(BytesIO(source.getvalue()), SHEET)
        first = original.staff[0]
        updated = StaffSchedule(first.excel_row, ("OFF+", "RD", "NO++", "NO++", "VLRD") + first.shifts[5:])
        final = Roster(SHEET, (updated,) + original.staff[1:])
        self.assertEqual(_count_changes(original, final), (1, 5, 4))
        output = write_repaired_roster(source.getvalue(), SHEET, original, final, START, 1, 5, 4)
        workbook = load_workbook(BytesIO(output), data_only=True)
        log = workbook["Change Log"]
        self.assertEqual([log.cell(i, 2).value for i in range(1, 4)], [1, 5, 4])
        rows = list(log.iter_rows(min_row=6, values_only=True))
        self.assertEqual(len(rows), 5)
        self.assertEqual([(r[4], r[5], r[6], r[7], r[8]) for r in rows], [
            ("OFF", "OFF+", False, True, False),
            ("RD+", "RD", False, True, False),
            ("NO+", "NO++", False, True, False),
            ("OFF+", "NO++", True, True, True),
            ("VL", "VLRD", True, False, False),
        ])
        self.assertEqual((rows[0][0], rows[0][1], rows[0][2].date(), rows[0][3]),
                         (6, "D", START, workbook[SHEET]["A6"].value))
        workbook.close()

    def test_export_is_audited_after_serialization(self):
        contents = SOURCE.read_bytes()
        roster = load_roster(BytesIO(contents), SHEET)
        with patch("roster_audit.optimizer._solve_roster", return_value=(roster, cp_model.OPTIMAL)), \
             patch("roster_audit.optimizer.audit_loaded_roster", side_effect=[[], [object()]]) as audit:
            with self.assertRaisesRegex(NoFeasibleRosterError, "exported workbook did not pass"):
                self.optimize(contents)
        self.assertEqual(audit.call_count, 2)
        self.assertEqual(audit.call_args_list[1].args[0], roster)
        self.assertIsNot(audit.call_args_list[1].args[0], roster)

    def test_sample_priority_columns_follow_the_same_staff_rows(self):
        priorities = _load_priorities(SOURCE.read_bytes(), SHEET)
        self.assertEqual([next(staff for staff, rank in week.items() if rank == 1)
                          for week in priorities], [8, 7, 6, 5])

    def test_coverage_gap_can_be_repaired_without_reconstructing_a_leave_duty(self):
        result = self.optimize(workbook_with_changes({"Z6": "Z1"}))
        self.assertEqual(sum(staff.shifts[14] in DPW_CODES for staff in result.roster.staff), 4)
        self.assert_audited_export(result)

    def test_two_night_leave_cells_remain_leave_with_daily_coverage_restored(self):
        result = self.optimize(workbook_with_changes({"AD10": "VL", "AD16": "VL"}))
        for staff in (5, 11):
            self.assertIn(result.roster.staff[staff - 1].shifts[18], {"VL", "VLOFF", "VLRD"})
        self.assertEqual(sum(staff.shifts[18] in DPW_CODES for staff in result.roster.staff), 3)
        self.assert_audited_export(result)

    def test_no_xlsx_is_returned_when_leave_exceeds_daily_limit(self):
        with self.assertRaises(NoFeasibleRosterError):
            self.optimize(workbook_with_changes({"D8": "VL"}))

    def test_rest_day_leave_and_free_conversions_have_zero_penalized_changes(self):
        contents = full_roster_with_rest_day_leave()
        result = self.optimize(contents)
        original = load_roster(BytesIO(contents), SHEET)
        self.assertEqual(result.penalized_change_count, 0)
        self.assertGreater(result.cell_edit_count, 0)
        self.assertEqual(result.roster.staff[-1], original.staff[-1])
        self.assert_audited_export(result)

    def test_priorities_are_optional_and_need_not_align_with_a_pattern(self):
        workbook = load_workbook(BytesIO(full_roster_with_rest_day_leave()))
        for row in range(6, 22):
            for column in PRIORITY_COLUMNS:
                workbook[SHEET].cell(row, column).value = None
        output = BytesIO()
        workbook.save(output)
        workbook.close()
        result = self.optimize(output.getvalue())
        self.assertEqual(result.penalized_change_count, 0)
        self.assert_audited_export(result)

    def test_holiday_shortage_is_repaired_from_uploaded_coverage(self):
        result = self.optimize(workbook_with_changes({"AD11": "VL"}))
        self.assertEqual(sum(staff.shifts[18] in {"XE", "XE1"} for staff in result.roster.staff), 2)
        self.assert_audited_export(result)

    def test_export_counts_use_uploaded_roster_and_exclude_free_conversions(self):
        contents = full_roster_with_leave()
        original = load_roster(BytesIO(contents), SHEET)
        result = self.optimize(contents)
        pairs = [(before, after) for old, new in zip(original.staff, result.roster.staff)
                 for before, after in zip(old.shifts, new.shifts)]
        self.assertEqual(result.penalized_change_count, sum(_change_cost(old, new) for old, new in pairs))
        self.assertEqual(result.cell_edit_count, sum(old != new for old, new in pairs))
        self.assertEqual(result.plus_change_count, sum(_marker(old) != _marker(new) for old, new in pairs))
        self.assertGreater(result.penalized_change_count, 0)
        # Priority 1 is used for the new night duty despite alternative covers
        # potentially requiring fewer paid edits elsewhere in the roster.
        self.assertEqual([
            staff for staff, (old, new) in enumerate(zip(original.staff, result.roster.staff), 1)
            if old.shifts[14] not in DPW_CODES and new.shifts[14] in DPW_CODES
        ], [6])
        self.assertIn(result.roster.staff[0].shifts[14], {"VL", "VLOFF", "VLRD"})
        uploaded = load_workbook(BytesIO(contents), read_only=True)
        self.assertEqual(uploaded[SHEET]["Z6"].value, "VL")
        uploaded.close()
        self.assert_audited_export(result)


if __name__ == "__main__":
    unittest.main()

