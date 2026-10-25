import { ShieldCheck } from "lucide-react"
import { ThemeToggle } from "@/components/web/theme-toggle"

export function AuditHeader() {
  return (
    <header className="relative mb-10 text-center">
      <div className="absolute top-0 right-0 sm:top-1">
        <ThemeToggle />
      </div>
      <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold tracking-wide text-primary uppercase">
        <ShieldCheck className="size-3.5" /> TTSH Pharmacy operations
      </div>
      <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
        RPT Monthly Roster Audit
      </h1>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-muted-foreground sm:text-base">
        Validate shifts in a single click.
      </p>
    </header>
  )
}
