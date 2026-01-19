import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        // Gradient variant for prominent CTAs - brand purple-blue gradient
        gradient:
          "bg-gradient-to-br from-[#667eea] to-[#764ba2] text-white font-semibold shadow-md hover:shadow-lg hover:from-[#5a6fd6] hover:to-[#6a4190] hover:-translate-y-0.5 active:translate-y-0 focus-visible:ring-[#764ba2]/40",
        // Success variant for positive actions
        success:
          "bg-gradient-to-br from-[#10b981] to-[#059669] text-white font-semibold shadow-md hover:shadow-lg hover:from-[#059669] hover:to-[#047857] hover:-translate-y-0.5 active:translate-y-0 focus-visible:ring-[#10b981]/40",
        destructive:
          "bg-destructive text-white hover:bg-destructive/90 hover:-translate-y-0.5 active:translate-y-0 active:brightness-95 focus-visible:ring-destructive/40 dark:bg-destructive/60",
        outline:
          "border bg-background shadow-xs hover:bg-accent hover:text-accent-foreground dark:bg-input/30 dark:border-input dark:hover:bg-input/50",
        // Outline primary - bordered with brand color
        "outline-primary":
          "border-2 border-primary bg-transparent text-primary hover:bg-primary/10 dark:hover:bg-primary/20",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost:
          "hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3",
        sm: "h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5",
        lg: "h-10 rounded-md px-6 has-[>svg]:px-4",
        // Extra large for prominent CTAs
        xl: "h-12 rounded-lg px-8 text-base has-[>svg]:px-6",
        icon: "size-9",
        "icon-sm": "size-8",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
