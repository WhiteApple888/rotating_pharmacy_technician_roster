"""Tests for daily roster coverage constraints."""

import unittest

from roster_audit.individual_staff_constraints import Roster, StaffSchedule
from roster_audit.daily_constraints import audit_daily_rules


class CoverageTests(unittest.TestCase):
    def test_public_holiday_replaces_normal_day_rules(self) -> None:
        day_one = ("XE", "XE1", "D", "P", "W", "D", "Z1", "Y", "Z1", "Y", "OFF+", "OFF++")
        filler = ("RD",) * 27
        roster = Roster(
            "Roster",
            tuple(StaffSchedule(row, (day_one[index],) + filler) for index, row in enumerate(range(6, 18))),
        )

        failures = audit_daily_rules(roster, {1})

        self.assertFalse(any(failure.day == 1 for failure in failures))
