import { Check } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AuditStep } from "./roster-audit-types"

const steps = ["Upload File", "Key Parameters", "Results"]

export function AuditStepper({
  step,
  onStepChange,
}: {
  step: AuditStep
  onStepChange: (step: AuditStep) => void
}) {
  return (
    <nav aria-label="Audit progress" className="mx-auto mb-10 w-full max-w-2xl">
      <ol className="grid grid-cols-3 gap-2 sm:gap-5">
        {steps.map((label, index) => {
          const position = (index + 1) as AuditStep
          const complete = position < step
          const active = position === step
          return (
            <li
              key={label}
              className="relative flex flex-col items-center gap-2 text-center"
            >
              {index > 0 && (
                <span
                  className={cn(
                    "absolute top-4 right-1/2 h-px w-full",
                    complete || active ? "bg-primary" : "bg-border"
                  )}
                />
              )}
              <button
                type="button"
                disabled={!complete}
                onClick={() => complete && onStepChange(position)}
                aria-current={active ? "step" : undefined}
                className={cn(
                  "relative z-10 flex size-8 items-center justify-center rounded-full border text-xs font-semibold transition-transform",
                  complete || active
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-border bg-background text-muted-foreground",
                  complete && "cursor-pointer hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                )}
              >
                {complete ? <Check className="size-4" /> : position}
              </button>
              <button
                type="button"
                disabled={!complete}
                onClick={() => complete && onStepChange(position)}
                className={cn(
                  "text-xs font-medium sm:text-sm",
                  active ? "text-foreground" : "text-muted-foreground",
                  complete && "cursor-pointer hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                )}
              >
                {label}
              </button>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
