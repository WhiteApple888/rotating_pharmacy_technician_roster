import { z } from "zod"

export const auditSchema = z.object({
  worksheetName: z.string().min(1, "Choose a worksheet."),
  startDate: z.date({ error: "Choose a start date." }),
  publicHolidays: z.array(z.date()).nullable(),
  staffCount: z.number("Please enter a valid whole number.").int("Please enter a valid whole number.").min(1, "Enter at least one staff member."),
})

export type AuditValues = z.infer<typeof auditSchema>
export type AuditStep = 1 | 2 | 3
export type IssueKind = "coverage" | "rest"

export type AuditIssue = {
  id: string
  type: IssueKind
  location: string
  staff: string
  violation: string
  rule: string
}
