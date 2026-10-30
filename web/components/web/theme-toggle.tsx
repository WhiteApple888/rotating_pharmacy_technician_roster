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
      className="duration-150 motion-reduce:transition-none"
      checked={isDark}
      disabled={!mounted}
      onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
      aria-label={`Switch to ${nextThemeLabel} mode`}
      title={`Switch to ${nextThemeLabel} mode`}
    >
      <Sun
        aria-hidden="true"
        className="pointer-events-none absolute left-2 size-4 text-amber-500 transition-opacity duration-150 group-data-[checked]/switch:opacity-0 motion-reduce:transition-none"
      />
      <Moon
        aria-hidden="true"
        className="pointer-events-none absolute right-2 size-4 text-primary-foreground opacity-0 transition-opacity duration-150 group-data-[checked]/switch:opacity-100 motion-reduce:transition-none"
      />
      <SwitchThumb className="duration-150 motion-reduce:transition-none">
        <Sun
          aria-hidden="true"
          className="size-3.5 text-amber-500 transition-opacity duration-150 group-data-[checked]/switch:opacity-0 motion-reduce:transition-none"
        />
        <Moon
          aria-hidden="true"
          className="absolute size-3.5 opacity-0 transition-opacity duration-150 group-data-[checked]/switch:opacity-100 motion-reduce:transition-none"
        />
      </SwitchThumb>
    </Switch>
  )
}
