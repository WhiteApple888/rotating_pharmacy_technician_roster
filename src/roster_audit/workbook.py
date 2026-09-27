"""Excel workbook input for the fixed roster layout."""

from pathlib import Path

from openpyxl import load_workbook

from .individual_staff_constraints import Roster, STAFF_ROWS, StaffSchedule
from .parsing import day_columns, normalise


def load_roster(path: Path, sheet_name: str | None) -> Roster:
    """Read the fixed 16-by-28 grid into the domain model."""
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook[sheet_name] if sheet_name else workbook.active
        columns = day_columns()
        staff = tuple(
            StaffSchedule(row, tuple(normalise(sheet.cell(row=row, column=column).value) for column in columns))
            for row in STAFF_ROWS
        )
        return Roster(worksheet=sheet.title, staff=staff)
    except KeyError as exc:
        raise ValueError(f"Worksheet '{sheet_name}' does not exist.") from exc
    finally:
        workbook.close()
