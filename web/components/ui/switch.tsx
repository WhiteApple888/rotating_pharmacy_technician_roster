import { Switch as SwitchPrimitive } from "@base-ui/react/switch"
import { cn } from "cn"

function Switch({ className, ...props }: SwitchPrimitive.Root.Props) {
  return (
    <SwitchPrimitive.Root
      data-slot="switch"
      className={cn(
        "group/switch relative inline-flex h-8 w-16 shrink-0 cursor-pointer items-center rounded-full border border-border/70 bg-muted p-0.5 shadow-sm transition-[background-color,border-color,box-shadow] duration-300 ease-out outline-none hover:border-primary/40 focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 data-[checked]:border-primary data-[checked]:bg-primary",
        className
      )}
      {...props}
    />
  )
}

function SwitchThumb({ className, ...props }: SwitchPrimitive.Thumb.Props) {
  return (
    <SwitchPrimitive.Thumb
      data-slot="switch-thumb"
      className={cn(
        "relative z-10 flex size-7 translate-x-0 items-center justify-center rounded-full bg-background text-foreground shadow-md transition-[transform,background-color,color] duration-300 ease-out data-[checked]:translate-x-8",
        className
      )}
      {...props}
    />
  )
}

export { Switch, SwitchThumb }
