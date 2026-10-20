"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { format } from "date-fns"
import {
  CalendarDays,
  ChevronRight,
  FileSpreadsheet,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react"
import { Controller, useForm } from "react-hook-form"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  auditSchema,
  type AuditValues,
} from "../../app/schema/roster-audit-types"

type StepParametersProps = {
  fileName: string
  worksheetNames: string[]
  values: AuditValues
  onValuesChange: (values: AuditValues) => void
  onBack: () => void
  onAudit: (values: AuditValues) => Promise<void>
}

export function StepParameters({
  fileName,
  worksheetNames,
  values,
  onValuesChange,
  onBack,
  onAudit,
}: StepParametersProps) {
  const [isRunning, setIsRunning] = useState(false)
  const {
    control,
    formState: { errors },
    handleSubmit,
  } = useForm<AuditValues>({
    resolver: zodResolver(auditSchema),
    values,
  })
  const submit = async (submittedValues: AuditValues) => {
    onValuesChange(submittedValues)
    setIsRunning(true)
    try {
      await onAudit(submittedValues)
    } finally {
      setIsRunning(false)
    }
  }
  return (
    <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
      <CardHeader className="border-b px-7 pt-7 sm:px-9">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
          <div>
            <CardTitle className="text-2xl tracking-tight">
              Audit parameters
            </CardTitle>
            <CardDescription className="mt-1">
              Fine-tune how the roster should be checked.
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={onBack}>
            <RefreshCw /> Change File
          </Button>
        </div>
        <div className="mt-3 flex items-center gap-3 rounded-xl bg-muted/70 p-3 text-sm">
          <span className="flex size-8 items-center justify-center rounded-lg bg-background text-primary">
            <FileSpreadsheet className="size-4" />
          </span>
          <span>
            <span className="block text-xs text-muted-foreground">
              Selected spreadsheet
            </span>
            <span className="block max-w-64 truncate font-medium">
              {fileName}
            </span>
          </span>
        </div>
      </CardHeader>
      <CardContent className="px-7 py-7 sm:px-9">
        <form onSubmit={handleSubmit(submit)} className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <Controller
              control={control}
              name="worksheetName"
              render={({ field }) => (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Worksheet Name</label>
                  <Select
                    onValueChange={(value) => {
                      if (!value) return
                      field.onChange(value)
                      onValuesChange({ ...values, worksheetName: value })
                    }}
                    value={field.value}
                  >
                    <SelectTrigger aria-invalid={Boolean(errors.worksheetName)}>
                      <SelectValue placeholder="Select worksheet" />
                    </SelectTrigger>
                    <SelectContent>
                      {worksheetNames.map((worksheetName) => (
                        <SelectItem key={worksheetName} value={worksheetName}>
                          {worksheetName}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.worksheetName && (
                    <p className="text-xs text-destructive">
                      {errors.worksheetName.message}
                    </p>
                  )}
                </div>
              )}
            />
            <Controller
              control={control}
              name="startDate"
              render={({ field }) => (
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium">Start Date</label>
                  <Popover>
                    <PopoverTrigger
                      render={
                        <Button
                          variant="outline"
                          aria-invalid={Boolean(errors.startDate)}
                          className="justify-start text-left font-normal"
                        >
                          <CalendarDays />
                          {format(field.value, "dd MMM yyyy")}
                        </Button>
                      }
                    />
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={field.value}
                        onSelect={(date) => {
                          if (!date) return
                          field.onChange(date)
                          onValuesChange({ ...values, startDate: date })
                        }}
                      />
                    </PopoverContent>
                  </Popover>
                  {errors.startDate && (
                    <p className="text-xs text-destructive">
                      {errors.startDate.message}
                    </p>
                  )}
                </div>
              )}
            />
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <Controller
              control={control}
              name="publicHolidays"
              render={({ field }) => (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Public Holidays</label>
                  <Popover>
                    <PopoverTrigger
                      render={
                        <Button
                          type="button"
                          variant="outline"
                          className="w-full justify-start text-left font-normal"
                          aria-invalid={Boolean(errors.publicHolidays)}
                        >
                          <CalendarDays />
                          {field.value?.length
                            ? `${field.value.length} holiday${field.value.length === 1 ? "" : "s"} selected`
                            : "Select public holidays (optional)"}
                        </Button>
                      }
                    />
                    <PopoverContent className="w-auto p-3" align="start">
                      <div className="mb-2 flex items-center justify-between px-1">
                        <p className="text-sm font-medium">Public holidays</p>
                        {field.value?.length ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-muted-foreground"
                            onClick={() => {
                              field.onChange(null)
                              onValuesChange({
                                ...values,
                                publicHolidays: null,
                              })
                            }}
                          >
                            <X /> Clear
                          </Button>
                        ) : null}
                      </div>
                      <Calendar
                        mode="multiple"
                        selected={field.value ?? []}
                        onSelect={(dates) => {
                          const publicHolidays = dates?.length ? dates : null
                          field.onChange(publicHolidays)
                          onValuesChange({ ...values, publicHolidays })
                        }}
                      />
                    </PopoverContent>
                  </Popover>
                  <p className="text-xs text-muted-foreground">
                    Choose one or more dates, or leave this blank when none
                    apply.
                  </p>
                  {errors.publicHolidays && (
                    <p className="text-xs text-destructive">
                      {errors.publicHolidays.message}
                    </p>
                  )}
                </div>
              )}
            />
            <Controller
              control={control}
              name="staffCount"
              render={({ field }) => (
                <div className="space-y-2">
                  <label htmlFor="staffCount" className="text-sm font-medium">
                    Staff Count
                  </label>
                  <Input
                    id="staffCount"
                    type="number"
                    min={1}
                    aria-invalid={Boolean(errors.staffCount)}
                    value={field.value}
                    onChange={(event) => {
                      const staffCount = event.target.valueAsNumber
                      field.onChange(staffCount)
                      onValuesChange({ ...values, staffCount })
                    }}
                  />
                  <p className="text-xs text-muted-foreground">
                    Total technicians expected in the roster.
                  </p>
                  {errors.staffCount && (
                    <p className="text-xs text-destructive">
                      {errors.staffCount.message}
                    </p>
                  )}
                </div>
              )}
            />
          </div>
          <div className="flex justify-between border-t pt-6">
            <Button type="button" variant="ghost" onClick={onBack}>
              Back
            </Button>
            <Button type="submit" size="lg" disabled={isRunning}>
              {isRunning ? (
                <LoaderCircle className="animate-spin" />
              ) : (
                <ShieldCheck />
              )}
              {isRunning ? "Running audit..." : "Run Audit"}
              <ChevronRight />
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
