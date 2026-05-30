import { Badge } from "@/components/ui/badge";

export type StatusKey =
  | "draft"
  | "document_uploaded"
  | "processing"
  | "reports_generated"
  | "under_review"
  | "consolidated"
  | "resources_generated"
  | "error"
  | "pending"
  | "approved"
  | "rejected"
  | "edited";

const statusMeta: Record<
  StatusKey,
  { label: string; variant: "yellow" | "green" | "blue" | "gray" | "secondary"; pulse?: boolean }
> = {
  draft: { label: "Borrador", variant: "gray" },
  document_uploaded: { label: "Documento subido", variant: "blue" },
  processing: { label: "Procesando", variant: "blue", pulse: true },
  reports_generated: { label: "Informes generados", variant: "yellow", pulse: true },
  under_review: { label: "En revisión", variant: "yellow", pulse: true },
  consolidated: { label: "Consolidado", variant: "green" },
  resources_generated: { label: "Recursos generados", variant: "green" },
  error: { label: "Error", variant: "secondary", pulse: true },
  pending: { label: "Pendiente", variant: "yellow", pulse: true },
  approved: { label: "Aprobada", variant: "green" },
  rejected: { label: "Rechazada", variant: "gray" },
  edited: { label: "Editada", variant: "blue" },
};

export function StatusBadge({ status }: { status: StatusKey }) {
  const meta = statusMeta[status];
  return (
    <Badge variant={meta.variant} data-status={status} className="gap-2 shadow-sm">
      <span className="status-dot" data-pulse={meta.pulse ? "true" : "false"} aria-hidden />
      {meta.label}
    </Badge>
  );
}
