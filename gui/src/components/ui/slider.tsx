// Minimal shadcn/ui-style Slider built on Radix (ARIA-compliant by construction —
// real accessibility infrastructure, spec 9/11.1), copied into the repo so we own it.
import * as React from "react";
import * as SliderPrimitive from "@radix-ui/react-slider";
import { cn } from "@/lib/utils";

const Slider = React.forwardRef<
  React.ElementRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn("relative flex w-full touch-none select-none items-center", className)}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-2 w-full grow overflow-hidden rounded-full bg-slate-200">
      <SliderPrimitive.Range className="absolute h-full bg-okabe-blue" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-5 w-5 rounded-full border-2 border-okabe-blue bg-white shadow focus:outline-none focus:ring-2 focus:ring-okabe-blue" />
  </SliderPrimitive.Root>
));
Slider.displayName = "Slider";
export { Slider };
