import {
  ArrowRight,
  CheckCircle2,
  Download,
  LoaderCircle,
  Sparkles,
  WandSparkles,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
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
  busy,
  error,
  run,
}: {
  optimized: Optimization | null
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
                Find a valid revised schedule from your uploaded shifts. You can
                run optimization without an audit first.
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
                • A complete 16-staff, 28-day roster with leave entered as VL,
                VLOFF or VLRD.
              </li>
              <li>
                • A lastRosterRD sheet with previous rest dates for each staff
                member.
              </li>
              <li>
                • A Monday start date. Staff 16 keeps the uploaded schedule.
              </li>
            </ul>
          </div>
          <Button className="mt-6 h-10 px-4" onClick={run} disabled={busy}>
            {busy ? <LoaderCircle className="animate-spin" /> : <Sparkles />}{" "}
            {busy
              ? "Optimizing… this can take up to a minute"
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
