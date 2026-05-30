import type { StatusKey } from "@/components/ui/StatusBadge";

export const dashboardMetrics = [
  { label: "Proyectos recientes", value: "12", tone: "red" },
  { label: "Temas en análisis", value: "4", tone: "blue" },
  { label: "Informes pendientes", value: "7", tone: "yellow" },
  { label: "Documentos consolidados", value: "9", tone: "green" },
  { label: "Recursos generados", value: "31", tone: "gray" },
];

export const projects = [
  {
    id: "demo",
    title: "Tema 12. El currículo en Educación Primaria",
    area: "Educación Primaria",
    level: "Oposiciones docentes",
    status: "under_review" as StatusKey,
    updatedAt: "2026-05-28",
  },
  {
    id: "historia-contemporanea",
    title: "Tema 34. Transformaciones sociales del siglo XX",
    area: "Geografía e Historia",
    level: "Secundaria",
    status: "reports_generated" as StatusKey,
    updatedAt: "2026-05-26",
  },
  {
    id: "biologia-celular",
    title: "Tema 5. Organización celular",
    area: "Biología y Geología",
    level: "Secundaria",
    status: "processing" as StatusKey,
    updatedAt: "2026-05-25",
  },
];

export const sections = [
  {
    title: "1. Marco introductorio",
    summary: "Presenta el encuadre general del tema y sus conceptos principales.",
    concepts: ["currículo", "competencias", "evaluación"],
  },
  {
    title: "2. Desarrollo normativo",
    summary: "Relaciona la estructura del tema con la normativa indicada por el docente.",
    concepts: ["LOMLOE", "decreto autonómico", "criterios de evaluación"],
  },
  {
    title: "3. Aplicación didáctica",
    summary: "Recoge implicaciones para la programación y la práctica docente.",
    concepts: ["situaciones de aprendizaje", "metodología", "atención a la diversidad"],
  },
];

export const suggestions = [
  {
    id: "sug-1",
    section: "2. Desarrollo normativo",
    type: "legal_curricular",
    original:
      "La referencia curricular se basa en normativa previa y no menciona el marco competencial vigente.",
    proposed:
      "Actualizar el fragmento para vincular competencias específicas, criterios de evaluación y saberes básicos según la normativa aportada.",
    justification:
      "La actualización mejora la trazabilidad curricular sin sustituir la revisión docente.",
    source: "Normativa aportada por el profesor",
    confidence: "medium",
    status: "pending" as StatusKey,
  },
  {
    id: "sug-2",
    section: "3. Aplicación didáctica",
    type: "didactic_improvement",
    original: "La metodología se describe de forma genérica.",
    proposed:
      "Añadir una referencia localizada a situaciones de aprendizaje y evaluación formativa.",
    justification:
      "La propuesta mejora la contextualización didáctica sin reescribir el tema completo.",
    source: "Diagnóstico interno mock",
    confidence: "high",
    status: "approved" as StatusKey,
  },
];

export const resources = [
  {
    title: "Esquema desarrollado",
    type: "esquema_desarrollado",
    description: "Estructura ampliada para repaso y exposición oral.",
  },
  {
    title: "Test de autoevaluación",
    type: "test_autoevaluacion",
    description: "Preguntas con soluciones y explicación breve.",
  },
  {
    title: "Guion de presentación",
    type: "presentacion_clase",
    description: "Secuencia de diapositivas para clase o defensa.",
  },
];
