"""Repair an uploaded four-week roster with priorities and minimum change cost."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from time import monotonic

from ortools.sat.python import cp_model

from .daily_policy import coverage_rules_for_day
from .individual_policy import (
    DPW_CODES,
    MAX_CONSECUTIVE_NIGHT_SHIFTS,
    NO_CODES,
    REQUIRED_FOUR_WEEK_HOURS,
    SHIFT_HOURS,
)
from .individual_staff_constraints import Roster, StaffSchedule
from .optimization_policy import (
    DAYS, MARKER_BASES, STAFF_COUNT,
    _change_cost, _first_stage_cost, _marker, _marker_cost, _new_d_cost,
    allowed_shift_codes, is_new_duty_cover, prohibits_unscored_day_cover,
)
from .planner_choices import PlannerChoices
from .rest_day_policy import (
    DAYS_PER_WEEK, MAX_REST_DAY_GAP, REST_DAY_CODES, REST_DAY_NO_PLUS_CODES,
    REST_DAYS_PER_WEEK, WEEKS_PER_ROSTER,
)
from .service import audit_loaded_roster
from .repair_workbook import load_exported_roster, load_repair_input, write_repaired_roster


class NoFeasibleRosterError(ValueError):
    """Unable to find a roster that satisfies the supplied leave and staffing rules."""


@dataclass(frozen=True)
class FullOptimizationResult:
    """An audited export with penalized changes and literal shift-cell edits."""

    status: str
    worksheet: str
    roster: Roster
    penalized_change_count: int
    cell_edit_count: int
    plus_change_count: int
    workbook_bytes: bytes


def _add_rest_day_constraints(model, shift, staff: int, previous: date, start_date: date) -> None:
    """Add the weekly and spacing rules for one staff member to the solver."""
    for week in range(WEEKS_PER_ROSTER):
        model.add(sum(
            shift(staff, day, REST_DAY_CODES)
            for day in range(week * DAYS_PER_WEEK + 1, (week + 1) * DAYS_PER_WEEK + 1)
        ) == REST_DAYS_PER_WEEK)

    window = MAX_REST_DAY_GAP + 1
    for day in range(1, DAYS - window + 2):
        model.add(sum(
            shift(staff, later, REST_DAY_NO_PLUS_CODES)
            for later in range(day, day + window)
        ) >= 1)

    due_day = (previous - start_date).days + MAX_REST_DAY_GAP + 2
    if due_day < 1:
        raise NoFeasibleRosterError(
            f"Staff {staff}'s previous RD has an interval of more than "
            f"{MAX_REST_DAY_GAP} days before the start of current roster"
        )
    model.add(sum(
        shift(staff, day, REST_DAY_NO_PLUS_CODES)
        for day in range(1, min(DAYS, due_day) + 1)
    ) >= 1)


def _add_hours_constraint(model, x, staff: int, codes) -> None:
    """Require the four-week hours target for one staff member."""
    model.add(sum(
        SHIFT_HOURS[code] * variable
        for day in range(1, DAYS + 1)
        for code in codes
        if (variable := x.get((staff, day, code))) is not None
    ) == REQUIRED_FOUR_WEEK_HOURS)


def _add_night_shift_constraints(model, shift, staff: int) -> None:
    """Apply night sequencing and consecutive-night rules within the roster."""
    for day in range(1, DAYS):
        model.add(shift(staff, day, DPW_CODES) <=
                  shift(staff, day + 1, DPW_CODES | NO_CODES))
        model.add(shift(staff, day + 1, NO_CODES) <= shift(staff, day, DPW_CODES))

    window = MAX_CONSECUTIVE_NIGHT_SHIFTS + 1
    for day in range(1, DAYS - window + 2):
        model.add(sum(shift(staff, later, DPW_CODES)
                      for later in range(day, day + window)) <= MAX_CONSECUTIVE_NIGHT_SHIFTS)


def _add_daily_coverage_constraints(model, shift, day: int, public_holiday_days: set[int],
                                    staff_count: int = STAFF_COUNT) -> None:
    """Add the applicable coverage targets for one roster day."""
    for rule in coverage_rules_for_day(day, public_holiday_days):
        count = sum(shift(staff, day, rule.accepted_codes)
                    for staff in range(1, staff_count + 1))
        if rule.comparison == "exactly":
            model.add(count == rule.target)
        elif rule.comparison == "at least":
            model.add(count >= rule.target)
        else:
            model.add(count <= rule.target)

def optimize_full_roster(
    workbook_bytes: bytes,
    *,
    start_date: date,
    public_holiday_days: set[int],
    worksheet_name: str | None,
    max_time_seconds: float = 60.0,
    num_staff: int = STAFF_COUNT,
    fixed_staff: set[int] | None = None,
    shift_restrictions: dict[int, set[str]] | None = None,
) -> FullOptimizationResult:
    """Repair only the uploaded roster, preserving priorities before change cost."""
    if not isfinite(max_time_seconds) or max_time_seconds <= 0:
        raise ValueError("max_time_seconds must be positive.")
    choices = PlannerChoices.create(num_staff, fixed_staff, shift_restrictions)
    fixed_staff = choices.fixed_staff
    restrictions = choices.shift_restrictions
    deadline = monotonic() + max_time_seconds
    if start_date.weekday() != 0:
        raise ValueError("Roster start_date must be a Monday to match the workbook layout.")
    roster, prior, priorities = load_repair_input(workbook_bytes, start_date, worksheet_name, num_staff, fixed_staff)
    for staff in fixed_staff:
        for day, code in enumerate(roster.staff[staff - 1].shifts, start=1):
            if code in restrictions.get(staff, ()):
                raise NoFeasibleRosterError(
                    f"Staff {staff}, day {day} is fixed to restricted shift {code}."
                )
    proposed, duty_status = _solve_roster(roster, prior, priorities, start_date, public_holiday_days, deadline, fixed_staff, restrictions)
    failures = audit_loaded_roster(proposed, public_holiday_days, start_date, prior)
    if failures:
        first = failures[0]
        raise NoFeasibleRosterError(
            f"CP-SAT candidate failed the roster audit ({len(failures)} failures): {first.message}"
        )

    changes, cell_edits, plus_changes = _count_changes(roster, proposed)
    output = write_repaired_roster(workbook_bytes, roster.worksheet, roster, proposed, start_date,
                                   changes, cell_edits, plus_changes, fixed_staff)
    exported = load_exported_roster(output, roster.worksheet, num_staff)
    if exported != proposed or audit_loaded_roster(
        exported, public_holiday_days, start_date, prior,
    ):
        raise NoFeasibleRosterError("The exported workbook did not pass the roster audit.")
    return FullOptimizationResult(
        "OPTIMAL" if duty_status == cp_model.OPTIMAL else "FEASIBLE",
        roster.worksheet, proposed, changes, cell_edits, plus_changes, output,
    )


def _count_changes(original: Roster, proposed: Roster) -> tuple[int, int, int]:
    """Count penalized changes, edited cells, and changed plus markers."""
    pairs = ((old, new) for before, after in zip(original.staff, proposed.staff)
             for old, new in zip(before.shifts, after.shifts))
    changes = cell_edits = plus_changes = 0
    for old, new in pairs:
        changes += _change_cost(old, new)
        cell_edits += old != new
        plus_changes += _marker(old) != _marker(new)
    return changes, cell_edits, plus_changes


def _solve_roster(roster: Roster, prior, priorities, start_date: date,
                  public_holiday_days: set[int], deadline: float,
                  fixed_staff: frozenset[int] = frozenset(),
                  shift_restrictions: dict[int, set[str]] | None = None):
    """Construct and solve the duty and marker optimization passes."""
    choices_policy = PlannerChoices.create(len(roster.staff), fixed_staff, shift_restrictions)
    baseline = tuple(schedule.shifts for schedule in roster.staff)
    for staff, shifts in enumerate(baseline, start=1):
        for day, shift in enumerate(shifts, start=1):
            if shift not in SHIFT_HOURS:
                raise ValueError(f"Unknown shift code {shift!r} for staff {staff}, day {day}.")

    model = cp_model.CpModel()
    codes = tuple(sorted(set(SHIFT_HOURS)))
    x: dict[tuple[int, int, str], cp_model.IntVar] = {}
    changed: list[cp_model.IntVar] = []
    staff_count = len(roster.staff)
    for staff in range(1, staff_count + 1):
        for day in range(1, DAYS + 1):
            original = baseline[staff - 1][day - 1]
            allowed = allowed_shift_codes(original, staff, fixed_staff)
            allowed = choices_policy.allowed(staff, allowed)
            choices = [
                model.new_bool_var(f"s{staff}_d{day}_{code}")
                for code in allowed
            ]
            model.add_exactly_one(choices)
            x.update({(staff, day, code): variable for code, variable in zip(allowed, choices)})
            # This flag is one only when the chosen code leaves the original
            # cost-equivalence group. Free conversions and markers contribute 0.
            difference = model.new_bool_var(f"changed_s{staff}_d{day}")
            model.add(difference == sum(
                x[staff, day, code] for code in allowed
                if _change_cost(original, code)
            ))
            changed.append(difference)

    def shift(staff: int, day: int, accepted: set[str] | frozenset[str]):
        return sum(x[staff, day, code] for code in accepted if (staff, day, code) in x)

    # Score newly assigned duties directly against the uploaded roster. There
    # is no missing-duty reconstruction and no assumed absent-person mapping.
    # checks the staff member’s weekly priority and applies a cost or a restriction.
    fallback_terms = []
    priority_terms = []
    for (staff, day, code), variable in x.items():
        original = baseline[staff - 1][day - 1]

        if is_new_duty_cover(original, code):
            priority = priorities[(day - 1) // DAYS_PER_WEEK].get(staff)

            if prohibits_unscored_day_cover(original, code, priority):
                model.add(variable == 0)

            # No priority: the assignment is counted as a fallback. 
            # The objective strongly prefers fewer fallback assignments.
            if priority is None:
                fallback_terms.append(variable)

            # Has a priority: the assignment contributes its priority value as a cost.
            # When other constraints allow, the solver prefers a smaller total priority cost.
            else:
                priority_terms.append(priority * variable)

    for staff in range(1, staff_count + 1):
        _add_hours_constraint(model, x, staff, codes)
        _add_rest_day_constraints(model, shift, staff, prior[staff - 1], start_date)
        _add_night_shift_constraints(model, shift, staff)


    for day in range(1, DAYS + 1):
        _add_daily_coverage_constraints(model, shift, day, public_holiday_days, staff_count)

    # Each component is bounded across the entire roster, so lower-priority
    # costs cannot outweigh even one unit of a higher-priority cost.
    fallback_cost = sum(fallback_terms)
    priority_cost = sum(priority_terms)
    new_d_cost = _new_d_cost(x, baseline)
    model.minimize(_first_stage_cost(fallback_cost, priority_cost, new_d_cost, sum(changed), staff_count))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(0.001, (deadline - monotonic()) * 0.85)
    solver.parameters.num_search_workers = 8
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        if status == cp_model.UNKNOWN:
            raise NoFeasibleRosterError(
                "The time limit expired before a feasible roster was found within the solver time limit."
            )
        raise NoFeasibleRosterError(
            "No roster satisfying the leave, priority, coverage, hours, rest, and night rules was found."
        )
    if status == cp_model.FEASIBLE and solver.value(fallback_cost):
        raise NoFeasibleRosterError(
            "Valid roster found but the time limit expired before priority exhaustion could be proved for fallback cover."
        )

    # Freeze duties and base statuses, then optimize only their markers. This
    # prevents changing duties merely to manufacture preferred marker holders.
    # The same individual constraints remain active, including unmarked-RD gaps.
    duty_status = status
    for staff in range(1, staff_count + 1):
        for day in range(1, DAYS + 1):
            selected = next(
                code for code in codes
                if (staff, day, code) in x and solver.boolean_value(x[staff, day, code])
            )
            base = selected.rstrip("+")
            model.add(shift(staff, day, frozenset(
                {base, base + "+", base + "++"} if base in MARKER_BASES else {selected}
            )) == 1)
    model.minimize(_marker_cost(x, priorities))
    solver.parameters.max_time_in_seconds = max(0.001, deadline - monotonic())
    status = solver.solve(model)
    if status != cp_model.OPTIMAL:
        raise NoFeasibleRosterError(
            "The time limit expired before the OFF > RD > NO marker preference could be proved."
        )

    proposed = Roster(roster.worksheet, tuple(
        StaffSchedule(schedule.excel_row, tuple(
            next(code for code in codes
                 if (staff, day, code) in x and solver.boolean_value(x[staff, day, code]))
            for day in range(1, DAYS + 1)
        ))
        for staff, schedule in enumerate(roster.staff, start=1)
    ))
    return proposed, duty_status
