# Pharmacy technician roster auditor

Audit a fixed four-week pharmacy technician roster stored in Excel. The tool
checks 16 staff rows across 28 days, prints any rule failures, and writes an
Excel audit report. It only reads the source workbook; the original is never
modified.

The application is the `roster_audit` package under `src/` and requires Python
3.10 or later.

## Installation

From the repository root, create an environment if desired, then install the
project and its dependencies:

```powershell
python -m pip install -e .
```

## Usage

```powershell
roster-audit ROSTER.xlsx [--sheet SHEET] [--start_date YYYY-MM-DD] [--ph DAYS] [--report REPORT.xlsx]
```

| Argument | Description |
| --- | --- |
| `ROSTER.xlsx` | Required source workbook. It must be an `.xlsx` file. |
| `--sheet SHEET` | Worksheet to audit. Defaults to the active worksheet. |
| `--start_date YYYY-MM-DD` | Calendar date for roster Day 1. Required for `lastRosterRD`, rest-day-spacing, and ISO public-holiday validation. |
| `--ph DAYS` | Public-holiday roster days or ISO dates. Accepts comma-separated values and can be repeated. |
| `--report REPORT.xlsx` | Destination for the audit workbook. Defaults to `<source-name>_audit.xlsx` beside the source file. |

The command exits with status `0` when the roster passes and `1` when one or
more constraints fail. In both cases, an audit report is written unless an
input or file error prevents it.

## Sample

Audit the included roster, treating roster Day 1 as a public holiday and
writing the results to `roster_audit.xlsx`:

```powershell
roster-audit .\13Apr-10May_26.xlsx --start_date 2026-04-13 --ph 1 --report .\roster_audit.xlsx
```

Public holidays can also be supplied as ISO dates. The following command uses
13 April 2026 as roster Day 1 and marks both Day 5 and Day 12 as public
holidays:

```powershell
roster-audit .\13Apr-10May_26.xlsx --start_date 2026-04-13 --ph 2026-04-17,12
```

Example console output:

```text
STATUS: FAIL
Fail: Staff in Row 6 worked 156 hours across the 4-week period; required 160.
Audit report: roster_audit.xlsx
```

The report contains a `Summary` sheet with the result and input details, and a
`Failures` sheet listing each broken constraint. A passing roster prints
`STATUS: PASS` and has no rows in `Failures`.

## Rest-day history checks

The source workbook must contain a `lastRosterRD` sheet. Cells `B2:B17` map,
in order, to roster staff rows `6:21`; each cell must contain an Excel date
strictly before roster Day 1. The auditor uses each staff member's historical
RD to check the Day 1 boundary. It also checks rest-day gaps within the roster
and work stretches of 12 or more days that continue to roster Day 28.

Rest-day-spacing and daily-coverage failures include roster dates whenever
`--start_date` is provided. The Excel report's `Failures` sheet includes a
`roster_date` column alongside the staff row and roster day for easier review.

## Repository layout

| Path | Purpose |
| --- | --- |
| `src/roster_audit/individual_staff_constraints.py` | Domain types and staff-level audit constraints. |
| `src/roster_audit/daily_constraints.py` | Daily coverage policy tables and audit rules. |
| `src/roster_audit/workbook.py`, `report.py` | Excel input and audit-report output. |
| `src/roster_audit/service.py`, `cli.py` | Audit workflow and command-line interface. |
| `tests/` | Fast unit tests for parsing and audit policy behaviour. |
| `pyproject.toml` | Dependency and command-line entry-point configuration. |
| `*.xlsx` | Example source roster and locally generated reports. |

## Policy changes

`individual_staff_constraints.py` is the single source of truth for shift
codes, hours, rest days, and staff-level rules. `daily_constraints.py` contains
the `NORMAL_COVERAGE_RULES` and `PH_COVERAGE_RULES` tables for daily coverage.
Add or update a focused test whenever a policy changes.

## Verification

After installing the project, run the test suite with the standard library:

```powershell
python -m unittest discover -s tests -v
```

If you have not installed the project in the active environment, run the same
command with `PYTHONPATH` pointed at `src`:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```
