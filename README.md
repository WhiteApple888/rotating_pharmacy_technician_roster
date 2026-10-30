# Pharmacy Technician Roster Auditor

A web application and Python CLI for auditing four-week pharmacy technician rosters in Excel. Upload a workbook through the Next.js interface or run the auditor locally; both use the same FastAPI-backed validation rules.

The auditor reads the source workbook without modifying it. The CLI additionally produces an Excel report with `Summary` and `Failures` sheets.

## What it checks

- Four-week working hours and weekly rest-day requirements
- Rest-day spacing, including the boundary from the previous roster
- Night-shift and next-day-off sequencing, including a maximum of two consecutive P/W/D shifts
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

In the sample roster, staff 1-16 occupy rows 6-21 of `13Aprto10May`.
The four weeks use these columns:

| Week | Priority | Seven daily shifts | Hours |
| --- | --- | --- | --- |
| 1 | C | D:J | K |
| 2 | N | O:U | V |
| 3 | Y | Z:AF | AG |
| 4 | AJ | AK:AQ | AR |

For example, `D6` is staff 1 on Day 1, `Z6` is staff 1 on Day 15, and
`AQ21` is staff 16 on Day 28. Optimization uses this uploaded grid as its
baseline; no separate weekly pattern workbook is needed.

A `lastRosterRD` worksheet is also required: `B2:B17` holds the previous
rest-day dates for roster rows 6-21, in order. Dates must be before Day 1.

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

### CP-SAT roster repair

`POST /optimize-roster` accepts one uploaded 28-day roster. Enter leave as
`VL`, `VLOFF`, or `VLRD` in that workbook. The solver repairs coverage, hours,
rest and night sequences directly from the uploaded shifts; it does not infer
original duties from a rotation or a second workbook. Staff 16 keeps the
uploaded schedule. The same workbook must contain `lastRosterRD` history.

| Field | Required | Description |
| --- | --- | --- |
| `file` | Yes | Complete 16-staff, 28-day roster with leave and a `lastRosterRD` sheet |
| `start_date` | Yes | Roster Day 1, which must be a Monday (`YYYY-MM-DD`) |
| `public_holidays` | No | Repeated or comma-separated roster days or ISO dates |
| `worksheet_name` | No | Roster sheet; defaults to the first sheet other than `lastRosterRD` |
| `max_time_seconds` | No | Solver limit, 60 seconds by default (maximum 120) |

```powershell
curl.exe -X POST http://localhost:8000/optimize-roster `
  -F "file=@C:\path\to\roster_with_vl.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" `
  -F "start_date=2026-04-13" `
  -F "public_holidays=2026-05-01" `
  -F "worksheet_name=13Aprto10May" `
  -o optimized_roster.xlsx
```

All roster and individual constraints remain hard requirements, including
160 hours per person, weekly rest days, RD spacing, night sequences, daily
coverage, and exactly one `+` and one `++` per day. Leave cells remain leave;
`VL`, `VLOFF` and `VLRD` may be exchanged to satisfy those requirements.
Special leave and OC entries remain fixed, and the solver does not invent
leave, OC, PH or XO cells to repair hours.

Weekly priority scores in C/N/Y/AJ are read from the uploaded roster. Scores
may be blank; supplied scores must be unique integers from 1 to 6 per week.
The solver first minimizes unscored duty cover, then the total priority score
of new duty cover, then penalized changes. This preserves priorities ahead of
change minimization. Unscored day-duty cover from a resting status must
originate from OFF/RD rather than NO. Existing working day duties may be
rearranged while satisfying coverage.

The following conversions have **zero change cost**, in either direction:

| Equivalent codes | Cost |
| --- | --- |
| `VL`, `VLOFF`, `VLRD` | 0 |
| `OFF`, `RD`, including their marker variants | 0 |
| `NO`, `NO+`, `NO++` | 0 |
| `Z`, `Y`, `Z1` | 0 |

Every other shift change costs one per cell. Adding, removing or switching
`+` and `++` never adds change cost. After duties and base statuses are settled,
a marker-only pass prefers OFF, then RD, then NO subject to individual rules.
These free conversions may change many displayed cells even when the
penalized change count is zero; literal edit count is not an objective.

The response downloads an audited `.xlsx` copy, preserves layout and
`lastRosterRD`, and refreshes numeric weekly hours. Its `Change Log` sheet replaces
any existing sheet of that name and lists each changed shift cell against the
upload, including base, marker and penalized-cost changes and the three totals.
`X-Roster-Penalized-Changes` reports the penalized change count.
`X-Roster-Cell-Edits` reports all
changed shift cells, including free conversions and markers.
`X-Roster-Plus-Changes` counts cells whose trailing marker changed; a cell can
contribute to multiple counts. Python callers can use `penalized_change_count`,
`cell_edit_count`, and `plus_change_count`.
`X-Roster-Status` is `OPTIMAL` when the first solve's objective was proved
optimal, or `FEASIBLE` for a valid candidate without that proof. The marker
pass must prove its preference optimum. Fallback cover is returned only when
the first objective is proved optimal. HTTP 409 returns no workbook when no
acceptable audited candidate was found within the constraints or time limit.

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

Policy definitions live in `backend/src/roster_audit/individual_policy.py`,
`rest_day_policy.py`, `daily_policy.py`, and `optimization_policy.py`. The
audit and optimizer interpret the shared roster rules separately. Update the
corresponding policy and agreement tests whenever a rule changes.
