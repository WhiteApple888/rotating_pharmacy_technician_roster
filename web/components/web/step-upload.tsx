"use client"

import { useRef, useState, type DragEvent } from "react"
import {
  DataSheetGrid,
  createTextColumn,
  keyColumn,
} from "react-datasheet-grid"
import * as XLSX from "xlsx"
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FileSpreadsheet,
  LoaderCircle,
  Table,
  UploadCloud,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"

type SpreadsheetRow = Record<string, string>
type Source = "upload" | "grid"

// The supplied roster uses columns A:BT (72 columns). Leave room for
// more columns so a complete worksheet can be pasted without truncation.
const GRID_COLUMN_COUNT = 100
const spreadsheetKeys = Array.from(
  { length: GRID_COLUMN_COUNT },
  (_, index) => `column${index + 1}`
)
const excelColumnLabel = (index: number) => {
  let value = index + 1
  let label = ""
  while (value > 0) {
    value -= 1
    label = String.fromCharCode(65 + (value % 26)) + label
    value = Math.floor(value / 26)
  }
  return label
}
const emptySpreadsheetRow = (): SpreadsheetRow =>
  Object.fromEntries(spreadsheetKeys.map((key) => [key, ""]))
const initialRows = <T,>(createRow: () => T) =>
  Array.from({ length: 8 }, createRow)
const hasValues = (row: Record<string, unknown>) =>
  Object.values(row).some((value) => String(value ?? "").trim().length > 0)
const stringColumn = createTextColumn<string>({ deletedValue: "" })

/** Convert pasted DD/MM/YYYY or YYYY-MM-DD values into an Excel date serial. */
const excelDateSerial = (value: unknown) => {
  const text = String(value ?? "")
  const match = text
    .trim()
    .match(/^(?:(\d{1,2})\/(\d{1,2})\/(\d{4})|(\d{4})-(\d{1,2})-(\d{1,2}))$/)
  if (!match) return value ?? ""

  const [
    ,
    dayText,
    monthText,
    yearText,
    isoYearText,
    isoMonthText,
    isoDayText,
  ] = match
  const day = Number(dayText ?? isoDayText)
  const month = Number(monthText ?? isoMonthText)
  const year = Number(yearText ?? isoYearText)
  const timestamp = Date.UTC(year, month - 1, day)
  const parsed = new Date(timestamp)
  if (
    parsed.getUTCFullYear() !== year ||
    parsed.getUTCMonth() !== month - 1 ||
    parsed.getUTCDate() !== day
  )
    return value ?? ""

  return Math.round((timestamp - Date.UTC(1899, 11, 30)) / 86_400_000)
}

const spreadsheetColumns = spreadsheetKeys.map((key, index) => ({
  ...keyColumn<SpreadsheetRow>(key, stringColumn),
  title: excelColumnLabel(index),
  basis: 112,
  minWidth: 88,
}))

export function StepUpload({
  onConfirm,
}: {
  onConfirm: (file: File, worksheetNames: string[]) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [mode, setMode] = useState<"upload" | "grid">("upload")
  const [sheet, setSheet] = useState<"active" | "last">("active")
  const [stage, setStage] = useState<1 | 2>(1)
  const [activeRows, setActiveRows] = useState<SpreadsheetRow[]>(() =>
    initialRows(emptySpreadsheetRow)
  )
  const [lastRows, setLastRows] = useState<SpreadsheetRow[]>(() =>
    initialRows(emptySpreadsheetRow)
  )
  const [activeFile, setActiveFile] = useState<File | null>(null)
  const [source, setSource] = useState<Source | null>(null)
  const [worksheetNames, setWorksheetNames] = useState<string[]>([])
  const [rowCounts, setRowCounts] = useState({ active: 0, last: 0 })
  const [error, setError] = useState("")
  const [isDragging, setIsDragging] = useState(false)
  const [isParsing, setIsParsing] = useState(false)

  const gridCounts = {
    active: activeRows.filter(hasValues).length,
    last: lastRows.filter(hasValues).length,
  }

  const canProceed =
    mode === "upload"
      ? Boolean(activeFile)
      : gridCounts.active + gridCounts.last > 0

  const selectFile = async (file?: File) => {
    if (!file || isParsing) return
    const extension = file.name.split(".").pop()?.toLowerCase()
    if (extension !== "xlsx") {
      setError("Select an .xlsx spreadsheet.")
      return
    }
    setIsParsing(true)
    setError("")
    try {
      const workbook = XLSX.read(await file.arrayBuffer(), { type: "array" })
      const sheets = workbook.SheetNames
      if (!sheets.length)
        throw new Error("The spreadsheet does not contain a worksheet.")
      const counts = sheets.map(
        (name) =>
          XLSX.utils.sheet_to_json(workbook.Sheets[name], {
            header: 1,
            blankrows: false,
          }).length
      )
      setActiveFile(file)
      setWorksheetNames(sheets)
      setRowCounts({
        active: Math.max(0, (counts[0] ?? 0)),
        last: Math.max(0, (counts[1] ?? 0)),
      })
      setSource("upload")
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The spreadsheet could not be read."
      )
    } finally {
      setIsParsing(false)
    }
  }

  const buildGridFile = () => {
    const workbook = XLSX.utils.book_new()
    const activeData = activeRows.filter(hasValues)
    const lastData = lastRows.filter(hasValues)
    const toWorksheet = (
      rows: SpreadsheetRow[],
      normaliseRestDayDates = false
    ) =>
      XLSX.utils.aoa_to_sheet(
        rows.map((row, rowIndex) =>
          spreadsheetKeys.map((key, columnIndex) => {
            const value = row[key] ?? ""
            return normaliseRestDayDates && rowIndex > 0 && columnIndex === 1
              ? excelDateSerial(value)
              : value
          })
        )
      )
    XLSX.utils.book_append_sheet(
      workbook,
      toWorksheet(activeData),
      "Active Roster"
    )
    XLSX.utils.book_append_sheet(
      workbook,
      toWorksheet(lastData, true),
      "lastRosterRD"
    )
    const bytes = XLSX.write(workbook, { bookType: "xlsx", type: "array" })
    return new File([bytes], "roster_combined.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    })
  }

  const proceed = () => {
    if (!canProceed) return
    if (mode === "grid") {
      const file = buildGridFile()
      setActiveFile(file)
      setWorksheetNames(["Active Roster", "lastRosterRD"])
      setRowCounts(gridCounts)
      setSource("grid")
    }
    setStage(2)
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    selectFile(event.dataTransfer.files[0])
  }

  if (stage === 2 && activeFile && source) {
    return (
      <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
        <CardHeader className="border-b px-7 pt-7 sm:px-9">
          <div className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <CheckCircle2 className="size-6" />
          </div>
          <CardTitle className="mt-3 text-2xl tracking-tight">
            Review your roster input
          </CardTitle>
          <CardDescription>
            Confirm the file, source, worksheets and rows
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5 px-7 py-7 sm:px-9">
          <dl className="grid gap-3 text-sm sm:grid-cols-3">
            <Summary label="Active file" value={activeFile.name} />
            <Summary
              label="Source"
              value={source === "upload" ? "Uploaded file" : "Data grid entry"}
            />
            <Summary label="Worksheets" value={worksheetNames.join(", ")} />
          </dl>
          <div className="grid gap-3 sm:grid-cols-2">
            <RowCount label="Active Roster" count={rowCounts.active} />
            <RowCount label="Last Roster RD" count={rowCounts.last} />
          </div>
          <div className="flex flex-col-reverse justify-between gap-3 border-t pt-5 sm:flex-row">
            <Button variant="ghost" onClick={() => setStage(1)}>
              <ArrowLeft /> Back
            </Button>
            <Button
              size="lg"
              onClick={() => onConfirm(activeFile, worksheetNames)}
            >
              Confirm and continue <ArrowRight />
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
      <CardHeader className="px-7 pt-8 sm:px-10">
        <CardTitle className="text-2xl tracking-tight">
          Start a roster audit
        </CardTitle>
        <CardDescription>
          Upload a spreadsheet or paste roster data into a structured workbook.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-7 pb-8 sm:px-10">
        <Tabs
          value={mode}
          onValueChange={(value) => setMode(value as "upload" | "grid")}
        >
          <TabsList className="mb-5 grid h-11 w-full grid-cols-2">
            <TabsTrigger value="upload">
              <UploadCloud /> File upload
            </TabsTrigger>
            <TabsTrigger value="grid">
              <Table /> Data grid
            </TabsTrigger>
          </TabsList>
          <TabsContent value="upload">
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(event) =>
                event.key === "Enter" && inputRef.current?.click()
              }
              onDragEnter={(event) => {
                event.preventDefault()
                setIsDragging(true)
              }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={cn(
                "group flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 text-center transition-all",
                isDragging
                  ? "border-primary bg-primary/5"
                  : "border-border bg-muted/30 hover:border-primary/50 hover:bg-primary/[0.03]"
              )}
            >
              <div className="mb-5 flex size-16 items-center justify-center rounded-2xl bg-background text-primary shadow-sm ring-1 ring-border transition-transform group-hover:-translate-y-1">
                {isParsing ? (
                  <LoaderCircle className="size-8 animate-spin" />
                ) : (
                  <FileSpreadsheet className="size-8" />
                )}
              </div>
              <h2 className="text-lg font-semibold">
                {isParsing
                  ? "Reading your spreadsheet..."
                  : activeFile && source === "upload"
                    ? activeFile.name
                    : "Upload roster spreadsheet"}
              </h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Drag & drop an .xlsx file or click to browse
              </p>
              <input
                ref={inputRef}
                type="file"
                accept=".xlsx"
                className="sr-only"
                onChange={(event) => selectFile(event.target.files?.[0])}
              />
              <div className="mt-6 flex items-center gap-2 text-xs text-muted-foreground">
                {isParsing ? (
                  <LoaderCircle className="size-5 animate-spin" />
                ) : (
                  <UploadCloud className="size-5" />
                )}
                {isParsing
                  ? "Detecting worksheet names"
                  : "Excel files up to 10 MB"}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="grid" className="space-y-4">
            <Tabs
              value={sheet}
              onValueChange={(value) => setSheet(value as "active" | "last")}
            >
              <TabsList className="h-10">
                <TabsTrigger value="active">Active Roster</TabsTrigger>
                <TabsTrigger value="last">Last Roster RD</TabsTrigger>
              </TabsList>
              <TabsContent value="active" className="mt-3">
                <GridShell>
                  <DataSheetGrid
                    value={activeRows}
                    onChange={setActiveRows}
                    columns={spreadsheetColumns}
                    createRow={emptySpreadsheetRow}
                    autoAddRow
                    height={300}
                  />
                </GridShell>
              </TabsContent>
              <TabsContent value="last" className="mt-3">
                <GridShell>
                  <DataSheetGrid
                    value={lastRows}
                    onChange={setLastRows}
                    columns={spreadsheetColumns}
                    createRow={emptySpreadsheetRow}
                    autoAddRow
                    height={300}
                  />
                </GridShell>
              </TabsContent>
            </Tabs>
            <div className="py-2">
              <p className="text-xs text-muted-foreground my-1">
                Paste an entire worksheet directly from Excel or Google Sheets.
              </p>
              <p className="text-xs text-muted-foreground">
                New rows are created automatically. Max column limit: 100
              </p>
            </div>
          </TabsContent>
        </Tabs>
        {error ? (
          <p role="alert" className="mt-3 text-sm text-destructive">
            {error}
          </p>
        ) : null}
        <div className="mt-6 flex justify-end border-t pt-5">
          <Button size="lg" disabled={!canProceed} onClick={proceed}>
            Next <ArrowRight />
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function GridShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="roster-grid overflow-hidden rounded-xl border border-border">
      {children}
    </div>
  )
}
function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 truncate font-medium" title={value}>
        {value}
      </dd>
    </div>
  )
}
function RowCount({ label, count }: { label: string; count: number }) {
  return (
    <div className="rounded-lg border bg-muted/30 p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">
        {count}{" "}
        <span className="text-sm font-normal text-muted-foreground">rows</span>
      </p>
    </div>
  )
}
