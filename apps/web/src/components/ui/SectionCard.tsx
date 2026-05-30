import type { ReactNode } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function SectionCard({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("interactive-card overflow-hidden", className)}>
      <div className="relative border-b border-border bg-white px-5 py-4">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-abacos-red/70 via-abacos-yellow/60 to-transparent" />
        <div className="mb-3 h-1 w-16 rounded-full flow-rail" />
        <h2 className="text-base font-semibold text-abacos-black">{title}</h2>
        {description ? <p className="mt-1 text-sm leading-6 text-abacos-gray">{description}</p> : null}
      </div>
      <div className="p-5">{children}</div>
    </Card>
  );
}
