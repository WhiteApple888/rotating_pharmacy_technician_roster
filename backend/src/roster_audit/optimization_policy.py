"""Roster-repair choices, takeover priorities, and objective policy."""

from ortools.sat.python import cp_model

from .individual_policy import DPW_CODES
from .planner_choices import DEFAULT_STAFF_COUNT
from .rest_day_policy import DAYS_PER_WEEK, WEEKS_PER_ROSTER

STAFF_COUNT = DEFAULT_STAFF_COUNT
DAYS = DAYS_PER_WEEK * WEEKS_PER_ROSTER
MAX_PRIORITY = 6
DAY_DUTY_CODES = frozenset({"Z", "Y", "XE1", "Z1", "XE"})
MARKER_BASES = frozenset({"OFF", "RD", "NO"})
MARKER_CODES = frozenset(base + marker for base in MARKER_BASES for marker in ("", "+", "++"))
LEAVE_OPTIONS = frozenset({"VL", "VLOFF", "VLRD"})
PROTECTED_CODES = frozenset({"VLPH", "VL(TO4H)", "OC"})
NORMAL_CODES = DPW_CODES | DAY_DUTY_CODES | MARKER_CODES
FREE_CHANGE_GROUPS = (LEAVE_OPTIONS, frozenset({"OFF", "RD"}), frozenset({"Z", "Y", "Z1"}))
MARKER_BASE_WEIGHT = {"OFF": 0, "RD": 1, "NO": 2}


def allowed_shift_codes(original: str, staff: int, fixed_staff: frozenset[int] = frozenset()) -> tuple[str, ...]:
    """Return repair choices while preserving fixed staff and protected shifts."""
    if staff in fixed_staff or original in PROTECTED_CODES:
        return (original,)
    if original in LEAVE_OPTIONS:
        return tuple(sorted(LEAVE_OPTIONS))
    return tuple(sorted(NORMAL_CODES | {original}))


def is_new_duty_cover(original: str, proposed: str) -> bool:
    """Identify new duty cover that consumes a weekly priority."""
    return (proposed in DPW_CODES and original not in DPW_CODES
            or proposed in DAY_DUTY_CODES and original.rstrip("+") in MARKER_BASES)


def prohibits_unscored_day_cover(original: str, proposed: str, priority: int | None) -> bool:
    """Disallow unscored day-duty cover from a night-off shift."""
    return proposed in DAY_DUTY_CODES and priority is None and original.rstrip("+") == "NO"


def valid_takeover_priority(value: object, staff: int, used: set[int], fixed_staff: frozenset[int] = frozenset()) -> bool:
    """A supplied score is unique, in range, and absent for fixed staff."""
    return (staff not in fixed_staff and not isinstance(value, bool)
            and isinstance(value, int) and 1 <= value <= MAX_PRIORITY and value not in used)


def _new_d_cost(x: dict[tuple[int, int, str], cp_model.IntVar],
                baseline: tuple[tuple[str, ...], ...]):
    """Count D only when the uploaded cell was outside the night-duty group."""
    return sum(variable for (staff, day, code), variable in x.items()
               if code == "D" and baseline[staff - 1][day - 1] not in DPW_CODES)


def _first_stage_cost(fallback_cost, priority_cost, new_d_cost, change_cost, staff_count: int = STAFF_COUNT):
    """Combine roster-wide objectives in their required lexicographic order."""
    cells = staff_count * DAYS
    return (((fallback_cost * (MAX_PRIORITY * cells + 1) + priority_cost) * (cells + 1)
             + new_d_cost) * (cells + 1) + change_cost)


def _marker(code: str) -> str:
    """Return the trailing plus marker, including the absence of one."""
    return code[len(code.rstrip("+")):]


def _change_cost(original: str, proposed: str) -> int:
    """Return 0 for user-approved equivalent codes, otherwise 1 per cell.

    The leave conversions form one group: VL <-> VLOFF <-> VLRD.
    Stripping markers also makes OFF/RD marker variants mutually free.
    """
    original = original.rstrip("+")
    proposed = proposed.rstrip("+")
    return int(original != proposed and not any(
        original in group and proposed in group for group in FREE_CHANGE_GROUPS
    ))


def _marker_cost(x: dict[tuple[int, int, str], cp_model.IntVar],
                 priorities: tuple[dict[int, int], ...]):
    """Rank first on-call, then second, by base code and weekly priority.

    Each component is a roster-wide total. Weights make the components
    lexicographic: a lower-ranked component cannot outweigh a higher one.
    """
    days = len({day for _, day, _ in x})
    
    # Order is first_on_call base, first_on_call score, second_on_call base, second_on_call score as per tuple
    # Use to calculate a single objective target
    components = [[], [], [], []]
    for (staff, day, code), variable in x.items():
        if code not in MARKER_CODES or not code.endswith("+"):
            continue
        second = code.endswith("++")
        base = code.rstrip("+")
        rank = priorities[(day - 1) // DAYS_PER_WEEK].get(staff, MAX_PRIORITY + 1) - 1
        index = 2 if second else 0
        components[index].append(MARKER_BASE_WEIGHT[base] * variable)
        components[index + 1].append(rank * variable)

    # Consolidate bounds and weights into 1 optimization target.
    score_bound = MAX_PRIORITY * days # 6 priority scores per day
    base_bound = max(MARKER_BASE_WEIGHT.values()) * days # max weight per day is 2 e.g. NO given plus

    # Priority second-on-call base > second-on-call priority cost.
    weight_second_base = score_bound + 1

    # Priority first -on-call priority score > second-on-call base.
    weight_first_score = (base_bound + 1) * weight_second_base

    # Priority first on-call base > first-on-call priority score
    weight_first_base = (score_bound + 1) * weight_first_score
    weights = (weight_first_base, weight_first_score, weight_second_base, 1)
    return sum(weight * sum(terms) for weight, terms in zip(weights, components))


