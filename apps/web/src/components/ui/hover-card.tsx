"use client";

import * as HoverCardPrimitive from "@radix-ui/react-hover-card";
import { cn } from "@/lib/utils";

export const HoverCard = HoverCardPrimitive.Root;
export const HoverCardTrigger = HoverCardPrimitive.Trigger;

export function HoverCardContent({
  className,
  sideOffset = 8,
  ...props
}: React.ComponentPropsWithoutRef<typeof HoverCardPrimitive.Content>) {
  return (
    <HoverCardPrimitive.Portal>
      <HoverCardPrimitive.Content
        sideOffset={sideOffset}
        className={cn(
          "z-50 w-80 rounded-lg border border-border bg-white p-4 text-sm leading-6 text-abacos-black shadow-soft outline-none",
          "data-[side=bottom]:animate-in data-[side=top]:animate-in",
          className,
        )}
        {...props}
      />
    </HoverCardPrimitive.Portal>
  );
}
