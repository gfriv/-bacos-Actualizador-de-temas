import type { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="relative isolate overflow-hidden rounded-lg border border-border bg-white/76 p-4 shadow-sm backdrop-blur sm:p-5 md:p-6">
      <div className="absolute inset-y-0 right-0 z-0 hidden w-80 abacus-rail opacity-10 lg:block" aria-hidden />
      <div className="relative z-10 flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-abacos-red-dark">
            Sistema Ábacos
          </p>
          <h1 className="text-xl font-bold tracking-tight text-abacos-black sm:text-2xl md:text-3xl">{title}</h1>
          {description ? <p className="mt-2 max-w-3xl text-sm leading-6 text-abacos-gray">{description}</p> : null}
        </div>
        {actions ? <div className="flex shrink-0 flex-wrap gap-2 sm:justify-end">{actions}</div> : null}
      </div>
    </div>
  );
}
