"use server"

import type { AuditResponse } from "@/lib/schema/audit-api"

type ApiError = { error?: { message?: string } }

export type AuditActionResult =
  | { ok: true; result: AuditResponse }
  | { ok: false; error: string }

/** Calendar-only values, serialized in the browser before calling this action. */
export type AuditRequestValues = {
  worksheetName: string
  startDate: string
  publicHolidays: string[]
  staffCount: number
}

const auditApiUrl = `${process.env.AUDIT_API_URL ?? process.env.NEXT_PUBLIC_AUDIT_API_URL ?? "http://localhost:8000"}/rpt-roster`

export async function runAudit(
  file: File,
  values: AuditRequestValues
): Promise<AuditActionResult> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("start_date", values.startDate)
  formData.append("num_staff", String(values.staffCount))
  formData.append("worksheet_name", values.worksheetName)
  values.publicHolidays.forEach((date) =>
    formData.append("public_holidays", date)
  )

  let response: Response
  try {
    response = await fetch(auditApiUrl, { method: "POST", body: formData })
  } catch {
    return {
      ok: false,
      error: "Could not reach the audit service. Please try again later.",
    }
  }

  const payload = (await response.json().catch(() => null)) as
    | AuditResponse
    | ApiError
    | null

  if (!response.ok) {
    return {
      ok: false,
      error:
        (payload as ApiError | null)?.error?.message ??
        "The audit service could not process this workbook.",
    }
  }

  return { ok: true, result: payload as AuditResponse }
}
