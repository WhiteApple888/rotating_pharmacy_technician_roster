"""Daily coverage policy shared by the audit and optimizer."""

from dataclasses import dataclass
from typing import Literal

from .individual_policy import DPW_CODES


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
    CoverageRule("Z", frozenset({"Z"}), 1, "exactly", frozenset({"Saturday"})),
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


def coverage_rules_for_day(day: int, public_holiday_days: set[int]) -> tuple[CoverageRule, ...]:
    """Select the applicable coverage rules for a roster day."""
    weekday = WEEKDAY_NAMES[(day - 1) % 7]
    rules = PH_COVERAGE_RULES if day in public_holiday_days else NORMAL_COVERAGE_RULES
    return tuple(rule for rule in rules if weekday in rule.weekdays)
