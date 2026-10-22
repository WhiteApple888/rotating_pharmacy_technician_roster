"use client"

import { useState } from "react"
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
import { Card, CardHeader } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import type { AuditResponse } from "@/lib/schema/audit-api"
import { format, parseISO } from "date-fns"

type IssueFilter = "all" | "daily" | "individual"

const issueFilters: { value: IssueFilter; label: string }[] = [
  { value: "all", label: "All Issues" },
  { value: "daily", label: "Daily" },
  { value: "individual", label: "Individual Rows" },
]

export function StepResults({
  result,
  onReaudit,
}: {
  result: AuditResponse
  onReaudit: () => void
}) {
  // activeFilter tracks which tab or filter view is currently selected by the user.
  const [activeFilter, setActiveFilter] = useState<IssueFilter>("all")
  const filteredFailures = result.failures.filter((failure) => {
    if (activeFilter === "all") return true
    return activeFilter === "daily"
      ? failure.day !== null
      : failure.day === null
  })
  const issueCountLabel = `${filteredFailures.length} issue${filteredFailures.length === 1 ? "" : "s"}`

  return (
    <div className="space-y-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <h1 className="text-2xl font-semibold tracking-tight">Results</h1>
        <Button variant="outline" onClick={onReaudit}>
          <RefreshCw /> Re-audit File
        </Button>
      </div>
      <Alert
        variant={result.passed ? "success" : "destructive"}
        className="border-0 px-5 py-4 ring-1"
      >
        <AlertCircle className="size-8" />
        <AlertTitle className="text-xl">
          {result.passed
            ? "Audit passed"
            : `Audit failed · ${result.failure_count} issue${result.failure_count === 1 ? "" : "s"} detected`}
        </AlertTitle>
        <AlertDescription className="text-base mt-1">
          {result.passed
            ? "No issues were detected."
            : "Please review the detected issues before publishing this roster."}
        </AlertDescription>
      </Alert>
      <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
        <Tabs
          value={activeFilter}
          onValueChange={(value) => setActiveFilter(value as IssueFilter)}
          className="gap-0"
        >
          <CardHeader className="gap-3 border-b px-6 py-5 text-sm font-medium sm:px-7">
            <Badge 
            variant= {result.passed ? "success" : "destructive"}
            className="rounded-full px-3 py-4 text-sm font-semibold">
              {issueCountLabel}
            </Badge>
            <TabsList className="min-h-10  w-full justify-start gap-1 rounded-lg border border-zinc-200 bg-zinc-100 p-1 dark:border-zinc-800 dark:bg-zinc-950">
              {issueFilters.map((filter) => (
                <TabsTrigger
                  key={filter.value}
                  value={filter.value}
                  className="shrink-0 px-3 py-4 text-m font-extrabold transition-all duration-200 data-active:bg-background data-active:text-foreground dark:data-active:border-zinc-700 dark:data-active:bg-zinc-800"
                >
                  {filter.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </CardHeader>
          <TabsContent value={activeFilter} className="mt-0 px-6 py-2 sm:px-7">
            {filteredFailures.length === 0 ? (
              <div className="flex min-h-36 items-center justify-center rounded-lg border border-dashed border-zinc-300 bg-zinc-50/50 px-4 text-center text-sm text-muted-foreground dark:border-zinc-800 dark:bg-zinc-950/50">
                No issues found in this category
              </div>
            ) : (
              <Accordion multiple className="motion-safe:animate-in motion-safe:duration-200 motion-safe:fade-in-0">
                {filteredFailures.map((failure, index) => (
                  <AccordionItem
                    key={`${failure.category}-${index}`}
                    value={`failure-${index}`}
                  >
                    <AccordionTrigger className="py-4 no-underline hover:no-underline">
                      <div className="flex min-w-0 flex-1 flex-col items-start gap-4 pr-4 sm:flex-row sm:items-center">
                        
                        <Badge variant="secondary" className="font-normal">
                            {failure.day
                              ? `Day ${failure.day}`
                              : failure.staff_row
                                ? `Staff Row ${failure.staff_row}`
                                : "Roster"}
                        </Badge>
                        
                        <span className="truncate text-sm font-medium">
                          {failure.day !== null
                            ? failure.roster_date
                              ? <Badge variant="secondary" className="font-normal">
                                {format(parseISO(failure.roster_date), "dd-MM-yyyy")}
                              </Badge>
                              : ""
                            : ""}
                        </span>
                        <Badge variant="destructive">{failure.category}</Badge>

                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="pb-5">
                      <div className="grid gap-4 rounded-xl bg-muted/60 p-4 text-sm sm:grid-cols-2">
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
                        <div>
                          <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                            Violation
                          </p>
                          <p>{failure.message}</p>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  )
}
