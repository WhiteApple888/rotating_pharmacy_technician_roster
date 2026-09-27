"""Input normalisation and roster calendar helpers."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from openpyxl.utils import column_index_from_string


WEEK_COLUMNS = (("D", "J"), ("O", "U"), ("Z", "AF"), ("AK", "AQ"))


def normalise(value: object) -> str:
    """Convert a worksheet value into a case- and whitespace-insensitive code."""
    return "" if value is None else "".join(str(value).split()).upper()


def day_columns() -> list[int]:
    """Return the 28 source Excel column indexes in Day 1--28 order."""
    return [column for first, last in WEEK_COLUMNS for column in range(
        column_index_from_string(first), column_index_from_string(last) + 1
    )]


def parse_ph_days(values: Iterable[str], start_date: date | None) -> set[int]:
    """Convert roster-day numbers and/or ISO dates to roster day numbers."""
    days: set[int] = set()
    for supplied in values:
        for token in supplied.split(","):
            token = token.strip()
            if not token:
                continue
            if token.isdigit():
                day = int(token)
            else:
                if start_date is None:
                    raise ValueError(f"PH date '{token}' needs --start-date YYYY-MM-DD.")
                try:
                    day = (date.fromisoformat(token) - start_date).days + 1
                except ValueError as exc:
                    raise ValueError(f"Invalid PH value '{token}'. Use 1-28 or YYYY-MM-DD.") from exc
            if not 1 <= day <= 28:
                raise ValueError(f"PH day {day} is outside the 28-day roster.")
            days.add(day)
    return days
