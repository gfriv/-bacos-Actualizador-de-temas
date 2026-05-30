import type { ReactNode } from "react";
import { FileQuestion } from "lucide-react";
import { cn } from "@/lib/utils";

export function PremiumEmptyState({
  title,
  description,
  action,
  className,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg border border-dashed border-border bg-white p-6",
        className,
      )}
    >
      <div className="absolute inset-y-0 right-0 w-48 abacus-rail opacity-10" aria-hidden />
      <div className="relative max-w-xl">
        <div className="grid h-11 w-11 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark">
          <FileQuestion className="h-5 w-5" aria-hidden />
        </div>
        <h3 className="mt-4 font-semibold text-abacos-black">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-abacos-gray">{description}</p>
        {action ? <div className="mt-5">{action}</div> : null}
      </div>
    </div>
  );
}
