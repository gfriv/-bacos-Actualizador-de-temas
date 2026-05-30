import Link from "next/link";
import { CheckCircle2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

export type WorkflowTimelineItem = {
  label: string;
  href?: string;
  done: boolean;
  active?: boolean;
};

export function WorkflowTimeline({ items }: { items: WorkflowTimelineItem[] }) {
  const completed = items.filter((item) => item.done).length;
  const width = items.length > 1 ? `${Math.max(8, (completed / (items.length - 1)) * 100)}%` : "0%";

  return (
    <div className="rounded-lg border border-border bg-white/82 p-4">
      <div className="relative">
        <div className="absolute left-4 right-4 top-4 h-0.5 bg-abacos-light" aria-hidden />
        <div className="flow-rail absolute left-4 top-4 h-0.5 rounded-full" style={{ width }} aria-hidden />
        <ol className="relative grid grid-cols-3 gap-3 sm:grid-cols-6">
          {items.map((item) => {
            const Icon = item.done ? CheckCircle2 : Circle;
            const content = (
              <span className="group grid justify-items-center gap-2 text-center">
                <span
                  className={cn(
                    "grid h-8 w-8 place-items-center rounded-full border bg-white transition group-hover:scale-105",
                    item.done
                      ? "border-abacos-green text-abacos-green"
                      : item.active
                        ? "border-abacos-red text-abacos-red"
                        : "border-border text-abacos-gray",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <span
                  className={cn(
                    "text-[0.72rem] font-semibold leading-4",
                    item.active ? "text-abacos-red-dark" : "text-abacos-gray",
                  )}
                >
                  {item.label}
                </span>
              </span>
            );

            return (
              <li key={item.label}>
                {item.href ? (
                  <Link href={item.href} className="block rounded-md outline-none focus-visible:ring-2 focus-visible:ring-abacos-red">
                    {content}
                  </Link>
                ) : (
                  content
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
