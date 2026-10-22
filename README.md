# Pharmacy Technician Roster Auditor

A web application and Python CLI for auditing four-week pharmacy technician rosters in Excel. Upload a workbook through the Next.js interface or run the auditor locally; both use the same FastAPI-backed validation rules.

The auditor reads the source workbook without modifying it. The CLI additionally produces an Excel report with `Summary` and `Failures` sheets.

## What it checks

- Four-week working hours and weekly rest-day requirements
- Rest-day spacing, including the boundary from the previous roster
- Night-shift and next-day-off sequencing
- Daily staffing coverage, with separate public-holiday rules

The default roster has 16 staff across 28 days. The API supports 1–30 staff; the roster grid starts at worksheet row 6.

## Requirements

- Python 3.12
- Node.js 20+ and pnpm (for the web client)

## Run locally

Start the API:

```powershell
cd backend
python -m pip install -e .
uvicorn roster_audit.api:app --reload --port 8000
```

In another terminal, start the web client:

```powershell
cd web
Copy-Item .env.example .env.local
pnpm install
pnpm dev
```

The client is available at `http://localhost:3000`, and the API documentation is at `http://localhost:8000/docs`. Set `AUDIT_API_URL` (server-side) or `NEXT_PUBLIC_AUDIT_API_URL` in `web/.env.local` if the API runs elsewhere.

## CLI

```powershell
cd backend
roster-audit ..\sample\13Apr-10May_26.xlsx --start_date 2026-04-13 --ph 1 --report .\roster_audit.xlsx
```

```text
roster-audit ROSTER.xlsx --start_date YYYY-MM-DD [--sheet SHEET] [--ph DAYS] [--report REPORT.xlsx]
```

`--ph` accepts comma-separated roster-day numbers and/or ISO dates and can be repeated. The command exits with `0` for a passing roster and `1` when validation failures are found.

## Workbook expectations

The selected worksheet contains the 28-day shift grid, beginning at row 6. A `lastRosterRD` worksheet is also required: column B, beginning at `B2`, must provide the previous rest-day date for each staff member, in roster order. Dates must be before Day 1.

## API

`POST /rpt-roster` accepts a multipart `.xlsx` upload (maximum 10 MB) plus:

| Field | Required | Description |
| --- | --- | --- |
| `file` | Yes | Excel workbook (`.xlsx`) |
| `start_date` | Yes | Roster Day 1 (`YYYY-MM-DD`) |
| `public_holidays` | No | Repeated or comma-separated roster days and/or ISO dates |
| `num_staff` | No | Number of staff; defaults to 16 |
| `worksheet_name` | No | Worksheet to audit; defaults to the active sheet |

Responses include the pass/fail status, worksheet name, failure count, and structured failures. `GET /health` returns service readiness. See the interactive contract at `/docs`.

## Validation and testing

```powershell
cd backend
python -m unittest discover -s tests -v

cd ..\web
pnpm typecheck
pnpm lint
```

## Project structure

| Path | Purpose |
| --- | --- |
| `backend/` | FastAPI service, CLI, Excel parsing, audit rules, and tests |
| `web/` | Next.js upload and results interface |
| `sample/` | Example roster workbooks |

Policy definitions live in `backend/src/roster_audit/individual_staff_constraints.py` and `daily_constraints.py`. Update the corresponding tests whenever a policy changes.
