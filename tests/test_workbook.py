"""Tests for Excel roster input."""

import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from roster_audit.workbook import load_roster


class WorkbookTests(unittest.TestCase):
    def test_load_roster_normalises_the_fixed_grid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "roster.xlsx"
            workbook = Workbook()
            workbook.active.cell(row=6, column=4, value=" xe1 ")
            workbook.save(path)
            workbook.close()

            roster = load_roster(path, None)

        self.assertEqual(len(roster.staff), 16)
        self.assertEqual(roster.staff[0].shifts[0], "XE1")
