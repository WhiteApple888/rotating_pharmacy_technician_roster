"""Read and write the Excel representation of a roster repair."""

from datetime import date, timedelta
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from .individual_policy import SHIFT_HOURS
from .individual_staff_constraints import Roster
from .optimization_policy import STAFF_COUNT, _change_cost, _marker, valid_takeover_priority
from .parsing import day_columns
from .workbook import CURRENT_ROSTER_START_ROW, load_last_roster_rest_days, load_roster

PRIORITY_COLUMNS = (3, 14, 25, 36)
WEEKLY_HOURS_COLUMNS = (11, 22, 33, 44)


def load_repair_input(workbook_bytes: bytes, start_date: date, worksheet_name: str | None):
    """Read the roster, previous rest days, and weekly takeover priorities."""
    if worksheet_name is None:
        workbook = load_workbook(BytesIO(workbook_bytes), read_only=True)
        try:
            worksheet_name = next(
                (name for name in workbook.sheetnames if name not in {"lastRosterRD", "Change Log"}), None,
            )
        finally:
            workbook.close()
        if worksheet_name is None:
            raise ValueError("Workbook has no roster worksheet.")
    roster = load_roster(BytesIO(workbook_bytes), worksheet_name, num_staff=STAFF_COUNT)
    if roster.worksheet == "lastRosterRD":
        raise ValueError("Select the roster worksheet, not lastRosterRD' worksheet.")
    prior = load_last_roster_rest_days(
        BytesIO(workbook_bytes), start_date, num_staff=STAFF_COUNT,
    ).dates
    return roster, prior, _load_priorities(workbook_bytes, roster.worksheet)


def load_exported_roster(workbook_bytes: bytes, sheet_name: str) -> Roster:
    """Read the serialized export afresh for independent verification."""
    return load_roster(BytesIO(workbook_bytes), sheet_name, num_staff=STAFF_COUNT)


def _load_priorities(workbook_bytes: bytes, sheet_name: str) -> tuple[dict[int, int], ...]:
    workbook = load_workbook(BytesIO(workbook_bytes), read_only=True, data_only=True)
    try:
        sheet = workbook[sheet_name]
        weeks = []
        for week, column in enumerate(PRIORITY_COLUMNS, start=1):
            ranks: dict[int, int] = {}
            used: set[int] = set()
            for staff in range(1, STAFF_COUNT + 1):
                value = sheet.cell(staff + CURRENT_ROSTER_START_ROW - 1, column).value
                if value is None or value == "":
                    continue
                if not valid_takeover_priority(value, staff, used):
                    raise ValueError(f"Week {week} has an invalid takeover priority at row {staff + CURRENT_ROSTER_START_ROW - 1}.")
                ranks[staff] = value
                used.add(value)
            weeks.append(ranks)
        return tuple(weeks)
    finally:
        workbook.close()


def write_repaired_roster(workbook_bytes: bytes, sheet_name: str, original: Roster,
                  roster: Roster, start_date: date, penalized_changes: int,
                  cell_edits: int, plus_changes: int) -> bytes:
    workbook = load_workbook(BytesIO(workbook_bytes))
    try:
        sheet = workbook[sheet_name]
        columns = day_columns()
        for schedule in roster.staff:
            for column, code in zip(columns, schedule.shifts):
                sheet.cell(schedule.excel_row, column).value = code
            for week, column in enumerate(WEEKLY_HOURS_COLUMNS):
                hours_cell = sheet.cell(schedule.excel_row, column)
                # Preserve formulas and intentionally blank cells. The source
                # workbook uses numeric snapshots for the first 15 staff.
                if isinstance(hours_cell.value, (int, float)) and not isinstance(
                    hours_cell.value, bool
                ):
                    hours_cell.value = sum(
                        SHIFT_HOURS[code]
                        for code in schedule.shifts[week * 7:(week + 1) * 7]
                    )
        if "Change Log" in workbook:
            del workbook["Change Log"]
        log = workbook.create_sheet("Change Log")
        for label, value in (("Penalized change count", penalized_changes),
                             ("Cell edit count", cell_edits),
                             ("Plus change count", plus_changes)):
            log.append([label, value])
        log.append([])
        log.append(["Excel row", "Column", "Date", "Staff name", "Before", "After",
                    "Base shift changed", "Plus marker changed", "Penalized cost changed"])
        for before, after in zip(original.staff, roster.staff):
            for day, (old, new) in enumerate(zip(before.shifts, after.shifts)):
                if old == new:
                    continue
                log.append([before.excel_row, get_column_letter(columns[day]),
                            start_date + timedelta(days=day),
                            sheet.cell(before.excel_row, 1).value, old, new,
                            old.rstrip("+") != new.rstrip("+"),
                            _marker(old) != _marker(new), bool(_change_cost(old, new))])
                log.cell(log.max_row, 3).number_format = "yyyy-mm-dd"
        for cell in log[5]:
            cell.font = Font(bold=True)
        log.freeze_panes = "A6"
        log.auto_filter.ref = f"A5:I{max(5, log.max_row)}"
        for column, width in enumerate((12, 10, 14, 22, 14, 14, 20, 21, 24), 1):
            log.column_dimensions[get_column_letter(column)].width = width
        output = BytesIO()
        workbook.save(output)
        return output.getvalue()
    finally:
        workbook.close()
