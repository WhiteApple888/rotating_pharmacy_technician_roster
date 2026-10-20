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
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { auditIssues } from "./roster-audit-data"
import type { IssueKind } from "./roster-audit-types"

export function StepResults({ onReaudit }: { onReaudit: () => void }) {
  const [filter, setFilter] = useState<"all" | IssueKind>("all")
  const visibleIssues = auditIssues.filter(
    (issue) => filter === "all" || issue.type === filter
  )
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
        variant="destructive"
        className="border-0 bg-destructive/[0.08] px-5 py-4 text-destructive ring-1 ring-destructive/15"
      >
        <AlertCircle className="size-5" />
        <AlertTitle className="text-base">
          Audit Failed · 7 Issues Detected
        </AlertTitle>
        <AlertDescription className="mt-1 text-destructive/80">
          Review the exceptions found in sheet{" "}
          <span className="font-semibold">Roster</span> before publishing this
          roster.
        </AlertDescription>
      </Alert>
      <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
        <CardHeader className="border-b px-6 py-5 sm:px-7">
          <Tabs
            value={filter}
            onValueChange={(value) => setFilter(value as "all" | IssueKind)}
          >
            <TabsList className="w-full justify-start overflow-x-auto sm:w-auto">
              <TabsTrigger value="all">All Issues (7)</TabsTrigger>
              <TabsTrigger value="coverage">Coverage (3)</TabsTrigger>
              <TabsTrigger value="rest">Rest-Day (4)</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent className="px-6 py-2 sm:px-7">
          <Accordion>
            {visibleIssues.map((issue) => (
              <AccordionItem key={issue.id} value={issue.id}>
                <AccordionTrigger className="py-4 no-underline hover:no-underline">
                  <div className="flex min-w-0 flex-1 flex-col items-start gap-2 pr-4 sm:flex-row sm:items-center">
                    <Badge variant="destructive" className="capitalize">
                      {issue.type === "rest" ? "Rest-Day" : "Coverage"}
                    </Badge>
                    <Badge variant="secondary" className="font-normal">
                      {issue.location}
                    </Badge>
                    <span className="truncate text-sm font-medium">
                      {issue.staff}
                    </span>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="pb-5">
                  <div className="grid gap-4 rounded-xl bg-muted/60 p-4 text-sm sm:grid-cols-2">
                    <div>
                      <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                        Violation
                      </p>
                      <p>{issue.violation}</p>
                    </div>
                    <div>
                      <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                        Rule Violated
                      </p>
                      <p>{issue.rule}</p>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>
    </div>
  )
}
