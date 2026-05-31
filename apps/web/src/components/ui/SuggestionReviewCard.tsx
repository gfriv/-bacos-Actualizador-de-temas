"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Edit3, Pause, RotateCcw, Save, X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatusBadge, type StatusKey } from "@/components/ui/StatusBadge";
import { Textarea } from "@/components/ui/textarea";
import { HelpTooltip, RichTooltip } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type ReviewPayload = {
  status: "approved" | "rejected" | "edited" | "pending";
  proposed_change?: string;
};

const confidenceLabels: Record<string, string> = {
  low: "Baja",
  medium: "Media",
  high: "Alta",
};

const anchorLabels: Record<string, { label: string; className: string; help: string }> = {
  matched: {
    label: "Anclaje verificado",
    className: "border-green-200 bg-green-50 text-green-800",
    help: "El fragmento original se ha localizado en el documento y puede integrarse si la sugerencia esta aprobada.",
  },
  failed: {
    label: "Anclaje fallido",
    className: "border-abacos-red/25 bg-abacos-red-soft text-abacos-red-dark",
    help: "El fragmento original ya no encaja con el documento activo. No se integrara automaticamente.",
  },
  unchecked: {
    label: "Anclaje pendiente",
    className: "border-abacos-yellow/35 bg-amber-50 text-amber-800",
    help: "El anclaje se comprobara al consolidar. Conviene revisar que el fragmento original coincide.",
  },
};

export function SuggestionReviewCard({
  id,
  section,
  original,
  proposed,
  justification,
  source,
  confidence,
  status,
  suggestionType,
  anchorStatus = "unchecked",
  teacherNotes,
  reviewedAt,
  onReview,
}: {
  id?: number;
  section: string;
  original: string;
  proposed: string;
  justification: string;
  source: string;
  confidence: string;
  status: StatusKey;
  suggestionType?: string;
  anchorStatus?: string | null;
  teacherNotes?: string | null;
  reviewedAt?: string | null;
  onReview?: (id: number, payload: ReviewPayload) => void | Promise<void>;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(proposed);

  useEffect(() => {
    setDraft(proposed);
  }, [proposed]);

  async function review(payload: ReviewPayload) {
    if (!id || !onReview) return;
    await onReview(id, payload);
    if (payload.status === "edited") setIsEditing(false);
  }

  const confidenceLabel = confidenceLabels[confidence] ?? confidence;
  const isIntegrable = status === "approved" || status === "edited";
  const anchor = anchorLabels[anchorStatus ?? "unchecked"] ?? anchorLabels.unchecked;

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      className={cn(
        "interactive-card overflow-hidden rounded-lg border bg-white shadow-sm surface-glow",
        isIntegrable ? "border-green-100" : status === "rejected" ? "border-neutral-200" : "border-border",
      )}
    >
      <div className="relative border-b border-border bg-white px-5 py-4">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-abacos-red/65 via-abacos-yellow/50 to-transparent" aria-hidden />
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary" className="uppercase tracking-[0.12em]">
                {formatSuggestionType(suggestionType)}
              </Badge>
              <Badge variant="outline">Confianza {confidenceLabel}</Badge>
              <Badge variant="outline" className={cn("gap-1.5", anchor.className)}>
                {anchor.label}
              </Badge>
              <HelpTooltip label="La confianza orienta la revisión, pero no sustituye la validación docente." />
            </div>
            <h3 className="mt-3 text-base font-semibold text-abacos-black">Sugerencia revisable</h3>
            <p className="mt-1 text-sm leading-6 text-abacos-gray">{section}</p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <StatusBadge status={status} />
            {reviewedAt ? (
              <span className="rounded-full bg-abacos-light px-2.5 py-1 text-xs font-semibold text-abacos-gray">
                Revisada
              </span>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-4 p-5">
        <div className="grid gap-4 xl:grid-cols-2">
          <TraceBlock title="Fragmento original" tone="neutral" text={original} />
          <div className="interactive-card rounded-md border border-abacos-red-soft bg-abacos-red-soft/45 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-red-dark">
                Cambio propuesto
              </p>
              <RichTooltip
                title="Cambio propuesto"
                detail="Puedes aceptar la redacción, rechazarla o editarla antes de marcarla como validada."
                recommendation="Si editas, el sistema guarda tu versión como cambio integrable."
              />
            </div>
            {isEditing ? (
              <Textarea
                className="mt-3 min-h-36 bg-white"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                aria-label="Editar cambio propuesto"
              />
            ) : (
              <p className="mt-3 text-sm leading-7 text-abacos-black">{proposed}</p>
            )}
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(260px,0.42fr)]">
          <div className="interactive-card rounded-md border border-border bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">Justificación</p>
            <p className="mt-2 text-sm leading-7 text-abacos-black">{justification}</p>
          </div>
          <div className="interactive-card rounded-md border border-border bg-abacos-light p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">Trazabilidad</p>
            <p className="mt-2 text-sm leading-6 text-abacos-black">{source}</p>
            <p className="mt-3 rounded-md border border-white/80 bg-white p-3 text-xs leading-5 text-abacos-gray">
              {anchor.help}
            </p>
            {teacherNotes ? (
              <p className="mt-3 rounded-md bg-white p-3 text-xs leading-5 text-abacos-gray">
                Nota docente: {teacherNotes}
              </p>
            ) : null}
          </div>
        </div>

        <div className="sticky bottom-3 z-10 flex flex-col gap-3 rounded-lg border border-border bg-white/92 p-3 shadow-[0_18px_45px_rgba(30,30,30,0.12)] backdrop-blur lg:flex-row lg:items-center lg:justify-between">
          <p className="text-xs leading-5 text-abacos-gray">
            Solo las sugerencias aceptadas o editadas podrán pasar al documento consolidado.
          </p>
          <div className="flex flex-wrap gap-2">
            {isEditing ? (
              <>
                <Button size="sm" className="button-glow" onClick={() => review({ status: "edited", proposed_change: draft })}>
                  <Save className="h-4 w-4" aria-hidden />
                  Guardar edición
                </Button>
                <Button size="sm" variant="outline" onClick={() => { setDraft(proposed); setIsEditing(false); }}>
                  <RotateCcw className="h-4 w-4" aria-hidden />
                  Cancelar
                </Button>
              </>
            ) : (
              <>
                <Button size="sm" className="button-glow" onClick={() => review({ status: "approved" })}>
                  <Check className="h-4 w-4" aria-hidden />
                  Aceptar
                </Button>
                <Button size="sm" variant="outline" onClick={() => review({ status: "rejected" })}>
                  <X className="h-4 w-4" aria-hidden />
                  Rechazar
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setIsEditing(true)}>
                  <Edit3 className="h-4 w-4" aria-hidden />
                  Editar
                </Button>
                <Button size="sm" variant="ghost" onClick={() => review({ status: "pending" })}>
                  <Pause className="h-4 w-4" aria-hidden />
                  Pendiente
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </motion.article>
  );
}

function TraceBlock({ title, text, tone }: { title: string; text: string; tone: "neutral" | "red" }) {
  return (
    <div
      className={cn(
        "interactive-card rounded-md border p-4",
        tone === "red" ? "border-abacos-red-soft bg-abacos-red-soft/45" : "border-border bg-abacos-light",
      )}
    >
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">{title}</p>
      <p className="mt-3 text-sm leading-7 text-abacos-black">{text}</p>
    </div>
  );
}

function formatSuggestionType(type?: string) {
  const labels: Record<string, string> = {
    scientific_update: "Actualización científica",
    legal_curricular: "Legal/curricular",
    bibliographic_update: "Bibliográfica",
    didactic_improvement: "Didáctica",
  };
  return type ? (labels[type] ?? type.replaceAll("_", " ")) : "Sugerencia";
}
