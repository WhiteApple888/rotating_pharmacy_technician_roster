import { Landing, SiteFooter, WorkflowGuide } from "@/components/web/landing"
import { RosterDashboard } from "@/components/web/roster-dashboard"

export default function Page() {
  return (
    <main className="min-h-screen">
      <Landing />
      <RosterDashboard />
      <WorkflowGuide />
      <SiteFooter />
    </main>
  )
}
