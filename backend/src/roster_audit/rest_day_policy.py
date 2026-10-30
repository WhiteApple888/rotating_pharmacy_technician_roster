"""Shared facts for the weekly rest-day and rest-day spacing policies."""

WEEKS_PER_ROSTER = 4
DAYS_PER_WEEK = 7
REST_DAYS_PER_WEEK = 1
MAX_REST_DAY_GAP = 12

# Marked rest days satisfy the weekly requirement but do not reset spacing.
REST_DAY_CODES = frozenset({"RD", "RD+", "RD++", "VLRD"})
REST_DAY_NO_PLUS_CODES = frozenset({"RD", "VLRD"})
