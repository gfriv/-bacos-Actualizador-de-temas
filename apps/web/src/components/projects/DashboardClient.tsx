"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { formatDistanceToNowStrict } from "date-fns";
import { es } from "date-fns/locale/es";
import { motion } from "framer-motion";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip as ChartTooltip, XAxis } from "recharts";
import {
  AlertTriangle,
  ArrowRight,
  BookOpenCheck,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileCheck2,
  FileText,
  FolderKanban,
  GraduationCap,
  ListChecks,
  PlusCircle,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  WandSparkles,
  XCircle,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card";
import { SectionCard } from "@/components/ui/SectionCard";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge, type StatusKey } from "@/components/ui/StatusBadge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { HelpTooltip, TooltipProvider } from "@/components/ui/tooltip";
import {
  getToken,
  listDocuments,
  listProjects,
  listSuggestions,
  type DocumentRecord,
  type Project,
  type Suggestion,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const statusOrder = [
  "draft",
  "document_uploaded",
  "processing",
  "reports_generated",
  "under_review",
  "consolidated",
  "resources_generated",
] as const satisfies readonly StatusKey[];

const statusLabels: Record<StatusKey, string> = {
  draft: "Borrador",
  document_uploaded: "Documento",
  processing: "Análisis",
  reports_generated: "Informes",
  under_review: "Revisión",
  consolidated: "Consolidado",
  resources_generated: "Recursos",
  error: "Error",
  pending: "Pendiente",
  approved: "Aprobada",
  rejected: "Rechazada",
  edited: "Editada",
};

const stageMeta: Record<
  (typeof statusOrder)[number],
  { icon: LucideIcon; helper: string; accent: string; soft: string }
> = {
  draft: {
    icon: FolderKanban,
    helper: "Proyecto creado pero todavía sin documento listo para analizar.",
    accent: "bg-neutral-500",
    soft: "bg-neutral-100",
  },
  document_uploaded: {
    icon: UploadCloud,
    helper: "El tema DOCX/PDF está cargado y pendiente de análisis.",
    accent: "bg-abacos-blue",
    soft: "bg-blue-50",
  },
  processing: {
    icon: Clock3,
    helper: "El sistema está extrayendo texto, dividiendo secciones o generando informes.",
    accent: "bg-abacos-blue",
    soft: "bg-blue-50",
  },
  reports_generated: {
    icon: FileCheck2,
    helper: "Ya existen informes y sugerencias que necesitan validación docente.",
    accent: "bg-abacos-yellow",
    soft: "bg-yellow-50",
  },
  under_review: {
    icon: ClipboardCheck,
    helper: "El profesor debe aceptar, rechazar, editar o dejar pendiente cada sugerencia.",
    accent: "bg-abacos-yellow",
    soft: "bg-yellow-50",
  },
  consolidated: {
    icon: BookOpenCheck,
    helper: "Documento final generado solo con sugerencias aprobadas o editadas.",
    accent: "bg-abacos-green",
    soft: "bg-green-50",
  },
  resources_generated: {
    icon: Sparkles,
    helper: "Recursos didácticos derivados del documento consolidado.",
    accent: "bg-abacos-green",
    soft: "bg-green-50",
  },
};

type ProjectAction = {
  label: string;
  detail: string;
  href: string;
  icon: LucideIcon;
  tone: "red" | "yellow" | "green" | "blue" | "gray";
};

type RiskFlag = {
  level: "critical" | "warning" | "info";
  label: string;
  detail: string;
  href: string;
  icon: LucideIcon;
};

type ProjectInsight = Project & {
  documents: DocumentRecord[];
  suggestions: Suggestion[];
  totalSuggestions: number;
  pendingCount: number;
  approvedCount: number;
  editedCount: number;
  rejectedCount: number;
  reviewedCount: number;
  validatedCount: number;
  documentName: string | null;
  nextAction: ProjectAction;
  riskFlags: RiskFlag[];
  priorityScore: number;
  lastActivityAt: string;
};

type ActivityItem = {
  id: string;
  title: string;
  detail: string;
  at: string;
  href: string;
  icon: LucideIcon;
};

export function DashboardClient() {
  const [insights, setInsights] = useState<ProjectInsight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    const token = getToken();
    setHasToken(Boolean(token));
    if (!token) {
      setLoading(false);
      return;
    }

    async function loadDashboard() {
      setLoading(true);
      setError(null);
      try {
        const projects = await listProjects();
        const sortedProjects = [...projects].sort(
          (a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at),
        );
        const enriched = await Promise.all(
          sortedProjects.map(async (project) => {
            const [documentsResult, suggestionsResult] = await Promise.allSettled([
              listDocuments(project.id),
              listSuggestions(project.id),
            ]);

            return buildProjectInsight(
              project,
              documentsResult.status === "fulfilled" ? documentsResult.value : [],
              suggestionsResult.status === "fulfilled" ? suggestionsResult.value : [],
            );
          }),
        );
        setInsights(enriched);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "No se pudo cargar el panel operativo");
      } finally {
        setLoading(false);
      }
    }

    void loadDashboard();
  }, []);

  const summary = useMemo(() => buildSummary(insights), [insights]);
  const priorityProject = useMemo(() => selectPriorityProject(insights), [insights]);
  const activity = useMemo(() => buildActivity(insights), [insights]);

  if (!hasToken) {
    return (
      <TooltipProvider>
        <UnauthenticatedDashboard />
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider delayDuration={150}>
      <div className="mt-6 grid gap-6">
        <CommandCenter
          insights={insights}
          loading={loading}
          priorityProject={priorityProject}
          summary={summary}
        />

        <motion.section
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
          initial="hidden"
          animate="show"
          variants={{
            hidden: {},
            show: { transition: { staggerChildren: 0.08 } },
          }}
        >
          <MetricCard
            label="Proyectos activos"
            value={summary.activeProjects}
            detail={`${summary.withDocuments} con documento cargado`}
            icon={FolderKanban}
            helper="Proyectos que todavía necesitan análisis, revisión, consolidación o generación de recursos."
          />
          <MetricCard
            label="Sugerencias pendientes"
            value={summary.pendingSuggestions}
            detail={`${summary.reviewProjects} temas en revisión`}
            icon={ClipboardCheck}
            helper="Sugerencias que no pueden integrarse hasta que el docente tome una decisión explícita."
            tone="yellow"
          />
          <MetricCard
            label="Cambios validados"
            value={summary.validatedSuggestions}
            detail={`${summary.approvedSuggestions} aprobados · ${summary.editedSuggestions} editados`}
            icon={ShieldCheck}
            helper="Cambios que sí pueden pasar al documento consolidado porque han sido aprobados o editados."
            tone="green"
          />
          <MetricCard
            label="Recursos listos"
            value={summary.resourcesGenerated}
            detail={`${summary.consolidatedProjects} consolidados pendientes o listos`}
            icon={Sparkles}
            helper="Proyectos que ya han generado recursos didácticos desde un documento consolidado."
            tone="blue"
          />
        </motion.section>

        <InsightCommandRow insights={insights} summary={summary} activity={activity} />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
          <PipelinePanel insights={insights} loading={loading} />
          <TraceabilityPanel insights={insights} summary={summary} />
        </div>

        <div className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <PriorityPanel insights={insights} loading={loading} />
          <ActivityPanel activity={activity} loading={loading} />
        </div>

        {error ? (
          <Card className="border-abacos-red-soft bg-abacos-red-soft p-4 text-sm text-abacos-red-dark">
            {error}
          </Card>
        ) : null}

        <ProjectsTable insights={insights.slice(0, 10)} loading={loading} />
      </div>
    </TooltipProvider>
  );
}

function UnauthenticatedDashboard() {
  return (
    <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card className="relative isolate overflow-hidden">
        <div className="pointer-events-none absolute inset-y-0 right-0 z-0 hidden w-72 abacus-rail opacity-20 2xl:block" aria-hidden />
        <div className="relative z-10 border-b border-border bg-white px-4 py-5 sm:px-6">
          <div className="mb-4 flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-abacos-red" aria-hidden />
            <span className="h-2.5 w-2.5 rounded-full bg-abacos-blue" aria-hidden />
            <span className="h-2.5 w-2.5 rounded-full bg-abacos-green" aria-hidden />
            <span className="h-2.5 w-2.5 rounded-full bg-abacos-yellow" aria-hidden />
          </div>
          <h2 className="max-w-2xl text-2xl font-bold tracking-tight text-abacos-black">
            Centro de control documental para temas académicos y oposiciones docentes.
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-abacos-gray">
            Inicia sesión para cargar documentos reales, revisar informes científicos y curriculares y consolidar
            únicamente los cambios validados por el profesor, también en temas de Infantil, Primaria, Secundaria y FP.
          </p>
        </div>
        <div className="relative z-10 grid gap-3 bg-white p-4 sm:grid-cols-2 sm:p-6 lg:grid-cols-3 2xl:grid-cols-5">
          {[
            ["1", "Documento", "DOCX o PDF con texto extraíble."],
            ["2", "Secciones", "Extracción y división del tema."],
            ["3", "Informes", "Actualización científica y curricular."],
            ["4", "Revisión", "Validación humana obligatoria."],
            ["5", "Recursos", "Materiales derivados del consolidado."],
          ].map(([step, title, copy]) => (
            <div key={step} className="min-w-0 rounded-md border border-border bg-abacos-light p-4">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-abacos-red text-sm font-bold text-white">
                {step}
              </div>
              <h3 className="mt-3 text-base font-semibold leading-6 text-abacos-black">{title}</h3>
              <p className="mt-1 text-xs leading-5 text-abacos-gray">{copy}</p>
            </div>
          ))}
        </div>
      </Card>

      <SectionCard title="Sesión requerida">
        <div className="flex items-start gap-3 rounded-md bg-abacos-red-soft p-3 text-sm leading-6 text-abacos-red-dark">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          <p>El panel muestra documentos docentes privados, estados de revisión y trazabilidad de decisiones.</p>
        </div>
        <Button asChild className="mt-4 w-full">
          <Link href="/login">Ir al acceso</Link>
        </Button>
      </SectionCard>
    </div>
  );
}

function CommandCenter({
  insights,
  loading,
  priorityProject,
  summary,
}: {
  insights: ProjectInsight[];
  loading: boolean;
  priorityProject?: ProjectInsight;
  summary: DashboardSummary;
}) {
  const hasProjects = insights.length > 0;
  const ActionIcon = priorityProject?.nextAction.icon ?? PlusCircle;

  return (
    <Card className="relative overflow-hidden border-abacos-red-soft bg-white surface-glow">
      <div className="absolute inset-0 premium-grid opacity-50" aria-hidden />
      <div className="absolute inset-y-0 right-0 hidden w-[30rem] abacus-rail opacity-35 xl:block" aria-hidden />
      <div className="relative grid gap-6 p-4 sm:p-6 xl:grid-cols-[minmax(0,1fr)_minmax(320px,390px)] xl:items-stretch">
        <div className="flex flex-col justify-between gap-8">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-abacos-red-soft px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-abacos-red-dark">
                Panel profesional Ábacos
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-white px-3 py-1 text-xs font-semibold text-abacos-gray">
                <ShieldCheck className="h-3.5 w-3.5 text-abacos-green" aria-hidden />
                La IA propone, el profesor valida
              </span>
              <span className="inline-flex items-center gap-1 rounded-full border border-border bg-white px-3 py-1 text-xs font-semibold text-abacos-gray">
                <GraduationCap className="h-3.5 w-3.5 text-abacos-blue" aria-hidden />
                Infantil · Primaria · Secundaria · FP
              </span>
            </div>
            <h2 className="mt-4 max-w-3xl text-xl font-bold tracking-tight text-abacos-black sm:text-2xl md:text-3xl">
              Centro de control para actualización científica, revisión curricular, oposiciones docentes y recursos didácticos.
            </h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-abacos-gray">
              Prioriza temas bloqueados, separa sugerencias pendientes de cambios validados y mantiene visible la
              trazabilidad antes de generar documentos consolidados para aula, temarios o preparación de tribunal.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <ControlPill
              label="Trazabilidad"
              value={`${summary.totalSuggestions} sugerencias`}
              helper="Cada sugerencia conserva fragmento original, propuesta, justificación y estado docente."
            />
            <ControlPill
              label="Revisión humana"
              value={`${summary.reviewedSuggestions}/${summary.totalSuggestions}`}
              helper="Solo las sugerencias aprobadas o editadas pueden integrarse en el documento final."
            />
            <ControlPill
              label="Bloqueos"
              value={`${summary.alerts} alertas`}
              helper="Alertas derivadas de documentos ausentes, sugerencias pendientes, errores o falta de cambios validados."
            />
          </div>
        </div>

        <div className="rounded-lg border border-border bg-white/95 p-4 shadow-soft">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-abacos-gray">
                Acción prioritaria
              </p>
              <h3 className="mt-2 text-lg font-bold leading-6 text-abacos-black">
                {loading
                  ? "Cargando proyectos"
                  : priorityProject
                    ? priorityProject.title
                    : "Crear el primer proyecto"}
              </h3>
            </div>
            <div className="grid h-10 w-10 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark">
              <ActionIcon className="h-5 w-5" aria-hidden />
            </div>
          </div>

          {priorityProject ? (
            <div className="mt-4 grid gap-3 text-sm">
              <div className="flex items-center justify-between gap-3">
                <span className="text-abacos-gray">Estado</span>
                <StatusBadge status={priorityProject.status} />
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-abacos-gray">Documento</span>
                <span className="max-w-[190px] truncate font-medium text-abacos-black">
                  {priorityProject.documentName ?? "Sin documento"}
                </span>
              </div>
              <div className="flex items-center justify-between gap-3">
                <span className="text-abacos-gray">Pendiente</span>
                <span className="font-semibold text-abacos-black">{priorityProject.nextAction.label}</span>
              </div>
              <p className="rounded-md bg-abacos-light p-3 text-xs leading-5 text-abacos-gray">
                {priorityProject.nextAction.detail}
              </p>
            </div>
          ) : (
            <p className="mt-4 rounded-md bg-abacos-light p-3 text-sm leading-6 text-abacos-gray">
              {hasProjects
                ? "No hay acciones urgentes. Revisa la tabla para continuar el flujo."
                : "Empieza creando un proyecto de mejora y subiendo un tema DOCX o PDF."}
            </p>
          )}

          <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
            <Button asChild className="button-glow sheen">
              <Link href={priorityProject ? priorityProject.nextAction.href : "/projects/new"}>
                {priorityProject ? priorityProject.nextAction.label : "Nuevo proyecto"}
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/projects/new">
                <PlusCircle className="h-4 w-4" aria-hidden />
                Crear otro tema
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}

function InsightCommandRow({
  insights,
  summary,
  activity,
}: {
  insights: ProjectInsight[];
  summary: DashboardSummary;
  activity: ActivityItem[];
}) {
  const chartData = statusOrder.map((status) => ({
    name: statusLabels[status],
    proyectos: insights.filter((project) => project.status === status).length,
  }));
  const reviewRatio = summary.totalSuggestions
    ? Math.round((summary.reviewedSuggestions / summary.totalSuggestions) * 100)
    : 0;

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
      <Card className="overflow-hidden border-abacos-red-soft bg-white surface-glow">
        <div className="border-b border-border bg-white px-5 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-abacos-red-dark">
                Radar operativo
              </p>
              <h2 className="mt-1 text-base font-semibold text-abacos-black">
                Distribución viva del flujo documental
              </h2>
            </div>
            <HoverCard>
              <HoverCardTrigger asChild>
                <button className="rounded-full border border-border bg-white px-3 py-1.5 text-xs font-semibold text-abacos-gray transition hover:border-abacos-red-soft hover:bg-abacos-red-soft hover:text-abacos-red-dark">
                  Cómo leerlo
                </button>
              </HoverCardTrigger>
              <HoverCardContent>
                <p className="font-semibold text-abacos-black">Lectura rápida</p>
                <p className="mt-1 text-abacos-gray">
                  El gráfico ayuda a ver dónde se acumula trabajo: documentos sin analizar, temas en revisión o recursos ya generados.
                </p>
              </HoverCardContent>
            </HoverCard>
          </div>
        </div>
        <div className="h-64 p-3 sm:h-72 sm:p-5">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ left: 0, right: 10, top: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="abacosArea" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="#B20D22" stopOpacity={0.32} />
                  <stop offset="100%" stopColor="#B20D22" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#e8e2de" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#4A4A4A" }} tickLine={false} axisLine={false} />
              <ChartTooltip
                contentStyle={{
                  border: "1px solid #e3dad6",
                  borderRadius: 8,
                  boxShadow: "0 12px 30px rgba(30,30,30,0.08)",
                }}
              />
              <Area
                type="monotone"
                dataKey="proyectos"
                stroke="#B20D22"
                strokeWidth={3}
                fill="url(#abacosArea)"
                activeDot={{ r: 5, stroke: "#8F0A1B", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="relative overflow-hidden border-border bg-abacos-black p-5 text-white surface-glow">
        <div className="absolute inset-0 premium-grid opacity-[0.08]" aria-hidden />
        <div className="relative">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/65">
                Control de calidad
              </p>
              <h2 className="mt-2 text-xl font-bold">Validación docente</h2>
            </div>
            <div className="grid h-11 w-11 place-items-center rounded-md bg-white/10 text-white">
              <ShieldCheck className="h-5 w-5" aria-hidden />
            </div>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <DarkStat label="Revisado" value={`${reviewRatio}%`} />
            <DarkStat label="Integrable" value={summary.validatedSuggestions} />
            <DarkStat label="Alertas" value={summary.alerts} />
          </div>
          <div className="mt-5 rounded-md border border-white/10 bg-white/5 p-4">
            <p className="text-sm font-semibold">Última señal operativa</p>
            <p className="mt-1 text-sm leading-6 text-white/70">
              {activity[0]
                ? `${activity[0].title}: ${activity[0].detail}`
                : "Aún no hay actividad registrada en este entorno."}
            </p>
          </div>
          <Button asChild className="button-glow mt-5 w-full">
            <Link href="/projects/new">
              <PlusCircle className="h-4 w-4" aria-hidden />
              Nuevo proyecto de mejora
            </Link>
          </Button>
        </div>
      </Card>
    </div>
  );
}

function DarkStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-white/10 bg-white/5 p-3">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-white/55">{label}</p>
      <p className="mt-2 text-xl font-bold text-white">{value}</p>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  helper,
  tone = "red",
}: {
  label: string;
  value: number;
  detail: string;
  icon: LucideIcon;
  helper: string;
  tone?: "red" | "yellow" | "green" | "blue";
}) {
  const toneClass = {
    red: "bg-abacos-red-soft text-abacos-red-dark",
    yellow: "bg-yellow-50 text-[#7a5b00]",
    green: "bg-green-50 text-abacos-green",
    blue: "bg-blue-50 text-abacos-blue",
  }[tone];

  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 16 },
        show: { opacity: 1, y: 0 },
      }}
      whileHover={{ y: -3, transition: { duration: 0.18 } }}
    >
    <Card className="sheen group relative overflow-hidden p-5 surface-glow">
      <div className="absolute left-0 top-0 h-full w-1 bg-abacos-red opacity-80" aria-hidden />
      <div className="flex items-start justify-between gap-4">
        <div className={cn("grid h-10 w-10 place-items-center rounded-md", toneClass)}>
          <Icon className="h-5 w-5" aria-hidden />
        </div>
        <HelpTooltip label={helper} />
      </div>
      <p className="mt-5 text-sm font-medium text-abacos-gray">{label}</p>
      <p className="mt-2 text-3xl font-bold text-abacos-black">{value}</p>
      <p className="mt-1 text-xs leading-5 text-abacos-gray">{detail}</p>
    </Card>
    </motion.div>
  );
}

function PipelinePanel({ insights, loading }: { insights: ProjectInsight[]; loading: boolean }) {
  const counts = useMemo(
    () =>
      statusOrder.map((status) => ({
        status,
        label: statusLabels[status],
        count: insights.filter((project) => project.status === status).length,
      })),
    [insights],
  );
  const total = Math.max(1, insights.length);

  return (
    <SectionCard
      title="Mapa del flujo documental"
      description="Localiza de un vistazo en qué fase están los temas y dónde se concentra el trabajo pendiente."
    >
      {loading ? (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(11.25rem,1fr))] gap-3">
          {statusOrder.map((status) => (
            <Skeleton key={status} className="h-36" />
          ))}
        </div>
      ) : (
      <div className="grid grid-cols-[repeat(auto-fit,minmax(11.25rem,1fr))] gap-3">
        {counts.map((item) => {
          const meta = stageMeta[item.status];
          const Icon = meta.icon;
          return (
            <div
              key={item.status}
              className="interactive-card relative min-h-36 overflow-hidden rounded-md border border-border bg-white p-4"
            >
              <div className={cn("absolute inset-x-0 top-0 h-1", meta.accent)} aria-hidden />
              <div className="flex items-start justify-between gap-3">
                <div className={cn("grid h-9 w-9 place-items-center rounded-md", meta.soft)}>
                  <Icon className="h-4 w-4 text-abacos-black" aria-hidden />
                </div>
                <HelpTooltip label={meta.helper} />
              </div>
              <p className="mt-4 text-2xl font-bold text-abacos-black">{item.count}</p>
              <p className="mt-1 break-words text-sm font-semibold leading-5 text-abacos-black">{item.label}</p>
              <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-abacos-light">
                <div
                  className={cn("h-full rounded-full", meta.accent)}
                  style={{ width: `${Math.max(8, (item.count / total) * 100)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      )}
    </SectionCard>
  );
}

function TraceabilityPanel({
  insights,
  summary,
}: {
  insights: ProjectInsight[];
  summary: DashboardSummary;
}) {
  const alerts = insights.flatMap((project) =>
    project.riskFlags.map((flag) => ({
      ...flag,
      projectTitle: project.title,
      projectId: project.id,
    })),
  );

  return (
    <SectionCard
      title="Control docente y alertas"
      description="Resumen de decisiones revisables antes de consolidar documentos."
    >
      <div className="rounded-md border border-border bg-abacos-light p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-abacos-black">Distribución de sugerencias</p>
            <p className="mt-1 text-xs leading-5 text-abacos-gray">
              Pendientes, aprobadas, editadas y rechazadas mantienen trazabilidad individual.
            </p>
          </div>
          <HelpTooltip label="El documento consolidado solo puede usar sugerencias aprobadas o editadas. Las pendientes y rechazadas quedan fuera." />
        </div>
        <ReviewDistribution summary={summary} />
      </div>

      <div className="mt-4 grid gap-3">
        {alerts.length === 0 ? (
          <div className="flex items-start gap-3 rounded-md border border-border bg-white p-4 text-sm leading-6 text-abacos-gray">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-abacos-green" aria-hidden />
            <p>No hay bloqueos críticos. Los proyectos pueden avanzar según su fase actual.</p>
          </div>
        ) : (
          alerts.slice(0, 5).map((alert) => {
            const Icon = alert.icon;
            return (
              <Link
                key={`${alert.projectId}-${alert.label}`}
                href={alert.href}
                className={cn(
                  "rounded-md border p-3 transition hover:bg-white",
                  alert.level === "critical"
                    ? "border-abacos-red-soft bg-abacos-red-soft"
                    : "border-border bg-white",
                )}
              >
                <div className="flex items-start gap-3">
                  <Icon
                    className={cn(
                      "mt-0.5 h-4 w-4 shrink-0",
                      alert.level === "critical" ? "text-abacos-red-dark" : "text-abacos-yellow",
                    )}
                    aria-hidden
                  />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-abacos-black">{alert.label}</p>
                    <p className="mt-0.5 truncate text-xs text-abacos-gray">{alert.projectTitle}</p>
                    <p className="mt-1 text-xs leading-5 text-abacos-gray">{alert.detail}</p>
                  </div>
                </div>
              </Link>
            );
          })
        )}
      </div>
    </SectionCard>
  );
}

function PriorityPanel({ insights, loading }: { insights: ProjectInsight[]; loading: boolean }) {
  const priorities = [...insights]
    .filter((project) => project.priorityScore > 0 || project.status !== "resources_generated")
    .sort((a, b) => b.priorityScore - a.priorityScore || Date.parse(b.updated_at) - Date.parse(a.updated_at))
    .slice(0, 5);

  return (
    <SectionCard
      title="Bandeja de prioridades"
      description="Ordena el trabajo por bloqueo, revisión pendiente y avance del flujo."
    >
      {loading ? <p className="text-sm text-abacos-gray">Calculando prioridades...</p> : null}
      {!loading && priorities.length === 0 ? (
        <div className="rounded-md border border-border bg-abacos-light p-5">
          <h3 className="font-semibold text-abacos-black">No hay tareas abiertas</h3>
          <p className="mt-1 text-sm leading-6 text-abacos-gray">
            Crea un proyecto para iniciar el ciclo documento, análisis, revisión y recursos.
          </p>
          <Button asChild className="mt-4">
            <Link href="/projects/new">
              <PlusCircle className="h-4 w-4" aria-hidden />
              Nuevo tema
            </Link>
          </Button>
        </div>
      ) : null}
      <div className="grid gap-3">
        {priorities.map((project) => {
          const ActionIcon = project.nextAction.icon;
          return (
            <Link
              key={project.id}
              href={project.nextAction.href}
              className="rounded-md border border-border bg-white p-4 transition hover:border-abacos-red-soft hover:bg-abacos-red-soft"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-abacos-black">{project.title}</p>
                  <p className="mt-1 text-xs text-abacos-gray">
                    {project.area} · {project.educational_level}
                  </p>
                </div>
                <StatusBadge status={project.status} />
              </div>
              <div className="mt-3 flex items-start gap-3 rounded-md bg-abacos-light p-3">
                <ActionIcon className="mt-0.5 h-4 w-4 shrink-0 text-abacos-red" aria-hidden />
                <div>
                  <p className="text-sm font-semibold text-abacos-black">{project.nextAction.label}</p>
                  <p className="mt-1 text-xs leading-5 text-abacos-gray">{project.nextAction.detail}</p>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </SectionCard>
  );
}

function ActivityPanel({ activity, loading }: { activity: ActivityItem[]; loading: boolean }) {
  return (
    <SectionCard
      title="Última actividad"
      description="Registro operativo de actualizaciones, sugerencias y decisiones recientes."
    >
      {loading ? <p className="text-sm text-abacos-gray">Cargando actividad...</p> : null}
      {!loading && activity.length === 0 ? (
        <div className="rounded-md border border-border bg-abacos-light p-5">
          <h3 className="font-semibold text-abacos-black">Todavía no hay actividad</h3>
          <p className="mt-1 text-sm leading-6 text-abacos-gray">
            Las subidas, sugerencias revisadas y consolidaciones aparecerán aquí.
          </p>
        </div>
      ) : null}
      <div className="grid gap-3">
        {activity.slice(0, 6).map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.id}
              href={item.href}
              className="flex items-start gap-3 rounded-md border border-border bg-white p-3 transition hover:bg-abacos-light"
            >
              <div className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-abacos-red-soft text-abacos-red-dark">
                <Icon className="h-4 w-4" aria-hidden />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-abacos-black">{item.title}</p>
                <p className="mt-1 text-xs leading-5 text-abacos-gray">{item.detail}</p>
                <p className="mt-1 text-xs font-medium text-abacos-gray">{formatRelative(item.at)}</p>
              </div>
            </Link>
          );
        })}
      </div>
    </SectionCard>
  );
}

function ProjectsTable({
  insights,
  loading,
}: {
  insights: ProjectInsight[];
  loading: boolean;
}) {
  return (
    <SectionCard
      title="Cartera de temas"
      description="Tabla operativa para retomar cada proyecto, revisar bloqueos y avanzar al siguiente paso."
    >
      {loading ? <p className="text-sm text-abacos-gray">Cargando proyectos...</p> : null}
      {!loading && insights.length === 0 ? (
        <div className="grid gap-4 rounded-md border border-dashed border-border bg-abacos-light p-6 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <h3 className="font-semibold text-abacos-black">Todavía no hay proyectos</h3>
            <p className="mt-1 text-sm leading-6 text-abacos-gray">
              Crea un proyecto, sube un tema DOCX/PDF y genera informes con búsqueda trazable para empezar a revisar sugerencias.
            </p>
          </div>
          <Button asChild>
            <Link href="/projects/new">
              <PlusCircle className="h-4 w-4" aria-hidden />
              Nuevo tema
            </Link>
          </Button>
        </div>
      ) : null}
      {insights.length > 0 ? (
        <>
          <div className="grid gap-3 lg:hidden">
            {insights.map((project) => (
              <Link
                key={project.id}
                href={project.nextAction.href}
                className="interactive-card rounded-lg border border-border bg-white p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="line-clamp-2 text-sm font-semibold leading-5 text-abacos-black">{project.title}</p>
                    <p className="mt-1 flex items-center gap-1 text-xs text-abacos-gray">
                      <GraduationCap className="h-3.5 w-3.5 shrink-0" aria-hidden />
                      <span className="truncate">
                        {project.area} - {project.educational_level}
                      </span>
                    </p>
                  </div>
                  <StatusBadge status={project.status} />
                </div>
                <div className="mt-4 rounded-md bg-abacos-light p-3">
                  <ReviewMeter project={project} />
                </div>
                <div className="mt-4 flex items-center justify-between gap-3">
                  <span className="min-w-0 truncate text-xs text-abacos-gray">
                    {project.documentName ?? "Pendiente de subida"}
                  </span>
                  <span className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-abacos-red-dark">
                    {project.nextAction.label}
                    <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                  </span>
                </div>
              </Link>
            ))}
          </div>

          <div className="hidden lg:block">
            <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tema</TableHead>
              <TableHead>Documento</TableHead>
              <TableHead>Revisión</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Siguiente paso</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {insights.map((project) => (
              <TableRow key={project.id}>
                <TableCell className="min-w-[260px]">
                  <Link
                    href={`/projects/${project.id}`}
                    className="flex items-start gap-3 font-semibold text-abacos-black hover:text-abacos-red-dark"
                  >
                    <FileText className="mt-0.5 h-4 w-4 shrink-0 text-abacos-red" aria-hidden />
                    <span>
                      <span className="block leading-5">{project.title}</span>
                      <span className="mt-1 flex items-center gap-1 text-xs font-normal text-abacos-gray">
                        <GraduationCap className="h-3.5 w-3.5" aria-hidden />
                        {project.area} · {project.educational_level}
                      </span>
                    </span>
                  </Link>
                </TableCell>
                <TableCell className="min-w-[180px]">
                  <span className="block max-w-[220px] truncate text-sm text-abacos-black">
                    {project.documentName ?? "Pendiente de subida"}
                  </span>
                  <span className="mt-1 block text-xs text-abacos-gray">
                    Actualizado {formatRelative(project.lastActivityAt)}
                  </span>
                </TableCell>
                <TableCell className="min-w-[210px]">
                  <ReviewMeter project={project} />
                </TableCell>
                <TableCell>
                  <StatusBadge status={project.status} />
                </TableCell>
                <TableCell className="min-w-[220px]">
                  <Button asChild size="sm" variant={project.nextAction.tone === "red" ? "default" : "outline"}>
                    <Link href={project.nextAction.href}>
                      {project.nextAction.label}
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
            </Table>
          </div>
        </>
      ) : null}
    </SectionCard>
  );
}

function ControlPill({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <div className="rounded-md border border-border bg-white/90 p-3 shadow-sm">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-abacos-gray">{label}</p>
        <HelpTooltip label={helper} />
      </div>
      <p className="mt-2 text-sm font-bold text-abacos-black">{value}</p>
    </div>
  );
}

function ReviewDistribution({ summary }: { summary: DashboardSummary }) {
  const total = Math.max(1, summary.totalSuggestions);
  const segments = [
    { label: "Pendientes", value: summary.pendingSuggestions, className: "bg-abacos-yellow" },
    { label: "Aprobadas", value: summary.approvedSuggestions, className: "bg-abacos-green" },
    { label: "Editadas", value: summary.editedSuggestions, className: "bg-abacos-blue" },
    { label: "Rechazadas", value: summary.rejectedSuggestions, className: "bg-neutral-400" },
  ];

  return (
    <div className="mt-4">
      <div className="flex h-2 overflow-hidden rounded-full bg-white">
        {segments.map((segment) => (
          <div
            key={segment.label}
            className={segment.className}
            style={{ width: `${summary.totalSuggestions === 0 ? 25 : Math.max(4, (segment.value / total) * 100)}%` }}
          />
        ))}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
        {segments.map((segment) => (
          <div key={segment.label} className="rounded-md bg-white p-2">
            <p className="font-semibold text-abacos-black">{segment.value}</p>
            <p className="mt-0.5 text-abacos-gray">{segment.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReviewMeter({ project }: { project: ProjectInsight }) {
  if (project.totalSuggestions === 0) {
    return (
      <div className="rounded-md bg-abacos-light px-3 py-2 text-xs leading-5 text-abacos-gray">
        Sin sugerencias generadas
      </div>
    );
  }

  const reviewedPercentage = Math.round((project.reviewedCount / project.totalSuggestions) * 100);
  const pendingPercentage = Math.max(0, 100 - reviewedPercentage);

  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="font-semibold text-abacos-black">{reviewedPercentage}% revisado</span>
        <span className="text-abacos-gray">{project.pendingCount} pendientes</span>
      </div>
      <div className="mt-2 flex h-1.5 overflow-hidden rounded-full bg-abacos-light">
        <div className="bg-abacos-green" style={{ width: `${reviewedPercentage}%` }} />
        <div className="bg-abacos-yellow" style={{ width: `${pendingPercentage}%` }} />
      </div>
      <p className="mt-1 text-xs text-abacos-gray">
        {project.validatedCount} integrables · {project.rejectedCount} rechazadas
      </p>
    </div>
  );
}

function buildProjectInsight(
  project: Project,
  documents: DocumentRecord[],
  suggestions: Suggestion[],
): ProjectInsight {
  const pendingCount = suggestions.filter((suggestion) => suggestion.status === "pending").length;
  const approvedCount = suggestions.filter((suggestion) => suggestion.status === "approved").length;
  const editedCount = suggestions.filter((suggestion) => suggestion.status === "edited").length;
  const rejectedCount = suggestions.filter((suggestion) => suggestion.status === "rejected").length;
  const reviewedCount = approvedCount + editedCount + rejectedCount;
  const validatedCount = approvedCount + editedCount;
  const documentName = documents[0]?.original_filename ?? null;
  const lastSuggestionActivity = suggestions
    .map((suggestion) => suggestion.reviewed_at ?? suggestion.created_at)
    .sort((a, b) => Date.parse(b) - Date.parse(a))[0];
  const lastActivityAt = [project.updated_at, documents[0]?.created_at, lastSuggestionActivity]
    .filter(Boolean)
    .sort((a, b) => Date.parse(b) - Date.parse(a))[0] as string;

  const nextAction = buildNextAction(project, documents, pendingCount, validatedCount);
  const riskFlags = buildRiskFlags(project, documents, suggestions, pendingCount, validatedCount);
  const priorityScore = scoreProject(project, pendingCount, validatedCount, riskFlags);

  return {
    ...project,
    documents,
    suggestions,
    totalSuggestions: suggestions.length,
    pendingCount,
    approvedCount,
    editedCount,
    rejectedCount,
    reviewedCount,
    validatedCount,
    documentName,
    nextAction,
    riskFlags,
    priorityScore,
    lastActivityAt: lastActivityAt ?? project.updated_at,
  };
}

function buildNextAction(
  project: Project,
  documents: DocumentRecord[],
  pendingCount: number,
  validatedCount: number,
): ProjectAction {
  const projectHref = `/projects/${project.id}`;
  const actions: Partial<Record<StatusKey, ProjectAction>> = {
    draft: {
      label: documents.length > 0 ? "Generar informes" : "Subir documento",
      detail: documents.length > 0 ? "El documento está cargado; falta lanzar el análisis con búsqueda." : "Añade el tema original en DOCX o PDF.",
      href: documents.length > 0 ? projectHref : `/projects/${project.id}/document`,
      icon: documents.length > 0 ? WandSparkles : UploadCloud,
      tone: "red",
    },
    document_uploaded: {
      label: "Generar informes",
      detail: "Lanza el análisis científico y curricular para crear sugerencias revisables.",
      href: projectHref,
      icon: WandSparkles,
      tone: "red",
    },
    processing: {
      label: "Comprobar análisis",
      detail: "Revisa si el proceso ha terminado o si necesita reintento.",
      href: projectHref,
      icon: Clock3,
      tone: "blue",
    },
    reports_generated: {
      label: "Revisar sugerencias",
      detail: pendingCount > 0 ? `Hay ${pendingCount} sugerencias pendientes de decisión.` : "No hay pendientes; comprueba si procede consolidar.",
      href: `/projects/${project.id}/review`,
      icon: ClipboardCheck,
      tone: "red",
    },
    under_review: {
      label: pendingCount > 0 ? "Continuar revisión" : "Generar consolidado",
      detail: pendingCount > 0 ? `Quedan ${pendingCount} sugerencias sin validar.` : `${validatedCount} cambios pueden integrarse.`,
      href: pendingCount > 0 ? `/projects/${project.id}/review` : `/projects/${project.id}/consolidated`,
      icon: pendingCount > 0 ? ClipboardCheck : BookOpenCheck,
      tone: pendingCount > 0 ? "red" : "green",
    },
    consolidated: {
      label: "Generar recursos",
      detail: "El documento consolidado ya puede alimentar esquema, test y guiones.",
      href: `/projects/${project.id}/resources`,
      icon: Sparkles,
      tone: "green",
    },
    resources_generated: {
      label: "Ver recursos",
      detail: "Consulta los materiales didácticos derivados del documento final.",
      href: `/projects/${project.id}/resources`,
      icon: Sparkles,
      tone: "blue",
    },
    error: {
      label: "Resolver incidencia",
      detail: "El proyecto está en error y necesita revisión técnica o reintento.",
      href: projectHref,
      icon: AlertTriangle,
      tone: "red",
    },
  };

  return actions[project.status] ?? {
    label: "Abrir proyecto",
    detail: "Continúa el flujo documental desde la vista del proyecto.",
    href: projectHref,
    icon: ArrowRight,
    tone: "gray",
  };
}

function buildRiskFlags(
  project: Project,
  documents: DocumentRecord[],
  suggestions: Suggestion[],
  pendingCount: number,
  validatedCount: number,
): RiskFlag[] {
  const flags: RiskFlag[] = [];

  if (project.status === "error") {
    flags.push({
      level: "critical",
      label: "Proyecto en error",
      detail: "Revisa el proceso antes de continuar con informes o consolidación.",
      href: `/projects/${project.id}`,
      icon: AlertTriangle,
    });
  }

  if (documents.length === 0) {
    flags.push({
      level: "warning",
      label: "Sin documento original",
      detail: "No se puede analizar ni consolidar un tema sin DOCX/PDF.",
      href: `/projects/${project.id}/document`,
      icon: UploadCloud,
    });
  }

  if (["reports_generated", "under_review"].includes(project.status) && pendingCount > 0) {
    flags.push({
      level: "warning",
      label: "Revisión docente pendiente",
      detail: `${pendingCount} sugerencias siguen bloqueando la consolidación completa.`,
      href: `/projects/${project.id}/review`,
      icon: ClipboardCheck,
    });
  }

  if (["reports_generated", "under_review"].includes(project.status) && suggestions.length === 0) {
    flags.push({
      level: "warning",
      label: "Informes sin sugerencias visibles",
      detail: "Comprueba que el análisis se haya completado correctamente.",
      href: `/projects/${project.id}`,
      icon: AlertTriangle,
    });
  }

  if (project.status === "under_review" && pendingCount === 0 && validatedCount === 0) {
    flags.push({
      level: "info",
      label: "Sin cambios integrables",
      detail: "Todas las sugerencias están rechazadas o no hay cambios aprobados.",
      href: `/projects/${project.id}/review`,
      icon: XCircle,
    });
  }

  return flags;
}

function scoreProject(
  project: Project,
  pendingCount: number,
  validatedCount: number,
  riskFlags: RiskFlag[],
) {
  const riskScore = riskFlags.reduce((total, flag) => {
    if (flag.level === "critical") return total + 80;
    if (flag.level === "warning") return total + 45;
    return total + 20;
  }, 0);
  const statusScore: Partial<Record<StatusKey, number>> = {
    error: 100,
    under_review: 70,
    reports_generated: 65,
    document_uploaded: 45,
    processing: 30,
    draft: 25,
    consolidated: validatedCount > 0 ? 35 : 20,
    resources_generated: 0,
  };

  return riskScore + (statusScore[project.status] ?? 0) + pendingCount * 4;
}

type DashboardSummary = ReturnType<typeof buildSummary>;

function buildSummary(insights: ProjectInsight[]) {
  const totalSuggestions = insights.reduce((total, project) => total + project.totalSuggestions, 0);
  const pendingSuggestions = insights.reduce((total, project) => total + project.pendingCount, 0);
  const approvedSuggestions = insights.reduce((total, project) => total + project.approvedCount, 0);
  const editedSuggestions = insights.reduce((total, project) => total + project.editedCount, 0);
  const rejectedSuggestions = insights.reduce((total, project) => total + project.rejectedCount, 0);
  const reviewedSuggestions = approvedSuggestions + editedSuggestions + rejectedSuggestions;

  return {
    totalProjects: insights.length,
    activeProjects: insights.filter((project) => project.status !== "resources_generated").length,
    withDocuments: insights.filter((project) => project.documents.length > 0).length,
    reviewProjects: insights.filter((project) =>
      ["reports_generated", "under_review"].includes(project.status),
    ).length,
    consolidatedProjects: insights.filter((project) =>
      ["consolidated", "resources_generated"].includes(project.status),
    ).length,
    resourcesGenerated: insights.filter((project) => project.status === "resources_generated").length,
    totalSuggestions,
    pendingSuggestions,
    approvedSuggestions,
    editedSuggestions,
    rejectedSuggestions,
    reviewedSuggestions,
    validatedSuggestions: approvedSuggestions + editedSuggestions,
    alerts: insights.reduce((total, project) => total + project.riskFlags.length, 0),
  };
}

function selectPriorityProject(insights: ProjectInsight[]) {
  return [...insights].sort((a, b) => b.priorityScore - a.priorityScore || Date.parse(b.updated_at) - Date.parse(a.updated_at))[0];
}

function buildActivity(insights: ProjectInsight[]): ActivityItem[] {
  const activity: ActivityItem[] = [];

  insights.forEach((project) => {
    activity.push({
      id: `project-${project.id}`,
      title: project.title,
      detail: `Proyecto en estado ${statusLabels[project.status].toLowerCase()}.`,
      at: project.updated_at,
      href: `/projects/${project.id}`,
      icon: FolderKanban,
    });

    project.documents.forEach((document) => {
      activity.push({
        id: `document-${document.id}`,
        title: document.original_filename,
        detail: `Documento original asociado a ${project.title}.`,
        at: document.created_at,
        href: `/projects/${project.id}/document`,
        icon: FileText,
      });
    });

    project.suggestions.slice(0, 3).forEach((suggestion) => {
      activity.push({
        id: `suggestion-${suggestion.id}`,
        title:
          suggestion.status === "pending"
            ? "Sugerencia pendiente de revisión"
            : `Sugerencia ${statusLabels[suggestion.status].toLowerCase()}`,
        detail: `${project.title} · ${suggestion.suggestion_type.replaceAll("_", " ")}`,
        at: suggestion.reviewed_at ?? suggestion.created_at,
        href: `/projects/${project.id}/review`,
        icon: suggestion.status === "rejected" ? XCircle : ListChecks,
      });
    });
  });

  return activity.sort((a, b) => Date.parse(b.at) - Date.parse(a.at));
}

function formatRelative(date: string) {
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return "sin fecha";
  return `hace ${formatDistanceToNowStrict(parsed, { locale: es })}`;
}

export function NewProjectAction() {
  return (
    <Button asChild>
      <Link href="/projects/new">
        <PlusCircle className="h-4 w-4" aria-hidden />
        Nuevo proyecto de mejora
      </Link>
    </Button>
  );
}
