# Roster audit backend

The FastAPI service and Python package for the pharmacy technician roster auditor.
See the repository-level README for local development, API, and deployment instructions.

`POST /optimize-roster` accepts one uploaded four-week roster, a Monday start
date, and public holidays. The workbook includes leave entries and the
`lastRosterRD` history sheet. No weekly pattern file is required. The solver
preserves leave dates, repairs all audit rules, and minimizes penalized changes
after honoring weekly takeover priorities. Leave variants, OFF/RD variants,
Z/Y/Z1 conversions and marker changes are free. It downloads an XLSX copy only
after the exported roster passes the audit. See the repository README for
fields, zero-cost groups, and response count headers.
