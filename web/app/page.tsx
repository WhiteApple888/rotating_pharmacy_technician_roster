"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "motion/react"
import { AuditHeader } from "@/components/web/audit-header"
import { AuditStepper } from "@/components/web/audit-stepper"
import { StepParameters } from "@/components/web/step-parameters"
import { StepResults } from "@/components/web/step-results"
import { StepUpload } from "@/components/web/step-upload"
import { runAudit } from "@/app/actions"
import type { AuditResponse } from "@/lib/schema/audit-api"
import type { AuditStep } from "@/lib/schema/roster-audit-types"
import type { AuditValues } from "@/lib/schema/roster-audit-types"

export default function Page() {
  const [step, setStep] = useState<AuditStep>(1) // Tracks current wizard step (1: Upload, 2: Parameters, 3: Results).
  const [fileName, setFileName] = useState("") // Holds the uploaded raw filename.
  const [file, setFile] = useState<File | null>(null) // Holds the uploaded file object.
  const [worksheetNames, setWorksheetNames] = useState<string[]>([]) // List of sheet names extracted from the uploaded Excel/spreadsheet file.
  const [result, setResult] = useState<AuditResponse | null>(null) // Holds the API output after processing
  const [auditError, setAuditError] = useState("") // Stores error messages if the runAudit request fails.
  const [parameters, setParameters] = useState<AuditValues>({
    // Stores user-configured audit setting for persistence
    worksheetName: "Roster",
    startDate: new Date(),
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
                    const auditResult = await runAudit(file, submittedValues)
                    if (!auditResult.ok) {
                      setAuditError(auditResult.error)
                      return
                    }
                    setResult(auditResult.result)
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
