"""Policy and constraints that apply across the roster on each day."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from datetime import date, timedelta

from .individual_staff_constraints import AuditFailure, DPW_CODES, Roster



WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
SINGLE_PLUS_CODES = frozenset({"OFF+", "RD+", "NO+"})
DOUBLE_PLUS_CODES = frozenset({"OFF++", "RD++", "NO++"})
Z1_D_CODES = frozenset({"Z1", "D"})
XE_XE1_CODES = frozenset({"XE", "XE1"})
Z1_Y_Z_CODES = frozenset({"Z1", "Y", "Z"})
Z1_Y_CODES = frozenset({"Z1", "Y"})
VL_OC_CODES = frozenset({"VL", "VLOFF", "VLRD", "OC"})

ALL_DAYS = frozenset(WEEKDAY_NAMES)
MON_TUE = frozenset({"Monday", "Tuesday"})
MON_THU_FRI = frozenset({"Monday", "Thursday", "Friday"})
TUE_WED = frozenset({"Tuesday", "Wednesday"})
WED_SUN = frozenset({"Wednesday", "Thursday", "Friday", "Saturday", "Sunday"})
FRI_SAT = frozenset({"Friday", "Saturday"})
PH_Z_MIN_FOUR_DAYS = ALL_DAYS - FRI_SAT


@dataclass(frozen=True)
class CoverageRule:
    """One coverage target that applies to a set of weekdays."""

    label: str
    accepted_codes: frozenset[str]
    target: int
    comparison: Literal["at least", "exactly", "at most"]
    weekdays: frozenset[str]


NORMAL_COVERAGE_RULES = (
    CoverageRule("VL/VLOFF/VLRD/OC", VL_OC_CODES, 2, "at most", ALL_DAYS),
    CoverageRule("single-plus (OFF+/RD+/NO+)", SINGLE_PLUS_CODES, 1, "exactly", ALL_DAYS),
    CoverageRule("double-plus (OFF++/RD++/NO++)", DOUBLE_PLUS_CODES, 1, "exactly", ALL_DAYS),
    CoverageRule("Z1/D", Z1_D_CODES, 6, "at least", MON_THU_FRI),
    CoverageRule("Z1/D", Z1_D_CODES, 5, "at least", TUE_WED),
    CoverageRule("D/P/W", DPW_CODES, 4, "exactly", MON_TUE),
    CoverageRule("D/P/W", DPW_CODES, 3, "exactly", WED_SUN),
    CoverageRule("Z1/Y/Z", Z1_Y_Z_CODES, 5, "at least", frozenset({"Saturday"})),
    CoverageRule("Z1/Y", Z1_Y_CODES, 4, "at least", frozenset({"Sunday"})),
    CoverageRule("Y", frozenset({"Z"}), 1, "exactly", frozenset({"Saturday"})),
    CoverageRule("Y", frozenset({"Y"}), 1, "exactly", frozenset({"Saturday"})),
    CoverageRule("Y", frozenset({"Y"}), 2, "exactly", frozenset({"Sunday"})),
    CoverageRule("XE/XE1", XE_XE1_CODES, 2, "exactly", frozenset({"Sunday"})),
)

PH_COVERAGE_RULES = (
    CoverageRule("VL/VLOFF/VLRD/OC", VL_OC_CODES, 2, "at most", ALL_DAYS),
    CoverageRule("single-plus (OFF+/RD+/NO+)", SINGLE_PLUS_CODES, 1, "exactly", ALL_DAYS),
    CoverageRule("double-plus (OFF++/RD++/NO++)", DOUBLE_PLUS_CODES, 1, "exactly", ALL_DAYS),
    CoverageRule("Z1/Y/Z", Z1_Y_Z_CODES, 4, "at least", PH_Z_MIN_FOUR_DAYS),
    CoverageRule("Z1/Y/Z", Z1_Y_Z_CODES, 5, "at least", FRI_SAT),
    CoverageRule("XE/XE1", XE_XE1_CODES, 2, "exactly", ALL_DAYS),
    CoverageRule("D/P/W", DPW_CODES, 4, "exactly", MON_TUE),
    CoverageRule("D/P/W", DPW_CODES, 3, "exactly", WED_SUN),
)


def audit_coverage_rule(rule: CoverageRule, shifts: tuple[str, ...], day: int, weekday: str, roster_date: date | None,) -> AuditFailure | None:
    """Evaluate one coverage rule for one roster day."""
    actual = sum(shift in rule.accepted_codes for shift in shifts)
    if rule.comparison == "at least":
        passed = actual >= rule.target

    elif rule.comparison == "exactly":
        passed = actual == rule.target

    elif rule.comparison == "at most":
        passed = actual <= rule.target
    
    if passed:
        return None

    day_description = (
        f"Day {day} ({roster_date:%d %B %Y}, {weekday})"
        if roster_date
        else f"Day {day} ({weekday})"
    )
    
    return AuditFailure(
        category="Daily coverage", day=day,
        message=(f"{day_description} has {actual} {rule.label} shifts; required "
                 f"{rule.comparison} {rule.target}."),
        roster_date=roster_date,
    )

def audit_daily_rules(roster: Roster, ph_days: set[int], start_date: date | None = None,) -> list[AuditFailure]:
    """Apply normal-day or public-holiday coverage rules across the roster."""
    failures: list[AuditFailure] = []
    for day_index in range(28):
        day = day_index + 1
        roster_date = start_date + timedelta(days=day_index) if start_date else None
        weekday = WEEKDAY_NAMES[day_index % 7]
        day_shifts = tuple(schedule.shifts[day_index] for schedule in roster.staff)
        rules = PH_COVERAGE_RULES if day in ph_days else NORMAL_COVERAGE_RULES
        failures.extend(
            failure for rule in rules if weekday in rule.weekdays
            if (failure := audit_coverage_rule(rule, day_shifts, day, weekday, roster_date)) is not None
        )
    return failures
