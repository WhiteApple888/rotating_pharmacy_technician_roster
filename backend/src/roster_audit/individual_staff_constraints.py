"""Roster domain types and constraints that apply to one staff member."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

TOTAL_NUMBER_OF_STAFF = 16
MAX_REST_DAY_GAP = 12


SHIFT_HOURS: dict[str, int] = {
    "XE1": 8, "XO": 8, "Z1": 8, "Z": 8, "Y": 8, "PH": 8, "VL": 8, "OC": 8,
    "D": 12, "P": 12, "W": 10, "XE": 4, "VL(TO4H)": 4,
    "RD": 0, "RD+": 0, "RD++": 0, "VLRD": 0, "VLOFF": 0, "VLPH": 0,
    "OFF": 0, "OFF+": 0, "OFF++": 0, "NO": 0, "NO+": 0, "NO++": 0,
}

REST_DAY_CODES = frozenset({"RD", "RD+", "RD++", "VLRD"})
REST_DAY_NO_PLUS_CODES = frozenset({"RD", "VLRD"})
DPW_CODES = frozenset({"D", "P", "W"})
NO_CODES = frozenset({"NO", "NO+", "NO++"})


@dataclass(frozen=True)
class StaffSchedule:
    """The 28 cleaned shift codes belonging to one source worksheet row."""

    excel_row: int
    shifts: tuple[str, ...]


@dataclass(frozen=True)
class Roster:
    """The roster grid after it has been read from Excel."""

    worksheet: str
    staff: tuple[StaffSchedule, ...]


@dataclass(frozen=True)
class AuditFailure:
    """A typed audit result that can be printed and exported consistently."""

    category: str
    message: str
    staff_row: int | None = None
    day: int | None = None
    source_cell: str | None = None
    roster_date: date | None = None


def audit_four_week_hours(schedule: StaffSchedule) -> list[AuditFailure]:
    """Require exactly 160 working hours for one staff member."""
    total_hours = sum(SHIFT_HOURS.get(shift, 0) for shift in schedule.shifts)
    if total_hours == 160:
        return []
    return [AuditFailure(
        category="Four-week working hours",
        staff_row=schedule.excel_row,
        message=(f"Fail: Staff in Row {schedule.excel_row} worked {total_hours} hours "
                 "across the 4-week period; required 160."),
    )]


def audit_weekly_rest_days(schedule: StaffSchedule) -> list[AuditFailure]:
    """Require exactly one recognised rest-day code in each week."""
    failures: list[AuditFailure] = []
    for week in range(4):
        week_shifts = schedule.shifts[week * 7:(week + 1) * 7]
        if sum(shift in REST_DAY_CODES for shift in week_shifts) != 1:
            failures.append(AuditFailure(
                category="Weekly rest days",
                staff_row=schedule.excel_row,
                message=(f"Fail: Staff in Row {schedule.excel_row} has no or multiple rest-day codes "
                         f"(RD/RD+/RD++/VLRD) in Week {week + 1}."),
            ))
    return failures


def audit_rest_day_spacing(
    schedule: StaffSchedule,
    previous_rest_day: date | None = None,
    start_date: date | None = None,
    *,
    include_schedule_gaps: bool = True,
) -> list[AuditFailure]:
    """Flag twelve or more worked days between consecutive recognised RDs.

    ``previous_rest_day`` is the staff member's last RD before this roster.
    It is included only when ``start_date`` is supplied, so the Day 1 boundary
    is audited together with the 28-day schedule.
    """
    rest_days = [day for day, shift in enumerate(schedule.shifts, start=1) if shift in REST_DAY_NO_PLUS_CODES]
    failures: list[AuditFailure] = []

    if previous_rest_day is not None and start_date is not None and rest_days:
        first_rest_day = start_date + timedelta(days=rest_days[0] - 1) # Converts a 1-based index (e.g., "Day 1", "Day 5") into an actual calendar date
        elapsed_days = (first_rest_day - previous_rest_day).days
        if elapsed_days - 1 > MAX_REST_DAY_GAP:
            failures.append(AuditFailure(
                category="Rest day spacing",
                staff_row=schedule.excel_row,
                day=rest_days[0],
                roster_date=first_rest_day,
                message=(f"Fail: Staff in Row {schedule.excel_row} last had an RD on "
                         f"{previous_rest_day:%d %B %Y}, then on Day {rest_days[0]} "
                         f"({first_rest_day:%d %B %Y}); this is {elapsed_days - 1} "
                         "consecutive working days."),
            ))

    # A gap larger than the configured maximum between RD dates violates the spacing policy.
    if include_schedule_gaps:
        for earlier, later in zip(rest_days, rest_days[1:]):
            if later - earlier - 1 > MAX_REST_DAY_GAP:
                earlier_date = start_date + timedelta(days=earlier - 1) if start_date else None
                later_date = start_date + timedelta(days=later - 1) if start_date else None
                rest_day_details = (
                    f"Days {earlier} ({earlier_date:%d %B %Y}, {earlier_date:%A}) "
                    f"and {later} ({later_date:%d %B %Y}, {later_date:%A})"
                    if start_date
                    else f"Days {earlier} and {later}"
                )

                failures.append(AuditFailure(
                    category="Rest day spacing",
                    staff_row=schedule.excel_row,
                    day=later,
                    roster_date=later_date,
                    message=(f"Fail: Staff in Row {schedule.excel_row} has rest days on "
                             f"{rest_day_details} ({later - earlier - 1} days apart; "
                             f"maximum is {MAX_REST_DAY_GAP})."),
                ))

    # A roster can end with a long run of work even when there is no following
    # RD in the grid. Check that trailing run independently of the historical
    # RD validation, which is performed by the service layer.
    last_rest_day = rest_days[-1] if rest_days else 0
    trailing_work_days = len(schedule.shifts) - last_rest_day
    if trailing_work_days > MAX_REST_DAY_GAP:
        final_day = len(schedule.shifts)
        final_date = start_date + timedelta(days=final_day - 1) if start_date else None
        end_details = (
            f"Day {final_day} ({final_date:%d %B %Y}, {final_date:%A})"
            if final_date
            else f"Day {final_day}"
        )
        failures.append(AuditFailure(
            category="Rest day spacing",
            staff_row=schedule.excel_row,
            day=final_day,
            roster_date=final_date,
            message=(f"Fail: Staff in Row {schedule.excel_row} has {trailing_work_days} "
                     f"consecutive working days through {end_details}; maximum is "
                     f"{MAX_REST_DAY_GAP}."),
        ))

    return failures


def audit_no_after_night_shift(schedule: StaffSchedule) -> list[AuditFailure]:
    """Require NO codes to follow a D, P, or W shift."""
    failures: list[AuditFailure] = []
    for day_index, shift in enumerate(schedule.shifts):
        # Skip Day 1: it has no preceding day to validate.
        if shift in NO_CODES and day_index > 0 and schedule.shifts[day_index - 1] not in DPW_CODES:
            day = day_index + 1
            previous_label = schedule.shifts[day_index - 1]
            failures.append(AuditFailure(
                category="NO after night shift", staff_row=schedule.excel_row, day=day,
                message=(f"Fail: Staff in Row {schedule.excel_row} has {shift} on Day {day}, "
                         f"but the preceding day is {previous_label}; NO/NO+/NO++ must follow D/P/W."),
            ))
    return failures


def audit_night_shift_sequence(schedule: StaffSchedule) -> list[AuditFailure]:
    """Require night shifts to be followed by another night shift or NO code."""
    failures: list[AuditFailure] = []
    allowed_next_codes = DPW_CODES | NO_CODES
    for day_index, shift in enumerate(schedule.shifts):
        next_shift = schedule.shifts[day_index + 1] if day_index + 1 < len(schedule.shifts) else None
        if shift in DPW_CODES and day_index <27 and next_shift not in allowed_next_codes:
            day = day_index + 1
            failures.append(AuditFailure(
                category="Night-shift sequence", staff_row=schedule.excel_row, day=day,
                message=(f"Fail: Staff in Row {schedule.excel_row} has {shift} on Day {day}, "
                         f"followed by {next_shift or 'no following shift'} on Day {day + 1}. "
                         "D/P/W must be followed by D/P/W, NO, NO+, or NO++."),
            ))
    return failures


def audit_individual_rules(roster: Roster, start_date: date | None = None) -> list[AuditFailure]:
    """Apply every staff-level constraint to every schedule in a roster."""
    audit_functions = (
        audit_four_week_hours,
        audit_weekly_rest_days,
        lambda schedule: audit_rest_day_spacing(schedule, start_date=start_date),
        audit_no_after_night_shift,
        audit_night_shift_sequence,
    )
    return [failure for schedule in roster.staff for audit in audit_functions for failure in audit(schedule)]
