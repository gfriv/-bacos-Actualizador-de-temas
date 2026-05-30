import type {
  ConsolidatedDocument,
  DocumentRecord,
  DocumentSection,
  GeneratedResource,
  Project,
  Report,
  Suggestion,
} from "@/lib/api";

export const LOCAL_DEMO_TOKEN = "abacos-local-demo-token";

const now = new Date();
const isoDaysAgo = (days: number) => new Date(now.getTime() - days * 24 * 60 * 60 * 1000).toISOString();

export const demoProjects: Project[] = [
  {
    id: 101,
    owner_id: 1,
    title: "La célula y la organización celular",
    area: "Biología y Geología",
    educational_level: "4.º ESO",
    legal_framework: "LOMLOE. Decreto autonómico aportado por el centro.",
    bibliography_notes: "Manual de referencia del departamento y artículos de revisión indicados por el docente.",
    instructions: "Mantener el estilo académico y señalar ampliaciones como verificables.",
    status: "under_review",
    created_at: isoDaysAgo(8),
    updated_at: isoDaysAgo(1),
  },
  {
    id: 102,
    owner_id: 1,
    title: "Ecosistemas, energía y sostenibilidad",
    area: "Biología y Geología",
    educational_level: "1.º Bachillerato",
    legal_framework: "Normativa estatal y concreción curricular autonómica.",
    bibliography_notes: "Bibliografía base del tema original.",
    instructions: "Generar recursos claros para repaso autónomo.",
    status: "resources_generated",
    created_at: isoDaysAgo(14),
    updated_at: isoDaysAgo(0),
  },
  {
    id: 103,
    owner_id: 1,
    title: "La literatura del Siglo de Oro",
    area: "Lengua Castellana y Literatura",
    educational_level: "2.º Bachillerato",
    legal_framework: "Currículo LOMLOE de Bachillerato.",
    bibliography_notes: null,
    instructions: "Revisar conexión con competencias específicas.",
    status: "draft",
    created_at: isoDaysAgo(2),
    updated_at: isoDaysAgo(2),
  },
  {
    id: 104,
    owner_id: 1,
    title: "Tema 3. Desarrollo evolutivo de 0 a 6 años",
    area: "Educación Infantil",
    educational_level: "Oposiciones Educación Infantil",
    legal_framework:
      "LOMLOE, Real Decreto 95/2022, convocatoria de oposiciones y normativa autonómica aportada por el docente.",
    bibliography_notes: "Temario base de preparación de oposiciones y materiales de academia revisados.",
    instructions: "Orientar las sugerencias a defensa ante tribunal y programación didáctica.",
    status: "reports_generated",
    created_at: isoDaysAgo(4),
    updated_at: isoDaysAgo(0),
  },
];

export const demoDocuments: DocumentRecord[] = [
  {
    id: 201,
    project_id: 101,
    original_filename: "tema-celula-organizacion.docx",
    file_type: "docx",
    extracted_text:
      "1. Teoría celular\nLa célula es la unidad estructural y funcional de los seres vivos.\n\n2. Orgánulos\nEl tema describe núcleo, mitocondrias, ribosomas y retículo endoplasmático.",
    created_at: isoDaysAgo(7),
  },
  {
    id: 202,
    project_id: 102,
    original_filename: "ecosistemas-energia-sostenibilidad.pdf",
    file_type: "pdf",
    extracted_text:
      "1. Flujo de energía\nLos ecosistemas se analizan mediante niveles tróficos.\n\n2. Sostenibilidad\nSe revisan impactos humanos y estrategias de conservación.",
    created_at: isoDaysAgo(13),
  },
  {
    id: 203,
    project_id: 104,
    original_filename: "tema-desarrollo-evolutivo-infantil.docx",
    file_type: "docx",
    extracted_text:
      "1. Desarrollo evolutivo\nEl tema aborda dimensiones motriz, cognitiva, afectiva y social de 0 a 6 años.\n\n2. Implicaciones educativas\nSe plantean orientaciones metodológicas para el aula de Educación Infantil.",
    created_at: isoDaysAgo(3),
  },
];

export const demoSections: DocumentSection[] = [
  {
    id: 301,
    project_id: 101,
    title: "Teoría celular",
    order_index: 1,
    content: "La célula es la unidad estructural y funcional de los seres vivos.",
    summary: "Base conceptual del tema.",
    detected_concepts: ["teoría celular", "unidad funcional", "estructura celular"],
  },
  {
    id: 302,
    project_id: 101,
    title: "Orgánulos celulares",
    order_index: 2,
    content: "Descripción de núcleo, mitocondrias, ribosomas y retículo endoplasmático.",
    summary: "Apartado descriptivo con posible actualización terminológica.",
    detected_concepts: ["orgánulos", "mitocondria", "ribosoma"],
  },
  {
    id: 303,
    project_id: 102,
    title: "Flujo de energía",
    order_index: 1,
    content: "Los ecosistemas se analizan mediante niveles tróficos.",
    summary: "Apartado consolidado.",
    detected_concepts: ["ecosistema", "niveles tróficos", "energía"],
  },
  {
    id: 304,
    project_id: 104,
    title: "Desarrollo evolutivo de 0 a 6 años",
    order_index: 1,
    content: "El tema aborda dimensiones motriz, cognitiva, afectiva y social de 0 a 6 años.",
    summary: "Apartado base para actualización curricular y enfoque de oposición.",
    detected_concepts: ["educación infantil", "desarrollo evolutivo", "oposiciones docentes"],
  },
];

export const demoReports: Report[] = [
  {
    id: 401,
    project_id: 101,
    report_type: "scientific_update",
    title: "Informe de actualización científica",
    content_markdown:
      "## Diagnóstico\n\nEl tema es sólido, pero conviene actualizar terminología sobre biología celular y diferenciar claramente conceptos consolidados de ampliaciones recientes.\n\n## Recomendaciones\n\n- Revisar referencias a orgánulos y funciones celulares.\n- Señalar como ampliación verificable cualquier avance no presente en la bibliografía base.",
    created_at: isoDaysAgo(1),
  },
  {
    id: 402,
    project_id: 101,
    report_type: "curriculum_mapping",
    title: "Informe legislativo y curricular",
    content_markdown:
      "## Contextualización curricular\n\nLa conexión curricular debe apoyarse en la normativa aportada por el docente. Se proponen vínculos con competencias científicas solo cuando la formulación del tema lo permite.",
    created_at: isoDaysAgo(1),
  },
  {
    id: 403,
    project_id: 104,
    report_type: "curriculum_mapping",
    title: "Informe legislativo y curricular para oposición",
    content_markdown:
      "## Contextualización curricular\n\nEl tema se puede contrastar con el Real Decreto 95/2022, la convocatoria de oposiciones y la normativa autonómica aportada. Las conexiones con áreas, competencias y criterios quedan pendientes de validación docente.",
    created_at: isoDaysAgo(0),
  },
];

const baseSuggestions: Suggestion[] = [
  {
    id: 501,
    project_id: 101,
    section_id: 302,
    suggestion_type: "scientific_update",
    original_fragment: "Las mitocondrias son los orgánulos encargados de producir toda la energía celular.",
    proposed_change:
      "Matizar que las mitocondrias participan de forma central en la respiración celular y la síntesis de ATP, sin reducir toda la energética celular a un único orgánulo.",
    justification: "Evita una simplificación excesiva y mejora la precisión conceptual.",
    source_reference: "Requiere contraste con la bibliografía indicada por el departamento.",
    confidence_level: "medium",
    status: "pending",
    teacher_notes: null,
    created_at: isoDaysAgo(1),
    reviewed_at: null,
  },
  {
    id: 502,
    project_id: 101,
    section_id: 301,
    suggestion_type: "legal_curricular",
    original_fragment: "El tema se trabajará mediante actividades de identificación.",
    proposed_change:
      "Relacionar la actividad con interpretación de modelos celulares y uso de vocabulario científico preciso, si la normativa aportada lo respalda.",
    justification: "Mejora la trazabilidad curricular sin inventar criterios ni artículos normativos.",
    source_reference: "Normativa indicada por el usuario.",
    confidence_level: "high",
    status: "approved",
    teacher_notes: "Correcto para la programación del centro.",
    created_at: isoDaysAgo(1),
    reviewed_at: isoDaysAgo(0),
  },
  {
    id: 503,
    project_id: 102,
    section_id: 303,
    suggestion_type: "didactic_improvement",
    original_fragment: "El alumnado realizará un resumen.",
    proposed_change: "Añadir una tabla de niveles tróficos con ejemplos y una pregunta de transferencia.",
    justification: "La mejora didáctica ya está integrada en el documento consolidado de demo.",
    source_reference: "Propuesta didáctica generada desde el tema consolidado.",
    confidence_level: "high",
    status: "edited",
    teacher_notes: "Adaptar ejemplos al entorno local del alumnado.",
    created_at: isoDaysAgo(4),
    reviewed_at: isoDaysAgo(2),
  },
  {
    id: 504,
    project_id: 104,
    section_id: 304,
    suggestion_type: "legal_curricular",
    original_fragment: "Se plantean orientaciones metodológicas para el aula de Educación Infantil.",
    proposed_change:
      "Vincular las orientaciones metodológicas con el enfoque globalizador, el juego, la autonomía progresiva y la normativa de Educación Infantil aportada para la convocatoria.",
    justification:
      "Mejora la defensa del tema ante tribunal porque conecta el contenido psicopedagógico con el marco curricular sin inventar artículos.",
    source_reference: "Real Decreto 95/2022 y normativa autonómica aportada por el docente.",
    confidence_level: "medium",
    status: "pending",
    teacher_notes: null,
    created_at: isoDaysAgo(0),
    reviewed_at: null,
  },
];

export function getDemoSuggestions(): Suggestion[] {
  if (typeof window === "undefined") return baseSuggestions;
  const stored = window.localStorage.getItem("abacos_demo_suggestions");
  if (!stored) return baseSuggestions;
  try {
    return JSON.parse(stored) as Suggestion[];
  } catch {
    return baseSuggestions;
  }
}

export function updateDemoSuggestion(
  suggestionId: number,
  payload: { status: "approved" | "rejected" | "edited" | "pending"; teacher_notes?: string; proposed_change?: string },
): Suggestion {
  const suggestions = getDemoSuggestions();
  const updated = suggestions.map((suggestion) =>
    suggestion.id === suggestionId
      ? {
          ...suggestion,
          ...payload,
          reviewed_at: payload.status === "pending" ? null : new Date().toISOString(),
        }
      : suggestion,
  );
  window.localStorage.setItem("abacos_demo_suggestions", JSON.stringify(updated));
  return updated.find((suggestion) => suggestion.id === suggestionId) ?? suggestions[0];
}

export const demoConsolidated: ConsolidatedDocument = {
  id: 601,
  project_id: 102,
  content_markdown:
    "# Ecosistemas, energía y sostenibilidad\n\n## Flujo de energía\n\nLos ecosistemas se analizan mediante niveles tróficos y transferencia de materia y energía.\n\n## Actividad consolidada\n\nTabla de niveles tróficos con ejemplos y pregunta de transferencia contextualizada.",
  created_at: isoDaysAgo(2),
};

export const demoResources: GeneratedResource[] = [
  {
    id: 701,
    project_id: 102,
    resource_type: "esquema_desarrollado",
    title: "Esquema desarrollado",
    content_markdown:
      "## 1. Ecosistema\n\n- Componentes bióticos y abióticos.\n- Relaciones tróficas.\n\n## 2. Energía\n\n- Productores, consumidores y descomponedores.\n- Transferencia energética y pérdida de energía.",
    created_at: isoDaysAgo(1),
  },
  {
    id: 702,
    project_id: 102,
    resource_type: "guion_audio",
    title: "Guion de audio",
    content_markdown:
      "## Introducción\n\nEn este audio se repasará cómo fluye la energía en un ecosistema y por qué la sostenibilidad exige interpretar relaciones entre niveles tróficos.",
    created_at: isoDaysAgo(0),
  },
];

export function createDemoResource(projectId: string | number, resourceType: string): GeneratedResource {
  return {
    id: Date.now(),
    project_id: Number(projectId),
    resource_type: resourceType,
    title: resourceType.replaceAll("_", " "),
    content_markdown: `# ${resourceType.replaceAll("_", " ")}\n\nRecurso demo generado desde el documento consolidado. En entorno local con API activa, esta operación usa el ModelRouter configurado.`,
    created_at: new Date().toISOString(),
  };
}
