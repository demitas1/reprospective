import * as React from "react"
import { cn } from "@/lib/utils"

export interface SwitchProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, checked, onCheckedChange, ...props }, ref) => {
    return (
      <label className="inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          className="sr-only peer"
          checked={checked}
          onChange={(e) => onCheckedChange?.(e.target.checked)}
          ref={ref}
          {...props}
        />
        <div className={cn(
          "relative w-11 h-6 bg-muted rounded-full peer peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ring peer-focus:ring-offset-2 peer-checked:bg-primary transition-colors",
          className
        )}>
          <div className={cn(
            "absolute top-0.5 left-0.5 bg-background h-5 w-5 rounded-full transition-transform",
            checked && "translate-x-5"
          )} />
        </div>
      </label>
    )
  }
)
Switch.displayName = "Switch"

export { Switch }
