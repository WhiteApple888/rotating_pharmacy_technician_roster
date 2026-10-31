"""Boundary tests for the in-memory FastAPI adapter."""

import asyncio
from datetime import date
from io import BytesIO
from pathlib import Path
import unittest

from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from openpyxl import load_workbook
from starlette.datastructures import Headers, UploadFile

from roster_audit.api import XLSX_MEDIA_TYPE, app, audit, audit_form, optimize, optimize_form
from test_full_optimizer import full_roster_with_rest_day_leave


class ApiTests(unittest.TestCase):
    def test_optimizer_options_validate_json_and_staff_numbers(self):
        params = asyncio.run(optimize_form(start_date=date(2026, 4, 13), num_staff=20,
            fixed_staff='[1, 20]', shift_restrictions='{"2":["D", "OFF"]}'))
        self.assertEqual(params.fixed_staff, [1, 20])
        self.assertEqual(params.shift_restrictions, {2: ["D", "OFF"]})
        for fixed, restrictions in [('bad', None), ('[21]', None), (None, '{"1":["BAD"]}')]:
            with self.subTest(fixed=fixed, restrictions=restrictions), self.assertRaises(RequestValidationError):
                asyncio.run(optimize_form(start_date=date(2026, 4, 13), num_staff=20,
                                         fixed_staff=fixed, shift_restrictions=restrictions))

    def test_optimizer_contract_requires_only_one_workbook(self) -> None:
        schema = app.openapi()
        body = schema["paths"]["/optimize-roster"]["post"]["requestBody"]
        reference = body["content"]["multipart/form-data"]["schema"]["$ref"]
        properties = schema["components"]["schemas"][reference.rsplit("/", 1)[1]]["properties"]
        self.assertIn("file", properties)
        self.assertNotIn("pattern_file", properties)

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

    def test_optimize_downloads_an_audited_roster(self) -> None:
        parameters = asyncio.run(optimize_form(
            start_date=date(2026, 4, 13),
            public_holidays=["19"],
            worksheet_name="13Aprto10May",
        ))
        upload = UploadFile(
            BytesIO(full_roster_with_rest_day_leave()),
            filename="roster.xlsx",
            headers=Headers({"content-type": XLSX_MEDIA_TYPE}),
        )
        response = asyncio.run(optimize(parameters, upload))
        async def read_body() -> bytes:
            return b"".join([chunk async for chunk in response.body_iterator])
        workbook = load_workbook(BytesIO(asyncio.run(read_body())), read_only=True)

        self.assertEqual(response.headers["x-roster-status"], "OPTIMAL")
        self.assertEqual(response.headers["x-roster-penalized-changes"], "0")
        self.assertNotIn("x-roster-changes", response.headers)
        self.assertEqual(int(response.headers["x-roster-plus-changes"]), workbook["Change Log"]["B3"].value)
        self.assertGreater(int(response.headers["x-roster-cell-edits"]), 0)
        self.assertIn(workbook["13Aprto10May"]["AC6"].value, {"VL", "VLOFF", "VLRD"})
        workbook.close()

    def test_optimize_form_rejects_invalid_holiday(self) -> None:
        with self.assertRaises(RequestValidationError):
            asyncio.run(optimize_form(
                start_date=date(2026, 4, 13),
                public_holidays=["2026-06-30"],
            ))
