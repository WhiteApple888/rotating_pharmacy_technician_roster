import type { AuditValues } from "@/app/schema/roster-audit-types"
import { format } from "date-fns"

export type AuditFailure = {
  category: string
  message: string
  staff_row: number | null
  day: number | null
  source_cell: string | null
  roster_date: string | null
}

export type AuditResponse = {
  status: "PASS" | "FAIL"
  passed: boolean
  failure_count: number
  worksheet: string
  failures: AuditFailure[]
}

type ApiError = { error?: { message?: string } }
const auditApiUrl = `${process.env.NEXT_PUBLIC_AUDIT_API_URL ?? "http://localhost:8000"}/rpt-roster`

export async function runAudit(
  file: File,
  values: AuditValues
): Promise<AuditResponse> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("start_date", format(values.startDate, "yyyy-MM-dd"))
  formData.append("num_staff", String(values.staffCount))
  formData.append("worksheet_name", values.worksheetName)
  values.publicHolidays?.forEach((date) =>
    formData.append("public_holidays", format(date, "yyyy-MM-dd"))
  )
  let response: Response
  try {
    response = await fetch(auditApiUrl, { method: "POST", body: formData })
  } catch {
    throw new Error(
      "Could not reach the audit service. Confirm that the FastAPI server is running."
    )
  }
  const payload = (await response.json().catch(() => null)) as
    AuditResponse | ApiError | null
  if (!response.ok)
    throw new Error(
      (payload as ApiError | null)?.error?.message ??
        "The audit service could not process this workbook."
    )
  return payload as AuditResponse
}
