"""Shared facts for four-week hours and night-shift policies."""

REQUIRED_FOUR_WEEK_HOURS = 160
MAX_CONSECUTIVE_NIGHT_SHIFTS = 2

SHIFT_HOURS: dict[str, int] = {
    "XE1": 8, "XO": 8, "Z1": 8, "Z": 8, "Y": 8, "PH": 8, "VL": 8, "OC": 8,
    "D": 12, "P": 12, "W": 10, "XE": 4, "VL(TO4H)": 4,
    "RD": 0, "RD+": 0, "RD++": 0, "VLRD": 0, "VLOFF": 0, "VLPH": 0,
    "OFF": 0, "OFF+": 0, "OFF++": 0, "NO": 0, "NO+": 0, "NO++": 0,
}

DPW_CODES = frozenset({"D", "P", "W"})
NO_CODES = frozenset({"NO", "NO+", "NO++"})
