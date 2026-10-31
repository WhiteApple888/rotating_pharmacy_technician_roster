"""Planner choices for staff selection and exact shift restrictions."""

from dataclasses import dataclass

from .individual_policy import SHIFT_HOURS

DEFAULT_STAFF_COUNT = 16
MAX_STAFF_COUNT = 30


@dataclass(frozen=True)
class PlannerChoices:
    num_staff: int
    fixed_staff: frozenset[int]
    shift_restrictions: dict[int, frozenset[str]]

    @classmethod
    def create(cls, num_staff=DEFAULT_STAFF_COUNT, fixed_staff=None, shift_restrictions=None):
        if isinstance(num_staff, bool) or not isinstance(num_staff, int) or not 1 <= num_staff <= MAX_STAFF_COUNT:
            raise ValueError(f"num_staff must be an integer between 1 and {MAX_STAFF_COUNT}.")
        fixed = frozenset(fixed_staff or ())
        restrictions = shift_restrictions or {}
        for staff in fixed | set(restrictions):
            if isinstance(staff, bool) or not isinstance(staff, int) or not 1 <= staff <= num_staff:
                raise ValueError(f"Staff number {staff!r} must be between 1 and {num_staff}.")
        normalized = {}
        for staff, codes in restrictions.items():
            if isinstance(codes, str) or not isinstance(codes, (set, frozenset, list, tuple)):
                raise ValueError(f"Shift restrictions for staff {staff} must be a collection of shift codes.")
            if any(not isinstance(code, str) or code not in SHIFT_HOURS for code in codes):
                raise ValueError(f"Shift restrictions for staff {staff} contain an unknown shift code.")
            normalized[staff] = frozenset(codes)
        return cls(num_staff, fixed, normalized)

    def allowed(self, staff, codes):
        forbidden = self.shift_restrictions.get(staff, frozenset())
        return tuple(code for code in codes if code not in forbidden)
