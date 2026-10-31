import type { Dispatch, SetStateAction } from "react"
import {
  ArrowRight,
  ClipboardCheck,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { TabsContent } from "@/components/ui/tabs"
import { ErrorMessage } from "@/components/web/error-message"
import { StepResults } from "@/components/web/step-results"
import type { AuditResponse } from "@/lib/schema/audit-api"

type Props = {
  staff: number
  setStaff: Dispatch<SetStateAction<number>>
  resetResults: () => void
  audit: AuditResponse | null
  busy: boolean
  error: string
  run: () => Promise<void>
}
export function AuditPanel({
  staff,
  setStaff,
  resetResults,
  audit,
  busy,
  error,
  run,
}: Props) {
  return (
    <TabsContent value="audit">
      <Card className="rounded-t-none py-0">
        <CardContent className="p-6 sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <Badge variant="secondary" className="mb-3">
                FOUR-WEEK REVIEW
              </Badge>
              <h3 className="text-2xl font-semibold tracking-tight">
                Audit your roster
              </h3>
              <p className="mt-2 max-w-xl text-sm leading-6 text-muted-foreground">
                Check shifts, coverage, working hours and rest-day rules across
                all 28 days.
              </p>
            </div>
            <div className="rounded-xl bg-primary/10 p-3 text-primary">
              <ClipboardCheck className="size-5" />
            </div>
          </div>
          <div className="mt-7 flex flex-wrap items-end gap-4 rounded-xl border bg-muted/30 p-4">
            <div className="space-y-2">
              <label htmlFor="staff" className="text-sm font-medium">
                Staff count
              </label>
              <Input
                id="staff"
                type="number"
                disabled={busy}
                min="1"
                max="30"
                className="w-28 bg-background"
                value={staff || ""}
                onChange={(e) => {
                  setStaff(Number(e.target.value))
                  resetResults()
                }}
              />
            </div>
            <p className="pb-2 text-xs text-muted-foreground">
              Audit supports 1–30 staff.
            </p>
          </div>
          <Button className="mt-6 h-10 px-4" onClick={run} disabled={busy}>
            {busy ? <LoaderCircle className="animate-spin" /> : <ShieldCheck />}{" "}
            {busy ? "Running audit…" : "Run audit"} {!busy && <ArrowRight />}
          </Button>
          {error && <ErrorMessage message={error} />}
          {audit && <StepResults result={audit} onReaudit={run} />}
        </CardContent>
      </Card>
    </TabsContent>
  )
}
