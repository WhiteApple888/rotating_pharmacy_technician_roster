"use client"

import { useRef, useState, type DragEvent } from "react"
import {
  FileSpreadsheet,
  LoaderCircle,
  ShieldCheck,
  UploadCloud,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { getWorksheetNames } from "@/lib/workbook-sheets"

export function StepUpload({
  onFile,
}: {
  onFile: (file: File, worksheetNames: string[]) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isParsing, setIsParsing] = useState(false)
  const [error, setError] = useState("")
  const selectFile = async (file?: File) => {
    if (!file || isParsing) return
    setIsParsing(true)
    setError("")
    try {
      const worksheetNames = await getWorksheetNames(file)
      onFile(file, worksheetNames)
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "The workbook could not be read."
      )
    } finally {
      setIsParsing(false)
    }
  }
  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragging(false)
    selectFile(event.dataTransfer.files[0])
  }
  return (
    <Card className="border-0 shadow-xl ring-1 shadow-slate-200/60 ring-slate-200/70 dark:shadow-none">
      <CardHeader className="px-7 pt-8 text-center sm:px-10">
        <div className="mx-auto mb-2 flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <ShieldCheck className="size-6" />
        </div>
        <CardTitle className="text-2xl tracking-tight">
          Start a roster audit
        </CardTitle>
        <CardDescription>
          Upload your latest pharmacy roster to validate coverage and rest-day
          rules.
        </CardDescription>
      </CardHeader>
      <CardContent className="px-7 pb-8 sm:px-10">
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
            "group flex min-h-72 cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-6 text-center transition-all",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-slate-200 bg-slate-50/70 hover:border-primary/50 hover:bg-primary/[0.03] dark:border-white/10 dark:bg-white/[0.02]"
          )}
        >
          <div className="mb-5 flex size-16 items-center justify-center rounded-2xl bg-background text-primary shadow-sm ring-1 ring-slate-200 transition-transform group-hover:-translate-y-1">
            <FileSpreadsheet className="size-8" />
          </div>
          <h2 className="text-lg font-semibold">
            {isParsing
              ? "Reading your spreadsheet..."
              : "Upload Roster Spreadsheet"}
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
              <LoaderCircle className="size-3.5 animate-spin" />
            ) : (
              <UploadCloud className="size-3.5" />
            )}
            {isParsing
              ? "Detecting worksheet names"
              : "Excel files up to 10 MB"}
          </div>
          {error ? (
            <p className="mt-3 text-xs text-destructive">{error}</p>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
