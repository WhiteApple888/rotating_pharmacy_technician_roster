"use client"

import { useMemo, useState } from "react"
import {
  DataSheetGrid,
  createTextColumn,
  keyColumn,
} from "react-datasheet-grid"
import * as XLSX from "xlsx"
import { Clipboard, LoaderCircle, Table2, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

type SpreadsheetRow = Record<string, string>
type Worksheet = {
  name: string
  rows: SpreadsheetRow[]
  columnCount: number
}

// Optimizer output is display-only, so show only the columns that actually
// exist in each worksheet instead of adding the upload grid's empty columns.
const MAX_GRID_COLUMN_COUNT = 100
const spreadsheetKeys = (columnCount: number) =>
  Array.from({ length: columnCount }, (_, index) => `column${index + 1}`)
const readOnlyTextColumn = createTextColumn<string>()

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

const createSpreadsheetColumns = (columnCount: number) =>
  spreadsheetKeys(columnCount).map((key, index) => ({
    ...keyColumn<SpreadsheetRow>(key, readOnlyTextColumn),
    title: excelColumnLabel(index),
    basis: 112,
    minWidth: 88,
    disabled: true,
  }))

function toSpreadsheetRow(
  values: unknown[],
  columnCount: number
): SpreadsheetRow {
  return Object.fromEntries(
    spreadsheetKeys(columnCount).map((key, index) => [
      key,
      String(values[index] ?? ""),
    ])
  )
}

function OutputWorksheetGrid({ worksheet }: { worksheet: Worksheet }) {
  const columns = useMemo(
    () => createSpreadsheetColumns(worksheet.columnCount),
    [worksheet.columnCount]
  )

  return (
    <div className="roster-grid max-w-full min-w-0 overflow-hidden rounded-xl border border-border bg-background">
      <DataSheetGrid
        value={worksheet.rows}
        onChange={() => undefined}
        columns={columns}
        lockRows
        disableContextMenu
        disableExpandSelection
        disableSmartDelete
        height={420}
      />
    </div>
  )
}

export function OptimizationOutputGrid({ output }: { output: Blob }) {
  const [worksheets, setWorksheets] = useState<Worksheet[] | null>(null)
  const [activeSheet, setActiveSheet] = useState("0")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  const openGrid = async () => {
    setIsLoading(true)
    setError("")
    try {
      const workbook = XLSX.read(await output.arrayBuffer(), { type: "array" })
      const nextWorksheets = workbook.SheetNames.map((name) => {
        const rows = XLSX.utils.sheet_to_json<unknown[]>(
          workbook.Sheets[name],
          {
            header: 1,
            blankrows: false,
            defval: "",
            raw: false,
          }
        )
        const columnCount = Math.min(
          MAX_GRID_COLUMN_COUNT,
          Math.max(1, ...rows.map((row) => row.length))
        )
        return {
          name,
          rows: rows.map((row) => toSpreadsheetRow(row, columnCount)),
          columnCount,
        }
      })
      if (!nextWorksheets.length)
        throw new Error("The optimized workbook has no worksheets.")
      setWorksheets(nextWorksheets)
      setActiveSheet("0")
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The optimized workbook could not be displayed."
      )
    } finally {
      setIsLoading(false)
    }
  }

  if (!worksheets) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={openGrid}
          disabled={isLoading}
        >
          {isLoading ? (
            <LoaderCircle data-icon="inline-start" className="animate-spin" />
          ) : (
            <Table2 data-icon="inline-start" />
          )}
          {isLoading ? "Opening output…" : "View output in data grid"}
        </Button>
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    )
  }

  return (
    <section
      className="w-full rounded-xl border bg-muted/20 p-4 sm:p-5"
      aria-labelledby="output-grid-title"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Table2 className="size-4 text-primary" />
            <h4 id="output-grid-title" className="font-semibold">
              Optimizer output
            </h4>
          </div>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Select cells, then copy and paste them into a separate Excel
            workbook.
          </p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setWorksheets(null)}
        >
          <X data-icon="inline-start" /> Close grid
        </Button>
      </div>
      <Tabs
        value={activeSheet}
        onValueChange={setActiveSheet}
        className="mt-4 min-w-0 gap-3"
      >
        <TabsList className="max-w-full overflow-x-auto">
          {worksheets.map((worksheet, index) => (
            <TabsTrigger
              key={`${worksheet.name}-${index}`}
              value={String(index)}
              className="max-w-48 truncate"
            >
              {worksheet.name}
            </TabsTrigger>
          ))}
        </TabsList>
        {worksheets.map((worksheet, index) => (
          <TabsContent
            key={`${worksheet.name}-${index}`}
            value={String(index)}
            className="min-w-0"
          >
            <OutputWorksheetGrid worksheet={worksheet} />
          </TabsContent>
        ))}
      </Tabs>
      <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
        <Clipboard className="size-3.5" /> The grid is read-only and supports
        standard copy and paste selection.
      </p>
    </section>
  )
}
