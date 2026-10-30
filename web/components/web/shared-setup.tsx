import { useState, type Dispatch, type SetStateAction } from "react"
import { format, parseISO } from "date-fns"
import { CalendarDays, FileSpreadsheet, Settings2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Calendar } from "@/components/ui/calendar"
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

type Props = {
  file: File
  sheets: string[]
  sheet: string
  start: string
  holidays: Date[]
  busy: boolean
  setSheet: Dispatch<SetStateAction<string>>
  setStart: Dispatch<SetStateAction<string>>
  setHolidays: Dispatch<SetStateAction<Date[]>>
  setChangingFile: Dispatch<SetStateAction<boolean>>
  resetResults: () => void
}
export function SharedSetup({
  file,
  sheets,
  sheet,
  start,
  holidays,
  busy,
  setSheet,
  setStart,
  setHolidays,
  setChangingFile,
  resetResults,
}: Props) {
  const [startCalendarOpen, setStartCalendarOpen] = useState(false)
  const CURRENT_YEAR = new Date().getFullYear()
  const START_MONTH = new Date(CURRENT_YEAR - 5, 0)
  const END_MONTH = new Date(CURRENT_YEAR + 5, 11)
  return (
    <Card className="gap-0 py-0">
      <div className="border-b p-6">
        <div className="flex items-center gap-2">
          <Settings2 className="size-4 text-primary" />
          <h3 className="font-semibold">Shared setup</h3>
        </div>
        <p className="mt-2 text-xs leading-5 text-muted-foreground">
          These settings apply to both audit and optimization.
        </p>
      </div>
      <CardContent className="space-y-5 p-6">
        <div className="rounded-lg border bg-muted/50 p-3">
          <div className="flex items-start gap-3">
            <FileSpreadsheet className="mt-0.5 size-4 shrink-0 text-primary" />
            <div className="min-w-0">
              <p className="text-xs text-muted-foreground">Workbook</p>
              <p className="truncate text-sm font-medium" title={file.name}>
                {file.name}
              </p>
            </div>
          </div>
          <Button
            variant="link"
            className="mt-2 h-auto p-0 text-xs"
            disabled={busy}
            onClick={() => setChangingFile(true)}
          >
            Change workbook
          </Button>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium" id="worksheet-label">
            Worksheet
          </label>
          <Select
            disabled={busy}
            value={sheet}
            onValueChange={(value) => {
              if (value) {
                setSheet(value)
                resetResults()
              }
            }}
          >
            <SelectTrigger aria-labelledby="worksheet-label" className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {sheets.map((name) => (
                <SelectItem key={name} value={name}>
                  {name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label id="start-label" className="text-sm font-medium">
            Roster start date
          </label>
          <Popover open={startCalendarOpen} onOpenChange={setStartCalendarOpen}>
            <PopoverTrigger
              render={
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  aria-labelledby="start-label start-value"
                  className="w-full justify-start font-normal"
                />
              }
            >
              <CalendarDays />
              <span id="start-value">
                {start ? format(parseISO(start), "dd/MM/yyyy") : "Select start date"}
              </span>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-3" align="start">
              <Calendar
                mode="single"
                captionLayout="dropdown"
                startMonth={new Date(CURRENT_YEAR - 100, 0)}
                endMonth={new Date(CURRENT_YEAR + 100, 11)}
                autoFocus
                selected={start ? parseISO(start) : undefined}
                defaultMonth={start ? parseISO(start) : undefined}
                onSelect={(date) => {
                  if (!date) return
                  const nextStart = format(date, "yyyy-MM-dd")
                  if (nextStart !== start) {
                    setStart(nextStart)
                    setHolidays([])
                    resetResults()
                  }
                  setStartCalendarOpen(false)
                }}
              />
            </PopoverContent>
          </Popover>
          <p className="text-xs text-muted-foreground">
            Day 1 of the four-week roster.
          </p>
        </div>
        <div className="space-y-2">
          <label id="holidays-label" className="text-sm font-medium">
            Public holidays{" "}
            <span className="font-normal text-muted-foreground">
              (optional)
            </span>
          </label>
          <Popover>
            <PopoverTrigger
              render={
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy || !start}
                  aria-labelledby="holidays-label holidays-value"
                  className="w-full justify-start font-normal"
                />
              }
            >
              <CalendarDays />
              <span id="holidays-value">
                {holidays.length
                  ? `${holidays.length} holiday${holidays.length === 1 ? "" : "s"} selected`
                  : "Select public holidays"}
              </span>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-3" align="start">
              <div className="flex items-center justify-between px-1">
                <p className="text-sm font-medium">Public holidays</p>
                {holidays.length > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setHolidays([])
                      resetResults()
                    }}
                  >
                    Clear
                  </Button>
                )}
              </div>
              {start && (
                <Calendar
                  mode="multiple"
                  captionLayout="dropdown"
                  startMonth={START_MONTH}
                  endMonth={END_MONTH}
                  autoFocus
                  selected={holidays}
                  defaultMonth={parseISO(start)}
                  onSelect={(dates) => {
                    setHolidays(dates ?? [])
                    resetResults()
                  }}
                />
              )}
            </PopoverContent>
          </Popover>
          <p className="text-xs leading-5 text-muted-foreground">
            Select dates within the four-week roster.
          </p>
          {holidays.length > 0 && (
            <p className="text-xs leading-5 text-muted-foreground">
              {[...holidays]
                .sort((a, b) => a.getTime() - b.getTime())
                .map((date) => format(date, "d MMM yyyy"))
                .join(", ")}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
