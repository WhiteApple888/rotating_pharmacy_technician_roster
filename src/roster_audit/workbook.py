"""Excel workbook input for the fixed roster layout and RD history sheet."""

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

from .individual_staff_constraints import Roster, STAFF_ROWS, StaffSchedule
from .parsing import day_columns, normalise


LAST_ROSTER_RD_SHEET = "lastRosterRD"
LAST_ROSTER_RD_COLUMN = 2  # Excel column B
LAST_ROSTER_RD_ROWS = range(2, 18)


@dataclass(frozen=True)
class LastRosterRestDays:
    """The 16 prior-RD values, in the same order as ``STAFF_ROWS``."""

    dates: tuple[date, ...]

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


def load_last_roster_rest_days(path: Path, start_date: date) -> LastRosterRestDays:
    """Read and validate ``lastRosterRD!B2:B17`` for the active roster.

    The sheet must contain one Excel date per staff member.  The baseline is
    the date must be before Day 1.
    """
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        try:
            sheet = workbook[LAST_ROSTER_RD_SHEET]
        except KeyError as exc:
            raise ValueError(
                f"Worksheet '{LAST_ROSTER_RD_SHEET}' is required for the baseline RD check."
            ) from exc

        dates: list[date] = []
        for row in LAST_ROSTER_RD_ROWS:
            cell = sheet.cell(row=row, column=LAST_ROSTER_RD_COLUMN)
            value = cell.value
            if isinstance(value, (int, float)):
                value = from_excel(value, workbook.epoch)

            if isinstance(value, datetime):
                value = value.date()

            if not isinstance(value, date):
                raise ValueError(
                    f"{LAST_ROSTER_RD_SHEET}!{cell.coordinate} must contain an Excel date; "
                    f"received {value!r}."
                )

            if value >= start_date:
                raise ValueError(
                    f"{LAST_ROSTER_RD_SHEET}!{cell.coordinate} must be before roster Day 1 "
                    f"({start_date.isoformat()}); received {value.isoformat()}."
                )

            dates.append(value)

        return LastRosterRestDays(tuple(dates))
    finally:
        workbook.close()
