"use client"

import { useState, useEffect } from "react"
import { Moon, Sun } from "lucide-react"
import { useTheme } from "next-themes"
import { Switch, SwitchThumb } from "@/components/ui/switch"

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => setMounted(true))

    return () => window.cancelAnimationFrame(frame)
  }, [])

  const isDark = mounted && resolvedTheme === "dark"
  const nextThemeLabel = isDark ? "light" : "dark"

  return (
    <Switch
      checked={isDark}
      disabled={!mounted}
      onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
      aria-label={`Switch to ${nextThemeLabel} mode`}
      title={`Switch to ${nextThemeLabel} mode`}
    >
      <Sun
        aria-hidden="true"
        className="pointer-events-none absolute left-2 size-4 text-amber-500 transition-opacity duration-200 group-data-[checked]/switch:opacity-0"
      />
      <Moon
        aria-hidden="true"
        className="pointer-events-none absolute right-2 size-4 text-primary-foreground opacity-0 transition-opacity duration-200 group-data-[checked]/switch:opacity-100"
      />
      <SwitchThumb>
        <Sun
          aria-hidden="true"
          className="size-3.5 text-amber-500 transition-all duration-300 group-data-[checked]/switch:scale-0 group-data-[checked]/switch:rotate-90 group-data-[checked]/switch:opacity-0"
        />
        <Moon
          aria-hidden="true"
          className="absolute size-3.5 scale-0 -rotate-90 opacity-0 transition-all duration-300 group-data-[checked]/switch:scale-100 group-data-[checked]/switch:rotate-0 group-data-[checked]/switch:opacity-100"
        />
      </SwitchThumb>
    </Switch>
  )
}
