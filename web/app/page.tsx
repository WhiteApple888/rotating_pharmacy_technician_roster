"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { AuditHeader } from "@/components/web/audit-header"
import { AuditStepper } from "@/components/web/audit-stepper"
import { StepParameters } from "@/components/web/step-parameters"
import { StepResults } from "@/components/web/step-results"
import { StepUpload } from "@/components/web/step-upload"
import type { AuditStep } from "@/components/web/roster-audit-types"
import type { AuditValues } from "@/components/web/roster-audit-types"

export default function Page() {
  const [step, setStep] = useState<AuditStep>(1)
  const [fileName, setFileName] = useState("")
  const [parameters, setParameters] = useState<AuditValues>({
    worksheetName: "Roster",
    startDate: new Date(2026, 3, 13),
    publicHolidays: null,
    staffCount: 16,
  })

  const returnToUpload = () => {
    setStep(1)
  }

  return (
    <main className="min-h-svh bg-[radial-gradient(circle_at_top,_rgba(14,116,144,0.11),_transparent_34rem)] px-4 py-10 sm:px-6 sm:py-16">
      <div className="mx-auto w-full max-w-3xl">
        <AuditHeader />
        <AuditStepper step={step} onStepChange={setStep} />
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 22 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -22 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
          >
            {step === 1 && (
              <StepUpload
                onFile={(file) => {
                  setFileName(file.name)
                  setStep(2)
                }}
              />
            )}
            {step === 2 && (
              <StepParameters
                fileName={fileName}
                values={parameters}
                onValuesChange={setParameters}
                onBack={returnToUpload}
                onAudit={() => setStep(3)}
              />
            )}
            {step === 3 && <StepResults onReaudit={() => setStep(2)} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </main>
  )
}
