import type { Dispatch, SetStateAction } from "react"
import {
  ArrowRight,
  CheckCircle2,
  Download,
  LoaderCircle,
  Plus,
  Trash2,
  Sparkles,
  WandSparkles,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { TabsContent } from "@/components/ui/tabs"
import { ErrorMessage } from "@/components/web/error-message"

export type Optimization = {
  url: string
  status: string | null
  penalized: string | null
  edits: string | null
  markers: string | null
}

export function OptimizationPanel({
  optimized,
  staff,
  timeLimit,
  fixedStaff,
  restrictions,
  setStaff,
  setTimeLimit,
  setFixedStaff,
  setRestrictions,
  resetResults,
  busy,
  error,
  run,
}: {
  optimized: Optimization | null
  staff: number
  timeLimit: string
  fixedStaff: string
  restrictions: { staff: string; codes: string }[]
  setStaff: Dispatch<SetStateAction<number>>
  setTimeLimit: Dispatch<SetStateAction<string>>
  setFixedStaff: Dispatch<SetStateAction<string>>
  setRestrictions: Dispatch<SetStateAction<{ staff: string; codes: string }[]>>
  resetResults: () => void
  busy: boolean
  error: string
  run: () => Promise<void>
}) {
  return (
    <TabsContent value="optimization">
      <Card className="rounded-t-none py-0">
        <CardContent className="p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <Badge variant="secondary" className="mb-3">
                SOLVER-ASSISTED
              </Badge>
              <h3 className="text-2xl font-semibold tracking-tight">
                Optimize your roster
              </h3>
              <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
                Find a valid revised schedule from your uploaded shifts.
              </p>
            </div>
            <div className="rounded-xl bg-primary/10 p-3 text-primary">
              <WandSparkles className="size-5" />
            </div>
          </div>
          <div className="mt-7 rounded-xl border bg-muted/30 p-5">
            <h4 className="text-sm font-semibold">Before you run</h4>
            <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
              <li>
                • A complete 28-day roster with leave entered as VL, VLOFF or
                VLRD.
              </li>
              <li>
                • A lastRosterRD sheet with previous rest dates for each staff
                member.
              </li>
              <li>
                • Indicate any staff row(s) whose schedule(s) must stay fixed below.
              </li>
            </ul>
          </div>
          <div className="mt-6 flex flex-col gap-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="optimization-staff"
                  className="text-sm font-medium"
                >
                  Staff count
                </label>
                <Input
                  id="optimization-staff"
                  type="number"
                  min="1"
                  max="30"
                  step="1"
                  disabled={busy}
                  value={staff || ""}
                  onChange={(event) => {
                    setStaff(Number(event.target.value))
                    resetResults()
                  }}
                />
                <p className="text-xs text-muted-foreground">
                  Max: 30
                </p>
              </div>
              <div className="flex flex-col gap-2">
                <label htmlFor="solver-time" className="text-sm font-medium">
                  Solver time limit (seconds)
                </label>
                <Input
                  id="solver-time"
                  type="number"
                  min="0.1"
                  max="120"
                  step="any"
                  disabled={busy}
                  value={timeLimit}
                  onChange={(event) => {
                    setTimeLimit(event.target.value)
                    resetResults()
                  }}
                />
                <p className="text-xs text-muted-foreground">
                  Default: 60, Max: 120.
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <label htmlFor="fixed-staff" className="text-sm font-medium">
                Indicate any staff row(s) whose schedule must stay fixed{" "}
                <span className="font-normal text-muted-foreground">
                  (optional)
                </span>
              </label>
              <Input
                id="fixed-staff"
                placeholder="e.g. 1, 16"
                disabled={busy}
                value={fixedStaff}
                onChange={(event) => {
                  setFixedStaff(event.target.value)
                  resetResults()
                }}
              />
              <p className="text-xs leading-5 text-muted-foreground">
                 Uploaded shifts will stay unchanged. No staff are fixed by default.
              </p>
            </div>
            <fieldset className="flex flex-col gap-3">
              <legend className="text-sm font-medium">
                Shift restrictions{" "}
                <span className="font-normal text-muted-foreground">
                  (optional)
                </span>
              </legend>
              <p className="text-xs leading-5 text-muted-foreground">
                Prevent specific staff from receiving exact shift codes on any
                day. For example, OFF, OFF+ and OFF++ are separate codes.
              </p>
              {restrictions.map((restriction, index) => (
                <div key={index} className="flex flex-wrap items-end gap-3">
                  <div className="flex w-28 flex-col gap-2">
                    <label
                      htmlFor={`restriction-staff-${index}`}
                      className="text-xs font-medium"
                    >
                      Staff number
                    </label>
                    <Input
                      id={`restriction-staff-${index}`}
                      type="number"
                      min="1"
                      max={staff}
                      step="1"
                      disabled={busy}
                      value={restriction.staff}
                      onChange={(event) => {
                        const value = event.target.value
                        setRestrictions((rows) =>
                          rows.map((row, i) =>
                            i === index ? { ...row, staff: value } : row
                          )
                        )
                        resetResults()
                      }}
                    />
                  </div>
                  <div className="flex min-w-40 flex-1 flex-col gap-2">
                    <label
                      htmlFor={`restriction-codes-${index}`}
                      className="text-xs font-medium"
                    >
                      Forbidden codes
                    </label>
                    <Input
                      id={`restriction-codes-${index}`}
                      placeholder="e.g. D, OFF"
                      disabled={busy}
                      value={restriction.codes}
                      onChange={(event) => {
                        const value = event.target.value
                        setRestrictions((rows) =>
                          rows.map((row, i) =>
                            i === index ? { ...row, codes: value } : row
                          )
                        )
                        resetResults()
                      }}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    disabled={busy}
                    aria-label={`Remove restriction ${index + 1}`}
                    onClick={() => {
                      setRestrictions((rows) =>
                        rows.filter((_, i) => i !== index)
                      )
                      resetResults()
                    }}
                  >
                    <Trash2 />
                  </Button>
                </div>
              ))}
              <div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={busy}
                  onClick={() => {
                    setRestrictions((rows) => [
                      ...rows,
                      { staff: "", codes: "" },
                    ])
                    resetResults()
                  }}
                >
                  <Plus data-icon="inline-start" /> Add restriction
                </Button>
              </div>
              <p className="text-xs leading-5 text-muted-foreground">
                Codes: XE1, XO, Z1, Z, Y, PH, VL, OC, D, P, W, XE, VL(TO4H), RD,
                RD+, RD++, VLRD, VLOFF, VLPH, OFF, OFF+, OFF++, NO, NO+, NO++.
              </p>
            </fieldset>
          </div>
          <Button className="mt-6 h-10 px-4" onClick={run} disabled={busy}>
            {busy ? <LoaderCircle className="animate-spin" /> : <Sparkles />}{" "}
            {busy
              ? "Optimizing… this may take a few minutes"
              : "Run optimization"}{" "}
            {!busy && <ArrowRight />}
          </Button>
          {error && <ErrorMessage message={error} />}
          {optimized && (
            <div className="mt-7 space-y-4 border-t pt-6">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="size-5 text-primary" /> Optimized
                workbook ready
              </div>
              {optimized.status && (
                <p className="text-sm text-muted-foreground">
                  Solver status:{" "}
                  <span className="font-medium text-foreground">
                    {optimized.status}
                  </span>
                  {optimized.status === "FEASIBLE"
                    ? " — a valid schedule was found without proof of optimality."
                    : optimized.status === "OPTIMAL"
                      ? " — the solver proved its first objective optimal."
                      : ""}
                </p>
              )}
              <div className="grid gap-3 min-[400px]:grid-cols-2 sm:grid-cols-3">
                {[
                  ["Penalized changes", optimized.penalized],
                  ["Cell edits", optimized.edits],
                  ["Marker changes", optimized.markers],
                ]
                  .filter(([, value]) => value !== null)
                  .map(([label, value]) => (
                    <div key={label} className="rounded-lg border p-3">
                      <p className="text-xl font-semibold">{value}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {label}
                      </p>
                    </div>
                  ))}
              </div>
              <p className="text-xs leading-5 text-muted-foreground">
                Penalized changes count shift changes the solver tries to
                minimize; some conversions and marker changes are free. Cell
                edits count changed roster cells, and marker changes count
                changes to + or ++ markers. See the Change Log for details.
              </p>
              <Button
                nativeButton={false}
                render={
                  <a href={optimized.url} download="optimized_roster.xlsx" />
                }
              >
                <Download /> Download workbook
              </Button>
              <p className="text-xs leading-5 text-muted-foreground">
                The workbook includes a Change Log with details of the edits.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  )
}
