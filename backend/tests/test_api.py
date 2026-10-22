"""Boundary tests for the in-memory FastAPI adapter."""

import asyncio
from datetime import date
from io import BytesIO
from pathlib import Path
import unittest

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.datastructures import Headers, UploadFile

from roster_audit.api import XLSX_MEDIA_TYPE, audit, audit_form


class ApiTests(unittest.TestCase):
    def test_audit_returns_the_audit_failure_contract_for_a_valid_upload(self) -> None:
        parameters = asyncio.run(audit_form(
            start_date=date(2026, 4, 13),
            public_holidays=["2026-04-17,12"],
            num_staff=16,
        ))
        repository_root = Path(__file__).resolve().parents[2]
        workbook = (repository_root / "sample" / "13Apr-10May_26.xlsx").read_bytes()
        upload = UploadFile(
            BytesIO(workbook),
            filename="roster.xlsx",
            headers=Headers({"content-type": XLSX_MEDIA_TYPE}),
        )

        response = asyncio.run(audit(parameters, upload))

        self.assertEqual(response.failure_count, len(response.failures))
        self.assertEqual(response.status, "PASS" if response.passed else "FAIL")
        self.assertTrue(all(failure.category and failure.message for failure in response.failures))

    def test_invalid_holiday_is_a_structured_bad_request_validation_error(self) -> None:
        with self.assertRaises(RequestValidationError):
            asyncio.run(audit_form(
                start_date=date(2026, 4, 13),
                public_holidays=["2026-05-30"],
                num_staff=16,
            ))

    def test_upload_requires_xlsx_extension_and_mime_type(self) -> None:
        parameters = asyncio.run(audit_form(
            start_date=date(2026, 4, 13),
            num_staff=16,
        ))
        upload = UploadFile(
            BytesIO(b"not a workbook"),
            filename="roster.csv",
            headers=Headers({"content-type": "text/csv"}),
        )

        with self.assertRaises(HTTPException) as raised:
            asyncio.run(audit(parameters, upload))

        self.assertEqual(raised.exception.status_code, 415)
