"use client"

import { useState } from "react"
import { format, isValid, parse, parseISO } from "date-fns"
import { AlertCircle, CheckCircle2, RefreshCw } from "lucide-react"
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
import type { AuditFailure, AuditResponse } from "@/lib/schema/audit-api"

type IssueFilter = "all" | "daily" | "individual"
type Finding = { failure: AuditFailure; id: string }

export function StepResults({
  result,
  onReaudit,
}: {
  result: AuditResponse
  onReaudit: () => void
}) {
  const [filter, setFilter] = useState<IssueFilter>("all")
  const [openGroups, setOpenGroups] = useState<string[]>([])
  const findings = result.failures.map((failure, index) => ({
    failure,
    id: `finding-${index}`,
  }))
  // A staff row identifies individual findings even when they also refer to a day.
  const daily = findings.filter(
    ({ failure }) => failure.staff_row == null && failure.day != null
  )
  const individual = findings.filter(({ failure }) => failure.staff_row != null)
  const other = findings.filter(
    ({ failure }) => failure.staff_row == null && failure.day == null
  )
  const groups = Array.from({ length: 4 }, (_, index) => ({
    id: `week-${index + 1}`,
    label: `Week ${index + 1}`,
    findings: daily.filter(
      ({ failure }) =>
        failure.day != null &&
        failure.day >= index * 7 + 1 &&
        failure.day <= index * 7 + 7
    ),
  })).filter((group) => group.findings.length > 0)
  const undatedDaily = daily.filter(
    ({ failure }) =>
      failure.day != null && (failure.day < 1 || failure.day > 28)
  )
  if (undatedDaily.length)
    groups.push({
      id: "other-days",
      label: "Other days",
      findings: undatedDaily,
    })
  const visible =
    filter === "daily" ? daily : filter === "individual" ? individual : findings
  const visibleGroups = [
    ...(filter === "individual" ? [] : groups),
    ...(filter === "daily"
      ? []
      : Array.from(new Set(individual.map(({ failure }) => failure.staff_row)))
          .sort((a, b) => (a ?? 0) - (b ?? 0))
          .map((row) => ({
            id: `staff-${row}`,
            label: `Staff row ${row}`,
            findings: individual.filter(
              ({ failure }) => failure.staff_row === row
            ),
          }))),
    ...(filter === "all" && other.length
      ? [{ id: "roster", label: "Roster-wide", findings: other }]
      : []),
  ]
  const groupIds = visibleGroups.map(({ id }) => id)
  const allOpen = groupIds.every((id) => openGroups.includes(id))

  return (
    <div className="mt-8 space-y-5 border-t pt-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 className="text-xl font-semibold">Results</h4>
        <Button variant="outline" onClick={onReaudit}>
          <RefreshCw /> Re-audit file
        </Button>
      </div>
      <Alert
        variant={result.passed ? "success" : "destructive"}
        className={
          result.passed
            ? "border-emerald-500/50 px-5 py-4"
            : "border-destructive/50 px-5 py-4"
        }
      >
        {result.passed ? (
          <CheckCircle2 className="size-6" />
        ) : (
          <AlertCircle className="size-6" />
        )}
        <AlertTitle className="text-lg">
          {result.passed
            ? "Audit passed"
            : `Audit failed · ${result.failure_count} issue${result.failure_count === 1 ? "" : "s"} detected`}
        </AlertTitle>
        <AlertDescription className="mt-1">
          {result.passed
            ? "No issues were detected."
            : "Please review the detected issues before publishing this roster."}
        </AlertDescription>
      </Alert>
      <Card className="gap-0 py-0">
        <Tabs
          value={filter}
          onValueChange={(value) => {
            setFilter(value as IssueFilter)
            setOpenGroups([])
          }}
          className="gap-0"
        >
          <CardHeader className="gap-3 border-b p-5">
            <Badge
              variant={result.passed ? "success" : "destructive"}
              className="rounded-full px-3 py-1"
            >
              {visible.length} issue{visible.length === 1 ? "" : "s"}
            </Badge>
            <TabsList className="h-auto min-h-10 w-full border p-1">
              <TabsTrigger value="all" className="py-2">
                All Issues
              </TabsTrigger>
              <TabsTrigger value="daily" className="py-2">
                Daily
              </TabsTrigger>
              <TabsTrigger value="individual" className="py-2">
                Individual Rows
              </TabsTrigger>
            </TabsList>
          </CardHeader>
          <TabsContent value={filter} className="p-5">
            {visible.length === 0 ? (
              <div className="flex min-h-36 items-center justify-center rounded-lg border border-dashed bg-muted/30 px-4 text-center text-sm text-muted-foreground">
                No issues found in this category
              </div>
            ) : (
              <>
                <div className="flex justify-end gap-2 border-b pb-3">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={allOpen}
                    onClick={() => {
                      setOpenGroups(groupIds)
                    }}
                  >
                    Expand all
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={!groupIds.some((id) => openGroups.includes(id))}
                    onClick={() => {
                      setOpenGroups([])
                    }}
                  >
                    Collapse all
                  </Button>
                </div>
                <Accordion
                  multiple
                  value={openGroups}
                  onValueChange={setOpenGroups}
                >
                  {visibleGroups.map((group) => (
                    <AccordionItem key={group.id} value={group.id}>
                      <AccordionTrigger className="py-4 hover:no-underline">
                        <span className="flex min-w-0 flex-1 flex-wrap items-center justify-between gap-3 pr-3">
                          <span className="flex min-w-0 flex-wrap items-center gap-2">
                            <span className="mr-1 text-sm font-semibold">
                              {group.label}
                            </span>
                            {Array.from(
                              new Set(
                                group.findings.map(
                                  ({ failure }) => failure.category
                                )
                              )
                            ).map((category) => (
                              <Badge
                                key={category}
                                variant="destructive"
                                className="h-auto max-w-full text-left whitespace-normal"
                              >
                                {category}
                              </Badge>
                            ))}
                          </span>
                          <span className="shrink-0 text-xs text-muted-foreground">
                            {group.findings.length} issue
                            {group.findings.length === 1 ? "" : "s"}
                          </span>
                        </span>
                      </AccordionTrigger>
                      <AccordionContent>
                        <FindingList findings={group.findings} />
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </>
            )}
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  )
}

function FindingList({ findings }: { findings: Finding[] }) {
  return (
    <div className="rounded-lg border bg-muted/60 px-4">
      {findings.map(({ failure, id }) => {
        const message = displayMessage(failure)
        const date = failure.roster_date ? parseISO(failure.roster_date) : null
        const dateLabel =
          date && isValid(date)
            ? format(date, "d MMM yyyy")
            : failure.roster_date
        const summary = (
          <span className="flex min-w-0 flex-1 flex-col items-start gap-2 text-left">
            <span className="text-sm leading-6 font-medium text-muted-foreground">{message}</span>
            <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-normal text-muted-foreground">
              {failure.day != null &&
                !new RegExp(`\\bDay ${failure.day}\\b`, "i").test(message) && (
                  <span>Day {failure.day}</span>
                )}
              {dateLabel && !message.includes(dateLabel) && (
                <span>{dateLabel}</span>
              )}
              {failure.source_cell?.trim() && (
                <span>Source cell: {failure.source_cell}</span>
              )}
            </span>
          </span>
        )
        return (
          <div key={id} className="border-b py-3 last:border-0">
            {summary}
          </div>
        )
      })}
    </div>
  )
}

function displayMessage(failure: AuditFailure) {
  let message = failure.message.replace(/^Fail:\s*/i, "")
  if (failure.staff_row != null) {
    const prefix = new RegExp(`^Staff in Row ${failure.staff_row}\\s+`, "i")
    if (prefix.test(message)) {
      message = message.replace(prefix, "")
      message = message.charAt(0).toUpperCase() + message.slice(1)
    }
  }
  return message.replace(
    /\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b/g,
    (value) => {
      const date = parse(value, "d MMMM yyyy", new Date())
      return isValid(date) ? format(date, "d MMM yyyy") : value
    }
  )
}
