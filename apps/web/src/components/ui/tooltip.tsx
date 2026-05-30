"use client";

import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";

export const TooltipProvider = TooltipPrimitive.Provider;
export const Tooltip = TooltipPrimitive.Root;
export const TooltipTrigger = TooltipPrimitive.Trigger;

export function TooltipContent({
  className,
  sideOffset = 8,
  ...props
}: React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        sideOffset={sideOffset}
        className={cn(
          "z-50 max-w-80 rounded-lg border border-white/10 bg-abacos-black px-3 py-2 text-xs leading-5 text-white shadow-[0_22px_55px_rgba(30,30,30,0.24)]",
          className,
        )}
        {...props}
      />
    </TooltipPrimitive.Portal>
  );
}

export function HelpTooltip({ label, className }: { label: string; className?: string }) {
  return (
    <Tooltip>
      <TooltipTrigger
        type="button"
        className={cn(
          "inline-flex h-5 w-5 items-center justify-center rounded-full text-abacos-gray transition hover:bg-abacos-red-soft hover:text-abacos-red-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-abacos-red",
          className,
        )}
        aria-label={label}
      >
        <Info className="h-3.5 w-3.5" aria-hidden />
      </TooltipTrigger>
      <TooltipContent>
        <div className="space-y-1.5">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-white/55">Ayuda contextual</p>
          <p>{label}</p>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}

export function RichTooltip({
  title,
  detail,
  recommendation,
  className,
}: {
  title: string;
  detail: string;
  recommendation?: string;
  className?: string;
}) {
  return (
    <Tooltip>
      <TooltipTrigger
        type="button"
        className={cn(
          "inline-flex h-7 items-center rounded-full border border-border bg-white px-2.5 text-xs font-semibold text-abacos-gray transition hover:border-abacos-red-soft hover:bg-abacos-red-soft hover:text-abacos-red-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-abacos-red",
          className,
        )}
        aria-label={title}
      >
        Detalle
      </TooltipTrigger>
      <TooltipContent className="p-4">
        <div className="space-y-2">
          <p className="font-semibold text-white">{title}</p>
          <p className="text-white/76">{detail}</p>
          {recommendation ? (
            <p className="rounded-md border border-white/10 bg-white/[0.08] p-2 text-white/72">{recommendation}</p>
          ) : null}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
