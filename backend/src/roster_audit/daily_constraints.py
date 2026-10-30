"""Policy and constraints that apply across the roster on each day."""

from __future__ import annotations

from datetime import date, timedelta

from .daily_policy import (
    ALL_DAYS, DOUBLE_PLUS_CODES, DPW_CODES, FRI_SAT, MON_THU_FRI, MON_TUE,
    NORMAL_COVERAGE_RULES, PH_COVERAGE_RULES, PH_Z_MIN_FOUR_DAYS,
    SINGLE_PLUS_CODES, TUE_WED, VL_OC_CODES, WED_SUN, WEEKDAY_NAMES,
    XE_XE1_CODES, Z1_D_CODES, Z1_Y_CODES, Z1_Y_Z_CODES, CoverageRule,
    coverage_rules_for_day,
)
from .individual_staff_constraints import AuditFailure, Roster



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
        rules = coverage_rules_for_day(day, ph_days)
        failures.extend(
            failure for rule in rules
            if (failure := audit_coverage_rule(rule, day_shifts, day, weekday, roster_date)) is not None
        )
    return failures
