import {
  ArrowDown,
  ArrowRight,
  CalendarDays,
  Check,
  ClipboardCheck,
  ShieldCheck,
  Upload,
} from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ThemeToggle } from "@/components/web/theme-toggle"

export function Landing() {
  return (
    <>
      <header className="border-b bg-background/90">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 sm:px-8">
          <a
            href="#top"
            className="flex items-center gap-3 font-semibold tracking-tight"
          >
            <span className="flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <ShieldCheck className="size-5" />
            </span>
            <span>
              RPT Roster<span className="text-primary"> / </span>Review{" "}
              <span className="hidden pl-2 text-xs font-normal text-muted-foreground sm:inline">
                TTSH Outpatient Pharmacy
              </span>
            </span>
          </a>
          <div className="flex items-center gap-5">
            <a
              href="#guide"
              className="hidden text-sm text-muted-foreground hover:text-foreground sm:block"
            >
              How it works
            </a>
            <a
              href="#workspace"
              className="hidden text-sm font-medium sm:block"
            >
              Dashboard
            </a>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <section
        id="top"
        className="relative overflow-hidden border-b bg-[radial-gradient(ellipse_at_78%_15%,color-mix(in_oklab,var(--primary)_12%,transparent),transparent_42%)]"
      >
        <div className="mx-auto grid max-w-7xl items-center gap-8 px-5 py-10 sm:px-8 lg:grid-cols-[1fr_0.9fr] lg:gap-16 lg:py-12">
          <div>
            <Badge
              variant="secondary"
              className="mb-6 rounded-full px-3 py-1 text-primary"
            >
              <span className="mr-2 size-1.5 rounded-full bg-primary" />{" "}
              PHARMACY OPERATIONS TOOL
            </Badge>
            <h1 className="max-w-2xl text-4xl leading-[1.08] font-semibold tracking-tight sm:text-5xl lg:text-6xl">
              A clearer view of every{" "}
              <span className="text-primary">roster.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-muted-foreground sm:text-lg">
              Review four weeks of shifts, check configured roster rules, and
              find a better schedule—all from your workbook.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-5">
              <Button
                size="lg"
                className="h-11 px-5"
                render={<a href="#workspace" />}
              >
                Open dashboard <ArrowRight />
              </Button>
              <a
                href="#guide"
                className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
              >
                See how it works <ArrowDown className="size-4" />
              </a>
            </div>
            <div className="mt-8 flex flex-wrap gap-x-7 gap-y-3 text-xs font-medium text-muted-foreground">
              <span className="flex items-center gap-2">
                <Check className="size-4 text-primary" /> 28-day review
              </span>
              <span className="flex items-center gap-2">
                <Check className="size-4 text-primary" /> Excel workbook in,
                Excel out
              </span>
            </div>
          </div>
          <Preview />
        </div>
      </section>
    </>
  )
}

export function WorkflowGuide() {
  return (
    <section
      id="guide"
      className="mx-auto max-w-7xl px-5 py-16 sm:px-8 lg:py-20"
    >
      <div className="grid gap-8 lg:grid-cols-[0.8fr_2fr] lg:gap-16">
        <div>
          <p className="text-xs font-semibold tracking-[0.16em] text-primary uppercase">
            A simple workflow
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            From workbook to clarity.
          </h2>
          <p className="mt-3 max-w-sm text-sm leading-6 text-muted-foreground">
            Use the same roster settings for both tools. Choose the workflow you
            need, in any order.
          </p>
        </div>
        <div className="grid gap-6 sm:grid-cols-3">
          {[
            [
              "01",
              "Add your roster",
              "Upload an .xlsx workbook or paste your roster into the grid.",
            ],
            [
              "02",
              "Set the context",
              "Choose the worksheet, roster start date and any public holidays.",
            ],
            [
              "03",
              "Review or optimize",
              "Run an audit to see findings, or optimize and download a revised workbook.",
            ],
          ].map(([n, title, description]) => (
            <div key={n} className="border-t-2 border-primary/30 pt-5">
              <span className="font-mono text-xs text-primary">{n} /</span>
              <h3 className="mt-4 font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
export function SiteFooter() {
  return (
    <footer className="border-t">
      <div className="mx-auto flex max-w-7xl flex-wrap justify-between gap-3 px-5 py-7 text-xs text-muted-foreground sm:px-8">
        <span>Roster / Review · TTSH Pharmacy</span>
        <span>Built for a more confident roster review.</span>
      </div>
    </footer>
  )
}
function Preview() {
  return (
    <div className="relative">
      <div className="absolute -inset-4 rounded-[2rem] bg-primary/5 blur-2xl" />
      <Card className="relative gap-0 overflow-hidden py-0 shadow-xl shadow-primary/5">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <ClipboardCheck className="size-4" />
            </span>
            <div>
              <p className="text-sm font-semibold">RPT Roster Dashboard</p>
              <p className="text-[11px] text-muted-foreground">
                A preview of your workspace
              </p>
            </div>
          </div>
          <Badge variant="outline">SAMPLE</Badge>
        </div>
        <div className="p-5 sm:p-6">
          <div className="flex gap-5 border-b text-sm">
            <span className="border-b-2 border-primary pb-3 font-medium text-primary">
              Audit
            </span>
            <span className="pb-3 text-muted-foreground">Optimization</span>
          </div>
          <div className="mt-5 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Four-week review</p>
              <p className="mt-1 font-semibold">Audit results</p>
            </div>
            <Badge variant="secondary">Example findings</Badge>
          </div>
          <div className="mt-5 space-y-2">
            {[
              ["01", "Week 1", "Days 1–7"],
              ["02", "Week 2", "Days 8–14"],
              ["03", "Week 3", "Days 15–21"],
              ["04", "Week 4", "Days 22–28"],
            ].map(([n, week, days]) => (
              <div
                key={n}
                className="flex items-center gap-3 rounded-lg border px-3 py-3"
              >
                <span className="font-mono text-xs text-primary">{n}</span>
                <span className="flex-1 text-sm font-medium">{week}</span>
                <span className="text-xs text-muted-foreground">{days}</span>
                <CalendarDays className="size-4 text-muted-foreground" />
              </div>
            ))}
          </div>
          <div className="mt-5 flex items-center gap-2 rounded-lg bg-primary/5 px-3 py-3 text-xs text-muted-foreground">
            <Upload className="size-4 text-primary" /> Upload a workbook below
            to see your own results.
          </div>
        </div>
      </Card>
    </div>
  )
}
