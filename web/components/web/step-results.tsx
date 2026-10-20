"use client"

import { AlertCircle, RefreshCw } from "lucide-react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import type { AuditResponse } from "@/lib/audit-api"

export function StepResults({
  result,
  onReaudit,
}: {
  result: AuditResponse
  onReaudit: () => void
}) {
  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-medium text-primary">Audit complete</p>
          <h1 className="text-2xl font-semibold tracking-tight">
            Roster validation results
          </h1>
        </div>
        <Button variant="outline" onClick={onReaudit}>
          <RefreshCw /> Re-audit File
        </Button>
      </div>
      <Alert
        variant={result.passed ? "default" : "destructive"}
        className="border-0 px-5 py-4 ring-1"
      >
        <AlertCircle className="size-5" />
        <AlertTitle className="text-base">
          {result.passed
            ? "Audit passed"
            : `Audit failed · ${result.failure_count} issue${result.failure_count === 1 ? "" : "s"} detected`}
        </AlertTitle>
        <AlertDescription className="mt-1">
          {result.passed
            ? "No audit exceptions were found."
            : "Review the exceptions before publishing this roster."}{" "}
          Sheet <span className="font-semibold">{result.worksheet}</span>.
        </AlertDescription>
      </Alert>
      <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
        <CardHeader className="border-b px-6 py-5 text-sm font-medium sm:px-7">
          {result.failure_count} issue{result.failure_count === 1 ? "" : "s"}
        </CardHeader>
        <CardContent className="px-6 py-2 sm:px-7">
          {result.passed ? (
            <p className="py-5 text-sm text-muted-foreground">
              This roster satisfies all configured audit rules.
            </p>
          ) : (
            <Accordion>
              {result.failures.map((failure, index) => (
                <AccordionItem
                  key={`${failure.category}-${index}`}
                  value={`failure-${index}`}
                >
                  <AccordionTrigger className="py-4 no-underline hover:no-underline">
                    <div className="flex min-w-0 flex-1 flex-col items-start gap-2 pr-4 sm:flex-row sm:items-center">
                      <Badge variant="destructive">{failure.category}</Badge>
                      <Badge variant="secondary" className="font-normal">
                        {failure.source_cell ??
                          (failure.day
                            ? `Day ${failure.day}`
                            : failure.staff_row
                              ? `Row ${failure.staff_row}`
                              : "Roster")}
                      </Badge>
                      <span className="truncate text-sm font-medium">
                        {failure.roster_date ?? "Audit exception"}
                      </span>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="pb-5">
                    <div className="grid gap-4 rounded-xl bg-muted/60 p-4 text-sm sm:grid-cols-2">
                      <div>
                        <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                          Violation
                        </p>
                        <p>{failure.message}</p>
                      </div>
                      <div>
                        <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                          Details
                        </p>
                        <p>
                          {[
                            failure.staff_row &&
                              `Staff row ${failure.staff_row}`,
                            failure.day && `Roster day ${failure.day}`,
                          ]
                            .filter(Boolean)
                            .join(" · ") || "No additional location details."}
                        </p>
                      </div>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
