"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { AuditHeader } from "@/components/web/audit-header"
import { AuditStepper } from "@/components/web/audit-stepper"
import { StepParameters } from "@/components/web/step-parameters"
import { StepResults } from "@/components/web/step-results"
import { StepUpload } from "@/components/web/step-upload"
import { runAudit, type AuditResponse } from "@/lib/audit-api"
import type { AuditStep } from "@/app/schema/roster-audit-types"
import type { AuditValues } from "@/app/schema/roster-audit-types"

export default function Page() {
  const [step, setStep] = useState<AuditStep>(1)
  const [fileName, setFileName] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [worksheetNames, setWorksheetNames] = useState<string[]>([])
  const [result, setResult] = useState<AuditResponse | null>(null)
  const [auditError, setAuditError] = useState("")
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
                onFile={(uploadedFile, sheets) => {
                  setFile(uploadedFile)
                  setWorksheetNames(sheets)
                  setParameters((current) => ({
                    ...current,
                    worksheetName: sheets[0],
                  }))
                  setFileName(uploadedFile.name)
                  setResult(null)
                  setAuditError("")
                  setStep(2)
                }}
              />
            )}
            {step === 2 && (
              <StepParameters
                fileName={fileName}
                worksheetNames={worksheetNames}
                values={parameters}
                onValuesChange={setParameters}
                onBack={returnToUpload}
                onAudit={async (submittedValues) => {
                  if (!file) return
                  try {
                    setAuditError("")
                    setResult(await runAudit(file, submittedValues))
                    setStep(3)
                  } catch (reason) {
                    setAuditError(
                      reason instanceof Error
                        ? reason.message
                        : "The audit could not be completed."
                    )
                  }
                }}
              />
            )}
            {step === 2 && auditError ? (
              <p
                role="alert"
                className="mt-4 text-center text-sm text-destructive"
              >
                {auditError}
              </p>
            ) : null}
            {step === 3 && result ? (
              <StepResults result={result} onReaudit={() => setStep(2)} />
            ) : null}
          </motion.div>
        </AnimatePresence>
      </div>
    </main>
  )
}
