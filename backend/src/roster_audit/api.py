"""FastAPI application for the stateless roster-audit service."""

from __future__ import annotations

import os
import json
import zipfile
from datetime import date
from io import BytesIO
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError, model_validator

from .api_service import audit_uploaded_roster
from .individual_staff_constraints import AuditFailure
from .optimizer import NoFeasibleRosterError, optimize_full_roster
from .parsing import parse_ph_days
from .planner_choices import DEFAULT_STAFF_COUNT, MAX_STAFF_COUNT, PlannerChoices

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_STAFF = MAX_STAFF_COUNT


def cors_origins() -> list[str]:
    """Load explicit browser origins; never default to a wildcard."""
    supplied = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
    return [origin.strip().rstrip("/") for origin in supplied.split(",") if origin.strip()]


class AuditInput(BaseModel):
    """Validated audit parameters after multipart form parsing."""

    start_date: date
    public_holidays: list[str] = Field(default_factory=list)
    num_staff: int = Field(gt=0, le=MAX_STAFF)
    worksheet_name: str | None = None

    @model_validator(mode="after")
    def validate_dates_and_holidays(self) -> "AuditInput":
        # Validate dates and 1--28 day numbers now, not after workbook parsing.
        parse_ph_days(self.public_holidays, self.start_date)
        return self

    @property
    def public_holiday_days(self) -> set[int]:
        return parse_ph_days(self.public_holidays, self.start_date)


class AuditFailureResponse(BaseModel):
    category: str
    message: str
    staff_row: int | None
    day: int | None
    source_cell: str | None
    roster_date: date | None

    @classmethod
    def from_domain(cls, failure: AuditFailure) -> "AuditFailureResponse":
        return cls(**{
            "category": failure.category,
            "message": failure.message,
            "staff_row": failure.staff_row,
            "day": failure.day,
            "source_cell": failure.source_cell,
            "roster_date": failure.roster_date,
        })


class AuditResponse(BaseModel):
    status: Literal["PASS", "FAIL"]
    passed: bool
    failure_count: int
    worksheet: str
    failures: list[AuditFailureResponse]


class OptimizeInput(BaseModel):
    """Validated optimizer parameters after multipart form parsing."""

    start_date: date
    public_holidays: list[str] = Field(default_factory=list)
    worksheet_name: str | None = None
    max_time_seconds: float = Field(default=60.0, gt=0, le=120)
    num_staff: int = Field(default=DEFAULT_STAFF_COUNT, gt=0, le=MAX_STAFF)
    fixed_staff: list[int] = Field(default_factory=list)
    shift_restrictions: dict[int, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_holidays(self) -> "OptimizeInput":
        parse_ph_days(self.public_holidays, self.start_date)
        PlannerChoices.create(self.num_staff, self.fixed_staff, self.shift_restrictions)
        return self

    @property
    def public_holiday_days(self) -> set[int]:
        return parse_ph_days(self.public_holidays, self.start_date)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[object] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


async def audit_form(
    start_date: Annotated[date, Form()],
    public_holidays: Annotated[list[str] | None, Form()] = None,
    num_staff: Annotated[int, Form(gt=0, le=MAX_STAFF)] = DEFAULT_STAFF_COUNT,
    worksheet_name: Annotated[str | None, Form()] = None,
) -> AuditInput:
    """Parse both repeated and comma-separated ``public_holidays`` fields."""
    try:
        return AuditInput(
            start_date=start_date,
            public_holidays=public_holidays or [],
            num_staff=num_staff,
            worksheet_name=worksheet_name,
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


async def optimize_form(
    start_date: Annotated[date, Form()],
    public_holidays: Annotated[list[str] | None, Form()] = None,
    worksheet_name: Annotated[str | None, Form()] = None,
    max_time_seconds: Annotated[float, Form(gt=0, le=120)] = 60.0,
    num_staff: Annotated[int, Form(gt=0, le=MAX_STAFF)] = DEFAULT_STAFF_COUNT,
    fixed_staff: Annotated[str | None, Form()] = None,
    shift_restrictions: Annotated[str | None, Form()] = None,
) -> OptimizeInput:
    """Parse optimizer multipart fields."""
    try:
        return OptimizeInput(
            start_date=start_date,
            public_holidays=public_holidays or [],
            worksheet_name=worksheet_name,
            max_time_seconds=max_time_seconds,
            num_staff=num_staff,
            fixed_staff=json.loads(fixed_staff) if fixed_staff is not None else [],
            shift_restrictions=json.loads(shift_restrictions) if shift_restrictions is not None else {},
        )
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
    except (json.JSONDecodeError, TypeError) as exc:
        raise RequestValidationError([{"loc": ("body",), "msg": "fixed_staff and shift_restrictions must be valid JSON.", "type": "value_error"}]) from exc


app = FastAPI(
    title="Roster Audit API",
    version="1.0.0",
    description="Stateless API for auditing uploaded pharmacy technician rosters.",
)

# This middleware tells the browser which external origins 
# are allowed to talk to your Roster Audit API and under what conditions.
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition", "X-Roster-Penalized-Changes", "X-Roster-Cell-Edits", "X-Roster-Plus-Changes", "X-Roster-Status"],
)


def custom_openapi() -> dict[str, object]:
    """Document the 400 validation contract instead of FastAPI's default 422."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, description=app.description, routes=app.routes)
    for path in ("/rpt-roster", "/optimize-roster"):
        schema["paths"][path]["post"]["responses"].pop("422", None)
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.exception_handler(RequestValidationError)
async def request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Use one documented 400 response shape for malformed client input."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({
            "error": {
                "code": "invalid_request",
                "message": "One or more request fields are invalid.",
                "details": exc.errors(),
            }
        }),
    )


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    """Keep expected client errors in the same top-level error envelope."""
    body = exc.detail if isinstance(exc.detail, dict) and "error" in exc.detail else {
        "error": {"code": "request_error", "message": str(exc.detail)}
    }
    return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(body))


@app.get("/health", tags=["operations"])
async def health() -> dict[str, str]:
    """Lightweight readiness endpoint suitable for Render health checks."""
    return {"status": "ok"}


@app.post(
    "/rpt-roster",
    response_model=AuditResponse,
    responses={400: {"model": ErrorResponse}, 413: {"model": ErrorResponse}, 415: {"model": ErrorResponse}},
    tags=["audit"],
)
async def audit(
    parameters: Annotated[AuditInput, Depends(audit_form)],
    file: Annotated[UploadFile, File(description="Roster workbook in .xlsx format")],
) -> AuditResponse:
    """Audit one XLSX roster entirely in memory and return JSON failures."""
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx") or file.content_type != XLSX_MEDIA_TYPE:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": {
                    "code": "unsupported_file",
                    "message": f"file must be an .xlsx upload with Content-Type {XLSX_MEDIA_TYPE}.",
                }
            },
        )

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "file_too_large",
                    "message": f"file must be no larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
                }
            },
        )
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "empty_file", "message": "file must not be empty."}},
        )

    try:
        worksheet, failures = audit_uploaded_roster(
            contents,
            start_date=parameters.start_date,
            public_holiday_days=parameters.public_holiday_days,
            num_staff=parameters.num_staff,
            worksheet_name=parameters.worksheet_name,
        )
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_workbook", "message": str(exc)}},
        ) from exc

    response_failures = [AuditFailureResponse.from_domain(failure) for failure in failures]
    return AuditResponse(
        status="PASS" if not response_failures else "FAIL",
        passed=not response_failures,
        failure_count=len(response_failures),
        worksheet=worksheet,
        failures=response_failures,
    )


@app.post(
    "/optimize-roster",
    response_class=StreamingResponse,
    responses={
        200: {"content": {XLSX_MEDIA_TYPE: {}}},
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
    },
    tags=["optimization"],
)
async def optimize(
    parameters: Annotated[OptimizeInput, Depends(optimize_form)],
    file: Annotated[UploadFile, File(description="Complete 28-day roster workbook in .xlsx format")],
) -> StreamingResponse:
    """Return an audited, optimized XLSX copy of a complete roster."""
    if (not (file.filename or "").lower().endswith(".xlsx")
            or file.content_type != XLSX_MEDIA_TYPE):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": {
                    "code": "unsupported_file",
                    "message": f"file must be an .xlsx upload with Content-Type {XLSX_MEDIA_TYPE}.",
                }
            },
        )

    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "file_too_large",
                    "message": f"file must be no larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
                }
            },
        )
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "empty_file", "message": "file must not be empty."}},
        )

    try:
        result = optimize_full_roster(
            contents,
            start_date=parameters.start_date,
            public_holiday_days=parameters.public_holiday_days,
            worksheet_name=parameters.worksheet_name,
            max_time_seconds=parameters.max_time_seconds,
            num_staff=parameters.num_staff,
            fixed_staff=set(parameters.fixed_staff),
            shift_restrictions=parameters.shift_restrictions,
        )
    except NoFeasibleRosterError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "infeasible_roster", "message": str(exc)}},
        ) from exc
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_workbook", "message": str(exc)}},
        ) from exc

    return StreamingResponse(
        BytesIO(result.workbook_bytes),
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": 'attachment; filename="optimized_roster.xlsx"',
            "X-Roster-Penalized-Changes": str(result.penalized_change_count),
            "X-Roster-Plus-Changes": str(result.plus_change_count),
            "X-Roster-Cell-Edits": str(result.cell_edit_count),
            "X-Roster-Status": result.status,
        },
    )
