"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  ClipboardCheck,
  FileCheck2,
  FileText,
  Layers3,
  Sparkles,
  UploadCloud,
  WandSparkles,
  type LucideIcon,
} from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { DocumentDropzone } from "@/components/ui/DocumentDropzone";
import { Progress } from "@/components/ui/progress";
import { ReportViewer } from "@/components/ui/ReportViewer";
import { SectionCard } from "@/components/ui/SectionCard";
import { StatusBadge, type StatusKey } from "@/components/ui/StatusBadge";
import { SuggestionReviewCard } from "@/components/ui/SuggestionReviewCard";
import { RichTooltip, TooltipProvider } from "@/components/ui/tooltip";
import { WorkflowTimeline } from "@/components/ui/WorkflowTimeline";
import {
  consolidateProject,
  generateResource,
  getConsolidated,
  getProject,
  listDocuments,
  listReports,
  listResources,
  listSections,
  listSuggestions,
  reviewSuggestion,
  runResearchAnalysis,
  uploadDocument,
  type ConsolidatedDocument,
  type DocumentRecord,
  type DocumentSection,
  type GeneratedResource,
  type Project,
  type Report,
  type Suggestion,
} from "@/lib/api";
import { cn } from "@/lib/utils";

type WorkspaceData = {
  project: Project | null;
  documents: DocumentRecord[];
  sections: DocumentSection[];
  reports: Report[];
  suggestions: Suggestion[];
  consolidated: ConsolidatedDocument | null;
  resources: GeneratedResource[];
};

type ReviewStats = {
  total: number;
  pending: number;
  approved: number;
  edited: number;
  rejected: number;
  reviewed: number;
  integrable: number;
};

const emptyWorkspace: WorkspaceData = {
  project: null,
  documents: [],
  sections: [],
  reports: [],
  suggestions: [],
  consolidated: null,
  resources: [],
};

const resourceTypes = [
  ["esquema_desarrollado", "Esquema desarrollado", "Estructura jerárquica del tema para repaso docente."],
  ["test_autoevaluacion", "Test de autoevaluación", "Preguntas con solución y explicación."],
  ["presentacion_clase", "Presentación de clase", "Guion estructurado para diapositivas."],
  ["guion_audio", "Guion de audio", "Narración para estudio autónomo."],
  ["guion_video", "Guion de vídeo", "Resumen audiovisual del tema consolidado."],
] as const;

function useProjectWorkspace(projectId: string) {
  const [data, setData] = useState<WorkspaceData>(emptyWorkspace);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [project, documents, sections, reports, suggestions, consolidated, resources] =
        await Promise.all([
          getProject(projectId),
          listDocuments(projectId),
          listSections(projectId),
          listReports(projectId),
          listSuggestions(projectId),
          getConsolidated(projectId).catch(() => null),
          listResources(projectId).catch(() => []),
        ]);

      setData({ project, documents, sections, reports, suggestions, consolidated, resources });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No se pudo cargar el proyecto");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { ...data, loading, error, reload };
}

export function ProjectOverviewClient({ projectId }: { projectId: string }) {
  const workspace = useProjectWorkspace(projectId);
  const [running, setRunning] = useState(false);
  const stats = useMemo(() => buildReviewStats(workspace.suggestions), [workspace.suggestions]);
  const progress = useMemo(() => buildFlowProgress(workspace), [workspace]);

  async function handleRunResearchAnalysis() {
    setRunning(true);
    try {
      await runResearchAnalysis(projectId);
      await workspace.reload();
      toast.success("Informes y sugerencias generados con búsqueda trazable");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo generar el análisis");
    } finally {
      setRunning(false);
    }
  }

  if (workspace.error) return <SectionCard className="mt-6" title="Error">{workspace.error}</SectionCard>;

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mt-6 grid gap-6">
        <ProjectCommandHeader
          project={workspace.project}
          stats={stats}
          progress={progress}
          loading={workspace.loading}
          onRunResearchAnalysis={handleRunResearchAnalysis}
          running={running}
          canRunAnalysis={workspace.sections.length > 0}
        />

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <ProjectMetric
            label="Secciones detectadas"
            value={workspace.sections.length}
            helper="Las secciones permiten que las sugerencias sean localizadas y revisables."
            icon={Layers3}
          />
          <ProjectMetric
            label="Informes generados"
            value={workspace.reports.length}
            helper="Debe existir un informe científico y uno curricular antes de revisar con criterio completo."
            icon={FileCheck2}
            tone="blue"
          />
          <ProjectMetric
            label="Sugerencias pendientes"
            value={stats.pending}
            helper="Las pendientes no se integran en el consolidado."
            icon={ClipboardCheck}
            tone="yellow"
          />
          <ProjectMetric
            label="Cambios integrables"
            value={stats.integrable}
            helper="Solo aprobadas y editadas pueden incorporarse al documento final."
            icon={BookOpenCheck}
            tone="green"
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
          <WorkflowBoard workspace={workspace} stats={stats} />
          <ProjectContextPanel project={workspace.project} stats={stats} />
        </div>
      </div>
    </TooltipProvider>
  );
}

export function ProjectDocumentClient({ projectId }: { projectId: string }) {
  const workspace = useProjectWorkspace(projectId);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const document = workspace.documents[0];

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(Number(projectId), file);
      setFile(null);
      await workspace.reload();
      toast.success("Documento subido y secciones detectadas");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo subir el documento");
    } finally {
      setUploading(false);
    }
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <SectionCard
          title={document?.original_filename ?? "Documento original"}
          description="Texto extraído del archivo DOCX/PDF. El contenido original se mantiene como referencia trazable."
        >
          {workspace.error ? <p className="text-sm text-abacos-red-dark">{workspace.error}</p> : null}
          {document ? (
            <div className="grid gap-4">
              <div className="flex flex-wrap gap-2">
                <Badge variant="blue">{document.file_type.toUpperCase()}</Badge>
                <Badge variant="outline">{document.extracted_text.length.toLocaleString("es-ES")} caracteres</Badge>
                <Badge variant="outline">{workspace.sections.length} secciones</Badge>
              </div>
              <pre className="max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md bg-abacos-light p-4 text-sm leading-7 text-abacos-black">
                {document.extracted_text}
              </pre>
            </div>
          ) : (
            <div className="rounded-md border border-dashed border-border bg-abacos-light p-6">
              <h3 className="font-semibold text-abacos-black">Todavía no hay documento subido</h3>
              <p className="mt-2 text-sm leading-6 text-abacos-gray">
                Sube un DOCX o PDF con texto extraíble para iniciar extracción, división por secciones y análisis.
              </p>
            </div>
          )}
        </SectionCard>

        <SectionCard
          title={document ? "Subir nueva versión" : "Carga del tema"}
          description="DOCX es el formato preferente. Los PDF escaneados requerirán OCR en una fase posterior."
        >
          <DocumentDropzone fileName={file?.name} onFileChange={setFile} />
          <Button className="mt-4 w-full" onClick={handleUpload} disabled={!file || uploading}>
            <UploadCloud className="h-4 w-4" aria-hidden />
            {uploading ? "Subiendo..." : "Subir documento"}
          </Button>
          <div className="mt-4 rounded-md bg-abacos-red-soft p-3 text-xs leading-5 text-abacos-red-dark">
            Si subes una nueva versión, las secciones se recalcularán. Revisa de nuevo las sugerencias antes de consolidar.
          </div>
        </SectionCard>
      </div>
    </TooltipProvider>
  );
}

export function ProjectSectionsClient({ projectId }: { projectId: string }) {
  const workspace = useProjectWorkspace(projectId);

  if (!workspace.loading && workspace.sections.length === 0) {
    return (
      <SectionCard className="mt-6" title="Sin secciones">
        <p className="text-sm leading-6 text-abacos-gray">
          Sube un documento para que el sistema detecte apartados y conceptos clave.
        </p>
      </SectionCard>
    );
  }

  return (
    <div className="mt-6 grid gap-4">
      <SectionCard
        title="Mapa de secciones"
        description="Cada apartado conserva contenido, resumen y conceptos detectados para que la revisión sea localizada."
      >
        <div className="grid gap-3 sm:grid-cols-3">
          <CompactStat label="Secciones" value={workspace.sections.length} />
          <CompactStat
            label="Conceptos"
            value={workspace.sections.reduce((total, section) => total + (section.detected_concepts?.length ?? 0), 0)}
          />
          <CompactStat
            label="Texto total"
            value={workspace.sections.reduce((total, section) => total + section.content.length, 0)}
          />
        </div>
      </SectionCard>

      {workspace.sections.map((section) => (
        <SectionCard
          key={section.id}
          title={`${section.order_index + 1}. ${section.title}`}
          description={section.summary ?? "Resumen pendiente de completar por el análisis."}
        >
          <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">
                Conceptos detectados
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(section.detected_concepts ?? []).length > 0 ? (
                  (section.detected_concepts ?? []).map((concept) => (
                    <Badge key={concept} variant="outline">
                      {concept}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-abacos-gray">Sin conceptos detectados todavía.</span>
                )}
              </div>
            </div>
            <p className="rounded-md bg-abacos-light p-4 text-sm leading-7 text-abacos-black">
              {section.content}
            </p>
          </div>
        </SectionCard>
      ))}
    </div>
  );
}

export function ProjectReportClient({
  projectId,
  reportType,
}: {
  projectId: string;
  reportType: "scientific_update" | "curriculum_mapping";
}) {
  const workspace = useProjectWorkspace(projectId);
  const report = workspace.reports.find((item) => item.report_type === reportType);
  const title = reportType === "scientific_update" ? "Informe científico" : "Informe curricular";
  const copy =
    reportType === "scientific_update"
      ? "Diagnóstico de actualización científica con propuestas localizadas y trazables."
      : "Contextualización legislativa y curricular basada en la normativa aportada por el docente.";

  return (
    <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div>
        {report ? (
          <ReportViewer title={report.title} markdown={report.content_markdown} />
        ) : (
          <SectionCard title="Informe pendiente" description={copy}>
            <p className="text-sm leading-6 text-abacos-gray">
              Genera informes con búsqueda web trazable desde el resumen del proyecto cuando el documento ya tenga secciones.
            </p>
            <Button asChild className="mt-4">
              <Link href={`/projects/${projectId}`}>
                Volver al resumen
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </Button>
          </SectionCard>
        )}
      </div>
      <SectionCard title={title} description="Criterios de uso docente">
        <div className="grid gap-3 text-sm leading-6 text-abacos-gray">
          <RuleLine icon={CheckCircle2} text="No sustituye la revisión profesional del profesor." />
          <RuleLine icon={FileText} text="No debe inventar referencias ni normativa." />
          <RuleLine icon={ClipboardCheck} text="Toda sugerencia derivada debe revisarse individualmente." />
        </div>
      </SectionCard>
    </div>
  );
}

export function ProjectReviewClient({ projectId }: { projectId: string }) {
  const workspace = useProjectWorkspace(projectId);
  const [filter, setFilter] = useState<StatusKey | "all">("all");
  const stats = useMemo(() => buildReviewStats(workspace.suggestions), [workspace.suggestions]);
  const sectionById = new Map(workspace.sections.map((section) => [section.id, section.title]));
  const filteredSuggestions =
    filter === "all" ? workspace.suggestions : workspace.suggestions.filter((suggestion) => suggestion.status === filter);

  async function handleReview(
    suggestionId: number,
    payload: { status: "approved" | "rejected" | "edited" | "pending"; proposed_change?: string },
  ) {
    try {
      await reviewSuggestion(suggestionId, payload);
      await workspace.reload();
      toast.success("Sugerencia actualizada");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo revisar la sugerencia");
    }
  }

  if (!workspace.loading && workspace.suggestions.length === 0) {
    return (
      <SectionCard className="mt-6" title="Sin sugerencias">
        <p className="text-sm leading-6 text-abacos-gray">
          Genera informes con búsqueda actualizada para crear sugerencias científicas y curriculares revisables.
        </p>
        <Button asChild className="mt-4">
          <Link href={`/projects/${projectId}`}>
            Ir al resumen
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </Button>
      </SectionCard>
    );
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mt-6 grid gap-6">
        <ReviewControlPanel stats={stats} filter={filter} onFilterChange={setFilter} />
        <div className="grid gap-4">
          {filteredSuggestions.map((suggestion) => (
            <SuggestionReviewCard
              key={suggestion.id}
              id={suggestion.id}
              section={sectionById.get(suggestion.section_id ?? 0) ?? "Sección general"}
              original={suggestion.original_fragment}
              proposed={suggestion.proposed_change}
              justification={suggestion.justification}
              source={suggestion.source_reference ?? "Sin referencia"}
              confidence={suggestion.confidence_level}
              status={suggestion.status}
              suggestionType={suggestion.suggestion_type}
              teacherNotes={suggestion.teacher_notes}
              reviewedAt={suggestion.reviewed_at}
              onReview={handleReview}
            />
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}

export function ProjectConsolidatedClient({ projectId }: { projectId: string }) {
  const workspace = useProjectWorkspace(projectId);
  const [loading, setLoading] = useState(false);
  const stats = useMemo(() => buildReviewStats(workspace.suggestions), [workspace.suggestions]);

  async function handleConsolidate() {
    setLoading(true);
    try {
      await consolidateProject(projectId);
      await workspace.reload();
      toast.success("Documento consolidado generado");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo consolidar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <SectionCard
          title="Documento consolidado"
          description="Versión final generada únicamente con sugerencias aprobadas o editadas."
        >
          <div className="rounded-md border border-abacos-yellow/50 bg-yellow-50 p-4 text-sm leading-6 text-abacos-black">
            Solo se integrarán los cambios aprobados o editados por el docente. Pendientes y rechazadas quedan fuera.
          </div>
          <Button className="mt-5" onClick={handleConsolidate} disabled={stats.integrable === 0 || loading}>
            <BookOpenCheck className="h-4 w-4" aria-hidden />
            {loading ? "Generando..." : "Generar documento consolidado"}
          </Button>
          {workspace.consolidated ? (
            <pre className="mt-5 max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md bg-abacos-light p-4 text-sm leading-7">
              {workspace.consolidated.content_markdown}
            </pre>
          ) : (
            <p className="mt-5 text-sm leading-6 text-abacos-gray">
              Aún no existe documento consolidado para este proyecto.
            </p>
          )}
        </SectionCard>

        <SectionCard title="Control de integración" description="Resumen de decisiones disponibles para consolidar.">
          <div className="grid gap-3">
            <CompactStat label="Integrables" value={stats.integrable} />
            <CompactStat label="Pendientes" value={stats.pending} />
            <CompactStat label="Rechazadas" value={stats.rejected} />
          </div>
          <div className="mt-4 rounded-md bg-abacos-red-soft p-3 text-xs leading-5 text-abacos-red-dark">
            El botón queda deshabilitado si no hay ninguna sugerencia aprobada o editada.
          </div>
        </SectionCard>
      </div>
    </TooltipProvider>
  );
}

export function ProjectResourcesClient({ projectId }: { projectId: string }) {
  const workspace = useProjectWorkspace(projectId);
  const [loadingType, setLoadingType] = useState<string | null>(null);
  const hasConsolidated = Boolean(workspace.consolidated);

  async function handleGenerate(resourceType: string) {
    setLoadingType(resourceType);
    try {
      await generateResource(projectId, resourceType);
      await workspace.reload();
      toast.success("Recurso generado");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "No se pudo generar el recurso");
    } finally {
      setLoadingType(null);
    }
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mt-6 grid gap-6">
        <SectionCard
          title="Generación de recursos didácticos"
          description="Los materiales se generan desde el documento consolidado, no desde sugerencias pendientes."
        >
          {!hasConsolidated ? (
            <div className="mb-5 flex items-start gap-3 rounded-md border border-abacos-yellow/50 bg-yellow-50 p-4 text-sm leading-6 text-abacos-black">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#7a5b00]" aria-hidden />
              <p>Genera primero el documento consolidado para activar los recursos didácticos.</p>
            </div>
          ) : null}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
            {resourceTypes.map(([type, label, description]) => (
              <ResourceActionCard
                key={type}
                title={label}
                description={description}
                disabled={!hasConsolidated || loadingType === type}
                loading={loadingType === type}
                onGenerate={() => handleGenerate(type)}
              />
            ))}
          </div>
        </SectionCard>

        {workspace.resources.length > 0 ? (
          <div className="grid gap-4">
            {workspace.resources.map((resource) => (
              <ReportViewer key={resource.id} title={resource.title} markdown={resource.content_markdown} />
            ))}
          </div>
        ) : (
          <SectionCard title="Sin recursos generados">
            <p className="text-sm leading-6 text-abacos-gray">
              Cuando generes esquema, test, presentación o guiones, aparecerán aquí en Markdown.
            </p>
          </SectionCard>
        )}
      </div>
    </TooltipProvider>
  );
}

function ProjectCommandHeader({
  project,
  stats,
  progress,
  loading,
  running,
  canRunAnalysis,
  onRunResearchAnalysis,
}: {
  project: Project | null;
  stats: ReviewStats;
  progress: number;
  loading: boolean;
  running: boolean;
  canRunAnalysis: boolean;
  onRunResearchAnalysis: () => void;
}) {
  const timelineItems = buildTimelineItems(project?.id, progress);

  return (
    <Card className="relative isolate overflow-hidden border-abacos-red-soft bg-white surface-glow">
      <div className="pointer-events-none absolute inset-y-0 right-0 z-0 hidden w-80 abacus-rail opacity-20 2xl:block" aria-hidden />
      <div className="relative z-10 grid gap-6 bg-white/95 p-4 sm:p-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            {project ? <StatusBadge status={project.status} /> : null}
            <Badge variant="secondary">Validación docente obligatoria</Badge>
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight text-abacos-black">
            {project?.title ?? "Cargando proyecto..."}
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-abacos-gray">
            {project
              ? `${project.area} · ${project.educational_level}`
              : loading
                ? "Cargando datos desde la API local..."
                : "No se ha podido cargar el proyecto."}
          </p>
          <div className="mt-5 max-w-2xl">
            <div className="flex items-center justify-between gap-3 text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">
              <span>Avance del flujo</span>
              <span>{progress}%</span>
            </div>
            <Progress className="mt-2" value={progress} />
          </div>
          <div className="mt-5">
            <WorkflowTimeline items={timelineItems} />
          </div>
        </div>
        <div className="interactive-card rounded-lg border border-border bg-white/95 p-4 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-abacos-gray">Siguiente acción</p>
              <p className="mt-2 text-sm font-semibold text-abacos-black">
                {stats.total > 0 ? "Revisar sugerencias" : "Generar informes con búsqueda"}
              </p>
            </div>
            <WandSparkles className="h-5 w-5 text-abacos-red" aria-hidden />
          </div>
          <Button className="button-glow mt-4 w-full" onClick={onRunResearchAnalysis} disabled={running || !canRunAnalysis}>
            <WandSparkles className="h-4 w-4" aria-hidden />
            {running ? "Buscando y generando..." : "Generar informes con búsqueda"}
          </Button>
          {!canRunAnalysis ? (
            <p className="mt-3 text-xs leading-5 text-abacos-gray">
              Sube un documento para detectar secciones antes de generar informes.
            </p>
          ) : null}
        </div>
      </div>
    </Card>
  );
}

function buildTimelineItems(projectId: number | undefined, progress: number) {
  const href = (path: string) => (projectId ? `/projects/${projectId}${path}` : undefined);
  return [
    { label: "Documento", href: href("/document"), done: progress >= 15, active: progress < 15 },
    { label: "Secciones", href: href("/sections"), done: progress >= 30, active: progress >= 15 && progress < 30 },
    { label: "Informes", href: href("/scientific-report"), done: progress >= 50, active: progress >= 30 && progress < 50 },
    { label: "Revisión", href: href("/review"), done: progress >= 70, active: progress >= 50 && progress < 70 },
    { label: "Consolidado", href: href("/consolidated"), done: progress >= 85, active: progress >= 70 && progress < 85 },
    { label: "Recursos", href: href("/resources"), done: progress >= 100, active: progress >= 85 && progress < 100 },
  ];
}

function WorkflowBoard({ workspace, stats }: { workspace: WorkspaceData; stats: ReviewStats }) {
  const projectId = workspace.project?.id;
  const items = [
    {
      label: "Documento",
      detail: workspace.documents[0]?.original_filename ?? "Sube el tema original.",
      href: `/projects/${projectId}/document`,
      done: workspace.documents.length > 0,
      icon: FileText,
    },
    {
      label: "Secciones",
      detail: `${workspace.sections.length} secciones detectadas.`,
      href: `/projects/${projectId}/sections`,
      done: workspace.sections.length > 0,
      icon: Layers3,
    },
    {
      label: "Informes",
      detail: `${workspace.reports.length}/2 informes disponibles.`,
      href: `/projects/${projectId}/scientific-report`,
      done: workspace.reports.length >= 2,
      icon: FileCheck2,
    },
    {
      label: "Revisión",
      detail: `${stats.reviewed}/${stats.total} sugerencias revisadas.`,
      href: `/projects/${projectId}/review`,
      done: stats.total > 0 && stats.pending === 0,
      icon: ClipboardCheck,
    },
    {
      label: "Consolidado",
      detail: workspace.consolidated ? "Documento final disponible." : "Pendiente de generar.",
      href: `/projects/${projectId}/consolidated`,
      done: Boolean(workspace.consolidated),
      icon: BookOpenCheck,
    },
    {
      label: "Recursos",
      detail: `${workspace.resources.length} recursos generados.`,
      href: `/projects/${projectId}/resources`,
      done: workspace.resources.length > 0,
      icon: Sparkles,
    },
  ];

  return (
    <SectionCard title="Flujo del proyecto" description="Controla cada fase sin perder trazabilidad documental.">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className="interactive-card group rounded-md border border-border bg-white p-4 transition hover:border-abacos-red-soft hover:bg-abacos-red-soft"
            >
              <div className="flex items-start justify-between gap-3">
                <div className={cn("grid h-9 w-9 place-items-center rounded-md transition group-hover:scale-105", item.done ? "bg-green-50 text-abacos-green" : "bg-abacos-light text-abacos-gray")}>
                  <Icon className="h-4 w-4" aria-hidden />
                </div>
                {item.done ? <CheckCircle2 className="h-4 w-4 text-abacos-green" aria-hidden /> : null}
              </div>
              <p className="mt-4 font-semibold text-abacos-black">{item.label}</p>
              <p className="mt-1 text-sm leading-6 text-abacos-gray">{item.detail}</p>
            </Link>
          );
        })}
      </div>
    </SectionCard>
  );
}

function ProjectContextPanel({ project, stats }: { project: Project | null; stats: ReviewStats }) {
  return (
    <SectionCard title="Contexto académico" description="Datos aportados por el profesor al crear el proyecto.">
      {project ? (
        <div className="grid gap-4">
          <ContextBlock label="Área o especialidad" value={project.area} />
          <ContextBlock label="Nivel educativo" value={project.educational_level} />
          <ContextBlock label="Legislación de referencia" value={project.legal_framework} />
          <ContextBlock label="Bibliografía base" value={project.bibliography_notes || "No indicada"} />
          <ContextBlock label="Instrucciones" value={project.instructions || "Sin instrucciones adicionales"} />
          <div className="rounded-md bg-abacos-light p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">Revisión</p>
            <p className="mt-2 text-sm leading-6 text-abacos-black">
              {stats.pending} pendientes · {stats.integrable} integrables · {stats.rejected} rechazadas
            </p>
          </div>
        </div>
      ) : (
        <p className="text-sm text-abacos-gray">Cargando contexto...</p>
      )}
    </SectionCard>
  );
}

function ReviewControlPanel({
  stats,
  filter,
  onFilterChange,
}: {
  stats: ReviewStats;
  filter: StatusKey | "all";
  onFilterChange: (value: StatusKey | "all") => void;
}) {
  const filters = [
    ["all", "Todas", stats.total],
    ["pending", "Pendientes", stats.pending],
    ["approved", "Aprobadas", stats.approved],
    ["edited", "Editadas", stats.edited],
    ["rejected", "Rechazadas", stats.rejected],
  ] as const;

  return (
    <SectionCard
      className="sticky top-20 z-20"
      title="Mesa de revisión docente"
      description="Decide sugerencia por sugerencia. Nada pendiente o rechazado se integrará en el consolidado."
    >
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div>
          <div className="flex flex-wrap gap-2">
            {filters.map(([value, label, count]) => (
              <button
                key={value}
                type="button"
                onClick={() => onFilterChange(value)}
                className={cn(
                  "button-premium rounded-full border px-3 py-1.5 text-sm font-semibold transition",
                  filter === value
                    ? "border-abacos-red bg-abacos-red text-white"
                    : "border-border bg-white text-abacos-gray hover:bg-abacos-red-soft hover:text-abacos-red-dark",
                )}
              >
                {label} · {count}
              </button>
            ))}
          </div>
          <div className="mt-5 h-2 overflow-hidden rounded-full bg-abacos-light">
            <div className="h-full bg-abacos-green" style={{ width: `${stats.total ? (stats.reviewed / stats.total) * 100 : 0}%` }} />
          </div>
          <p className="mt-2 text-sm text-abacos-gray">
            {stats.reviewed}/{stats.total} sugerencias revisadas. {stats.integrable} cambios podrán consolidarse.
          </p>
        </div>
        <div className="rounded-md bg-abacos-red-soft p-4 text-sm leading-6 text-abacos-red-dark">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            <p>La IA no modifica el tema final. La consolidación solo leerá decisiones aprobadas o editadas.</p>
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

function ProjectMetric({
  label,
  value,
  helper,
  icon: Icon,
  tone = "red",
}: {
  label: string;
  value: number;
  helper: string;
  icon: LucideIcon;
  tone?: "red" | "yellow" | "green" | "blue";
}) {
  const tones = {
    red: "bg-abacos-red-soft text-abacos-red-dark",
    yellow: "bg-yellow-50 text-[#7a5b00]",
    green: "bg-green-50 text-abacos-green",
    blue: "bg-blue-50 text-abacos-blue",
  };

  return (
    <Card className="interactive-card p-5">
      <div className="flex items-start justify-between gap-3">
        <div className={cn("grid h-10 w-10 place-items-center rounded-md", tones[tone])}>
          <Icon className="h-5 w-5" aria-hidden />
        </div>
        <RichTooltip
          title={label}
          detail={helper}
          recommendation="Úsalo como señal operativa, no como decisión automática."
        />
      </div>
      <p className="mt-5 text-sm font-medium text-abacos-gray">{label}</p>
      <p className="mt-2 text-3xl font-bold text-abacos-black">{value}</p>
    </Card>
  );
}

function ResourceActionCard({
  title,
  description,
  disabled,
  loading,
  onGenerate,
}: {
  title: string;
  description: string;
  disabled: boolean;
  loading: boolean;
  onGenerate: () => void;
}) {
  return (
    <article className="interactive-card sheen group rounded-md border border-border bg-white p-4">
      <div className="grid h-9 w-9 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark transition group-hover:scale-105">
        <Sparkles className="h-4 w-4" aria-hidden />
      </div>
      <h3 className="mt-4 font-semibold text-abacos-black">{title}</h3>
      <p className="mt-1 text-sm leading-6 text-abacos-gray">{description}</p>
      <Button className="button-glow mt-4 w-full" size="sm" onClick={onGenerate} disabled={disabled}>
        {loading ? "Generando..." : "Generar"}
      </Button>
    </article>
  );
}

function CompactStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-border bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">{label}</p>
      <p className="mt-2 text-lg font-bold text-abacos-black">
        {typeof value === "number" ? value.toLocaleString("es-ES") : value}
      </p>
    </div>
  );
}

function ContextBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-white p-4">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">{label}</p>
      <p className="mt-2 text-sm leading-6 text-abacos-black">{value}</p>
    </div>
  );
}

function RuleLine({ icon: Icon, text }: { icon: LucideIcon; text: string }) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-abacos-green" aria-hidden />
      <p>{text}</p>
    </div>
  );
}

function buildReviewStats(suggestions: Suggestion[]): ReviewStats {
  const pending = suggestions.filter((item) => item.status === "pending").length;
  const approved = suggestions.filter((item) => item.status === "approved").length;
  const edited = suggestions.filter((item) => item.status === "edited").length;
  const rejected = suggestions.filter((item) => item.status === "rejected").length;
  const reviewed = approved + edited + rejected;

  return {
    total: suggestions.length,
    pending,
    approved,
    edited,
    rejected,
    reviewed,
    integrable: approved + edited,
  };
}

function buildFlowProgress(workspace: WorkspaceData) {
  const completed = [
    workspace.documents.length > 0,
    workspace.sections.length > 0,
    workspace.reports.length >= 2,
    workspace.suggestions.length > 0 && buildReviewStats(workspace.suggestions).pending === 0,
    Boolean(workspace.consolidated),
    workspace.resources.length > 0,
  ].filter(Boolean).length;

  return Math.round((completed / 6) * 100);
}
