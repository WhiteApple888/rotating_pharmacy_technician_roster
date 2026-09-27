"""Tests for the application workflow result type."""

import unittest
from pathlib import Path

from roster_audit.individual_staff_constraints import AuditFailure
from roster_audit.service import AuditResult


class ServiceTests(unittest.TestCase):
    def test_result_passed_reflects_failures(self) -> None:
        self.assertTrue(AuditResult([], Path("report.xlsx")).passed)
        self.assertFalse(AuditResult([AuditFailure("test", "failed")], Path("report.xlsx")).passed)
