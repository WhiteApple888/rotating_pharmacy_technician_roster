"use client"
import { useState } from "react"
import { format } from "date-fns"
import { ClipboardCheck, FileSpreadsheet, WandSparkles } from "lucide-react"
import { runAudit } from "@/app/actions"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StepUpload } from "@/components/web/step-upload"
import { SharedSetup } from "@/components/web/shared-setup"
import { AuditPanel } from "@/components/web/audit-panel"
import {
  OptimizationPanel,
  type Optimization,
} from "@/components/web/optimization-panel"
import type { AuditResponse } from "@/lib/schema/audit-api"

export function RosterDashboard() {
  const [file, setFile] = useState<File | null>(null)
  const [sheets, setSheets] = useState<string[]>([])
  const [sheet, setSheet] = useState("")
  const [start, setStart] = useState(format(new Date(), "yyyy-MM-dd"))
  const [holidays, setHolidays] = useState<Date[]>([])
  const [staff, setStaff] = useState(16)
  const [timeLimit, setTimeLimit] = useState("60")
  const [fixedStaff, setFixedStaff] = useState("")
  const [restrictions, setRestrictions] = useState<
    { staff: string; codes: string }[]
  >([])
  const [audit, setAudit] = useState<AuditResponse | null>(null)
  const [optimized, setOptimized] = useState<Optimization | null>(null)
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [tab, setTab] = useState("audit")
  const [changingFile, setChangingFile] = useState(false)

  function resetResults() {
    setAudit(null)
    setOptimized((previous) => {
      if (previous) URL.revokeObjectURL(previous.url)
      return null
    })
    setError("")
  }
  const holidayDates = holidays.map((date) => format(date, "yyyy-MM-dd"))
  async function run() {
    if (!file) return
    setError("")
    if (!start) {
      setError("Choose a roster start date, then try again.")
      return
    }
    if (!Number.isInteger(staff) || staff < 1 || staff > 30) {
      setError("Enter a staff count between 1 and 30, then try again.")
      return
    }
    let fixed: number[] = []
    const forbidden: Record<string, string[]> = {}
    if (tab === "optimization") {
      const seconds = Number(timeLimit)
      if (
        !timeLimit.trim() ||
        !Number.isFinite(seconds) ||
        seconds <= 0 ||
        seconds > 120
      ) {
        setError(
          "Enter a solver time limit greater than 0 and no more than 120 seconds."
        )
        return
      }
      const fixedEntries = fixedStaff.trim()
        ? fixedStaff.split(",").map((entry) => entry.trim())
        : []
      if (
        fixedEntries.some(
          (entry) =>
            !/^\d+$/.test(entry) || Number(entry) < 1 || Number(entry) > staff
        )
      ) {
        setError(
          `Enter fixed staff numbers between 1 and ${staff}, separated by commas.`
        )
        return
      }
      fixed = [...new Set(fixedEntries.map(Number))]
      const validCodes = new Set([
        "XE1",
        "XO",
        "Z1",
        "Z",
        "Y",
        "PH",
        "VL",
        "OC",
        "D",
        "P",
        "W",
        "XE",
        "VL(TO4H)",
        "RD",
        "RD+",
        "RD++",
        "VLRD",
        "VLOFF",
        "VLPH",
        "OFF",
        "OFF+",
        "OFF++",
        "NO",
        "NO+",
        "NO++",
      ])
      for (const restriction of restrictions) {
        const number = restriction.staff.trim()
        const codes = restriction.codes
          .split(",")
          .map((code) => code.trim().toUpperCase())
        if (
          !/^\d+$/.test(number) ||
          Number(number) < 1 ||
          Number(number) > staff ||
          codes.some((code) => !validCodes.has(code))
        ) {
          setError(
            `For each restriction, enter a staff number between 1 and ${staff} and valid shift codes separated by commas.`
          )
          return
        }
        const key = String(Number(number))
        forbidden[key] = [...new Set([...(forbidden[key] ?? []), ...codes])]
      }
    }
    setBusy(true)
    try {
      if (tab === "audit") {
        setAudit(null)
        const response = await runAudit(file, {
          worksheetName: sheet,
          startDate: start,
          publicHolidays: holidayDates,
          staffCount: staff,
        })
        if (!response.ok)
          setError(
            `${response.error} Check your workbook and settings, then try again.`
          )
        else setAudit(response.result)
      } else {
        setOptimized((previous) => {
          if (previous) URL.revokeObjectURL(previous.url)
          return null
        })
        const data = new FormData()
        data.append("file", file)
        data.append("worksheet_name", sheet)
        data.append("start_date", start)
        data.append("num_staff", String(staff))
        data.append("max_time_seconds", timeLimit)
        data.append("fixed_staff", JSON.stringify(fixed))
        data.append("shift_restrictions", JSON.stringify(forbidden))
        holidayDates.forEach((date) => data.append("public_holidays", date))
        const response = await fetch("/api/optimize", {
          method: "POST",
          body: data,
        })
        if (!response.ok) {
          const payload = await response.json().catch(() => null)
          setError(
            `${payload?.error?.message ?? "The optimizer could not process this workbook."} Check the workbook requirements and settings, then try again.`
          )
        } else {
          setOptimized({
            url: URL.createObjectURL(await response.blob()),
            status: response.headers.get("x-roster-status"),
            penalized: response.headers.get("x-roster-penalized-changes"),
            edits: response.headers.get("x-roster-cell-edits"),
            markers: response.headers.get("x-roster-plus-changes"),
          })
        }
      }
    } catch {
      setError(
        "Something went wrong while processing the workbook. Check that the service is running and try again."
      )
    } finally {
      setBusy(false)
    }
  }
  return (
    <section id="workspace" className="border-t bg-muted/40 py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-5 sm:px-8">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold tracking-[0.16em] text-primary uppercase">
              Your workspace
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight">
              RPT Roster Dashboard
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              One workbook, two ways to work with it.
            </p>
          </div>
          <Badge variant="outline" className="px-3 py-1.5">
            <FileSpreadsheet className="mr-1 size-3.5" />{" "}
            {file ? "Workbook ready" : "No workbook selected"}
          </Badge>
        </div>
        {!file || changingFile ? (
          <div className="mx-auto max-w-3xl">
            <StepUpload
              onConfirm={(nextFile, names) => {
                resetResults()
                setFile(nextFile)
                setSheets(names)
                setSheet(
                  names.find(
                    (name) =>
                      name.toLowerCase() !== "lastroster rd" &&
                      name.toLowerCase() !== "lastrosterrd"
                  ) ?? names[0]
                )
                setChangingFile(false)
              }}
            />
            {file && (
              <Button
                variant="ghost"
                className="mt-3"
                onClick={() => setChangingFile(false)}
              >
                Cancel changing workbook
              </Button>
            )}
          </div>
        ) : (
          <div className="grid items-start gap-6 lg:grid-cols-[340px_1fr]">
            <SharedSetup
              file={file}
              sheets={sheets}
              sheet={sheet}
              start={start}
              holidays={holidays}
              busy={busy}
              setSheet={setSheet}
              setStart={setStart}
              setHolidays={setHolidays}
              setChangingFile={setChangingFile}
              resetResults={resetResults}
            />
            <Tabs
              value={tab}
              onValueChange={(value) => {
                setTab(value)
                setError("")
              }}
              className="gap-0"
            >
              <TabsList className="h-12 w-full justify-start rounded-b-none border bg-card p-1">
                <TabsTrigger disabled={busy} className="max-w-44" value="audit">
                  <ClipboardCheck /> Audit
                </TabsTrigger>
                <TabsTrigger
                  disabled={busy}
                  className="max-w-44"
                  value="optimization"
                >
                  <WandSparkles /> Optimization
                </TabsTrigger>
              </TabsList>
              <AuditPanel
                staff={staff}
                setStaff={setStaff}
                resetResults={resetResults}
                audit={audit}
                busy={busy}
                error={error}
                run={run}
              />
              <OptimizationPanel
                optimized={optimized}
                staff={staff}
                timeLimit={timeLimit}
                fixedStaff={fixedStaff}
                restrictions={restrictions}
                setStaff={setStaff}
                setTimeLimit={setTimeLimit}
                setFixedStaff={setFixedStaff}
                setRestrictions={setRestrictions}
                resetResults={resetResults}
                busy={busy}
                error={error}
                run={run}
              />
            </Tabs>
          </div>
        )}
      </div>
    </section>
  )
}
