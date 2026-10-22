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
