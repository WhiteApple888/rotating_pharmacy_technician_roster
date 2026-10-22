"""Excel report output."""

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .individual_staff_constraints import AuditFailure, Roster


def write_report(report_path: Path, failures: list[AuditFailure], source: Path, roster: Roster, ph_days: set[int]) -> None:
    """Export audit results to a formatted Excel report."""
    failure_frame = pd.DataFrame(
        [asdict(failure) for failure in failures],
        columns=["category", "staff_row", "day", "roster_date", "source_cell", "message"],
    )
    summary = pd.DataFrame([{
        "status": "PASS" if failure_frame.empty else "FAIL",
        "source_file": str(source),
        "worksheet": roster.worksheet,
        "public_holiday_days": ", ".join(map(str, sorted(ph_days))) or "None",
        "broken_constraints": len(failure_frame),
    }])
    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        summary.to_excel(writer, index=False, sheet_name="Summary")
        failure_frame.to_excel(writer, index=False, sheet_name="Failures")
        for sheet in writer.book.worksheets:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for column_cells in sheet.columns:
                letter = column_cells[0].column_letter
                width = max(len(str(cell.value or "")) for cell in column_cells) + 2
                sheet.column_dimensions[letter].width = min(120, max(12, width))
