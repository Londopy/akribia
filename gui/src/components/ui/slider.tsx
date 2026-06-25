import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

// shadcn/ui-style Slider on Radix (ARIA-compliant by construction — spec 9/11.1).
export const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root> & { accent?: string }
>(({ className, accent = "var(--accent)", ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn("relative flex w-full touch-none select-none items-center", className)}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-[#2a3550]">
      <SliderPrimitive.Range className="absolute h-full rounded-full" style={{ background: accent }} />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb
      className="block h-4 w-4 rounded-full border-2 bg-[#0b0e14] shadow transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-offset-bg"
      style={{ borderColor: accent }}
    />
  </SliderPrimitive.Root>
));
Slider.displayName = "Slider";
