"""Tests for roster input parsing helpers."""

import unittest
from datetime import date

from roster_audit.parsing import day_columns, normalise, parse_ph_days


class ParsingTests(unittest.TestCase):
    def test_normalise_removes_whitespace_and_uppercases(self) -> None:
        self.assertEqual(normalise(" vl (to 4h) "), "VL(TO4H)")
        self.assertEqual(normalise(None), "")

    def test_public_holidays_accept_day_numbers_and_dates(self) -> None:
        self.assertEqual(parse_ph_days(["1, 2026-04-15", "3"], date(2026, 4, 13)), {1, 3})

    def test_public_holiday_date_requires_start_date(self) -> None:
        with self.assertRaisesRegex(ValueError, "needs --start-date"):
            parse_ph_days(["2026-04-15"], None)

    def test_day_columns_cover_four_seven_day_blocks(self) -> None:
        columns = day_columns()
        self.assertEqual(len(columns), 28)
        self.assertEqual(columns[:7], list(range(4, 11)))
        self.assertEqual(columns[-7:], list(range(37, 44)))
