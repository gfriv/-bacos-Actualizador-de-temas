import type { StatusKey } from "@/components/ui/StatusBadge";
import { getAIConfigHeader, getAISessionHeader } from "@/lib/ai/config";
import {
  createDemoResource,
  demoConsolidated,
  demoDocuments,
  demoProjects,
  demoReports,
  demoResources,
  demoSections,
  getDemoSuggestions,
  LOCAL_DEMO_TOKEN,
  updateDemoSuggestion,
} from "@/lib/demo-data";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api";
export const TOKEN_KEY = "abacos_access_token";
export const DEMO_MODE_KEY = "abacos_demo_mode";

export type LegalFrameworkOption = {
  id: string;
  label: string;
  value: string;
  description: string;
};

export type Project = {
  id: number;
  owner_id: number;
  title: string;
  area: string;
  educational_level: string;
  legal_framework: string;
  bibliography_notes: string | null;
  instructions: string | null;
  status: StatusKey;
  created_at: string;
  updated_at: string;
};

export type DocumentRecord = {
  id: number;
  project_id: number;
  original_filename: string;
  file_type: string;
  extracted_text: string;
  version_index?: number;
  is_active?: boolean;
  extraction_metadata?: Record<string, unknown> | null;
  created_at: string;
};

export type DocumentSection = {
  id: number;
  project_id: number;
  document_id?: number | null;
  title: string;
  order_index: number;
  content: string;
  summary: string | null;
  detected_concepts: string[] | null;
};

export type Report = {
  id: number;
  project_id: number;
  report_type:
    | "initial_diagnosis"
    | "scientific_update"
    | "curriculum_mapping"
    | "source_validation"
    | "change_proposal"
    | "technical_traceability";
  title: string;
  content_markdown: string;
  analysis_run_id?: number | null;
  is_stale?: boolean;
  created_at: string;
};

export type Suggestion = {
  id: number;
  project_id: number;
  section_id: number | null;
  suggestion_type:
    | "scientific_update"
    | "legal_curricular"
    | "bibliographic_update"
    | "didactic_improvement";
  original_fragment: string;
  proposed_change: string;
  justification: string;
  source_reference: string | null;
  confidence_level: "low" | "medium" | "high" | string;
  status: StatusKey;
  teacher_notes: string | null;
  analysis_run_id?: number | null;
  anchor_status?: string | null;
  is_stale?: boolean;
  created_at: string;
  reviewed_at: string | null;
};

export type ConsolidatedDocument = {
  id: number;
  project_id: number;
  content_markdown: string;
  is_stale?: boolean;
  created_at: string;
};

export type GeneratedResource = {
  id: number;
  project_id: number;
  resource_type: string;
  title: string;
  content_markdown: string;
  is_stale?: boolean;
  created_at: string;
};

export type EvidenceSource = {
  id: number;
  project_id: number;
  analysis_run_id: number | null;
  title: string;
  url: string;
  snippet: string;
  source_kind: "official" | "scientific" | "web" | "unknown" | string;
  provider: string;
  validation_status: string;
  quality_score: number;
  rationale: string | null;
  retrieved_at: string;
};

export type ReportQualityIssue = {
  code: string;
  severity: "low" | "medium" | "high" | string;
  message: string;
};

export type ReportQuality = {
  ok: boolean;
  score: number;
  issues: ReportQualityIssue[];
  criteria: Record<string, number | boolean | string>;
};

export type ProjectCreatePayload = {
  title: string;
  area: string;
  educational_level: string;
  legal_framework?: string | null;
  bibliography_notes?: string;
  instructions?: string;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(TOKEN_KEY) ?? window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string, remember = false): void {
  clearToken();
  const storage = remember ? window.localStorage : window.sessionStorage;
  storage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(DEMO_MODE_KEY);
  window.localStorage.removeItem(DEMO_MODE_KEY);
}

function isOfflineDemoMode(): boolean {
  if (typeof window === "undefined") return false;
  const enabled =
    window.sessionStorage.getItem(DEMO_MODE_KEY) === "true" ||
    window.localStorage.getItem(DEMO_MODE_KEY) === "true";
  return enabled && getToken() === LOCAL_DEMO_TOKEN;
}

function setOfflineDemoMode(enabled: boolean, remember = false): void {
  window.sessionStorage.removeItem(DEMO_MODE_KEY);
  window.localStorage.removeItem(DEMO_MODE_KEY);
  const storage = remember ? window.localStorage : window.sessionStorage;
  storage.setItem(DEMO_MODE_KEY, enabled ? "true" : "false");
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const aiSessionHeader = getAISessionHeader();
  const aiConfigHeader = getAIConfigHeader();
  if (aiSessionHeader && shouldAttachAIConfig(path, init.method)) {
    headers.set("X-Abacos-AI-Session", aiSessionHeader);
  } else if (aiConfigHeader && shouldAttachAIConfig(path, init.method)) {
    headers.set("X-Abacos-AI-Config", aiConfigHeader);
  }
  if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let detail = `Error ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: unknown };
      detail = typeof data.detail === "string" ? data.detail : detail;
    } catch {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

function shouldAttachAIConfig(path: string, method: string | undefined): boolean {
  const httpMethod = (method ?? "GET").toUpperCase();
  return (
    httpMethod === "POST" &&
    (/^\/projects\/[^/]+\/analysis\//.test(path) || /^\/projects\/[^/]+\/resources$/.test(path))
  );
}

export async function registerAndLogin(email: string, password: string, fullName: string, remember = false) {
  try {
    await apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  } catch (error) {
    if (!(error instanceof Error) || !error.message.includes("registrado")) {
      throw error;
    }
  }
  const token = await apiFetch<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(token.access_token, remember);
  return token;
}

export async function loginDemo(remember = false) {
  try {
    const token = await apiFetch<{ access_token: string }>("/auth/demo", {
      method: "POST",
    });
    setOfflineDemoMode(false, remember);
    setToken(token.access_token, remember);
    return token;
  } catch {
    setToken(LOCAL_DEMO_TOKEN, remember);
    setOfflineDemoMode(true, remember);
    return { access_token: LOCAL_DEMO_TOKEN };
  }
}

export function listLegalFrameworks() {
  return apiFetch<LegalFrameworkOption[]>("/legal-frameworks");
}

export function listProjects() {
  if (isOfflineDemoMode()) return Promise.resolve(demoProjects);
  return apiFetch<Project[]>("/projects");
}

export function getProject(projectId: string | number) {
  if (isOfflineDemoMode()) {
    const project = demoProjects.find((item) => item.id === Number(projectId));
    return project
      ? Promise.resolve(project)
      : Promise.reject(new Error("Proyecto demo no encontrado"));
  }
  return apiFetch<Project>(`/projects/${projectId}`);
}

export function createProject(payload: ProjectCreatePayload) {
  if (isOfflineDemoMode()) {
    return Promise.resolve({
      id: Date.now(),
      owner_id: 1,
      title: payload.title,
      area: payload.area,
      educational_level: payload.educational_level,
      legal_framework:
        payload.legal_framework?.trim() ||
        "Marco normativo inferido automaticamente en modo demo; requiere verificacion docente.",
      bibliography_notes: payload.bibliography_notes ?? null,
      instructions: payload.instructions ?? null,
      status: "draft",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    } satisfies Project);
  }
  return apiFetch<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function uploadDocument(projectId: number, file: File) {
  if (isOfflineDemoMode()) {
    return Promise.resolve({
      id: Date.now(),
      project_id: projectId,
      original_filename: file.name,
      file_type: file.name.split(".").pop() ?? "docx",
      version_index: 1,
      is_active: true,
      extraction_metadata: { extractor: "demo", warnings: [] },
      extracted_text: "Documento demo cargado en modo preview sin backend público.",
      created_at: new Date().toISOString(),
    } satisfies DocumentRecord);
  }
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<DocumentRecord>(`/projects/${projectId}/documents`, {
    method: "POST",
    body: formData,
  });
}

export async function runResearchAnalysis(projectId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve({
      reports: demoReports.filter((report) => report.project_id === Number(projectId)),
      suggestions: getDemoSuggestions().filter(
        (suggestion) => suggestion.project_id === Number(projectId),
      ),
    });
  }
  try {
    return await apiFetch<{ reports: Report[]; suggestions: Suggestion[] }>(
      `/projects/${projectId}/analysis/research`,
      { method: "POST" },
    );
  } catch (error) {
    if (error instanceof Error && error.message.includes("404")) {
      return apiFetch<{ reports: Report[]; suggestions: Suggestion[] }>(
        `/projects/${projectId}/analysis/mock`,
        { method: "POST" },
      );
    }
    throw error;
  }
}

export const runMockAnalysis = runResearchAnalysis;

export function listDocuments(projectId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve(
      demoDocuments.filter((document) => document.project_id === Number(projectId)),
    );
  }
  return apiFetch<DocumentRecord[]>(`/projects/${projectId}/documents`);
}

export function listSections(projectId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve(
      demoSections.filter((section) => section.project_id === Number(projectId)),
    );
  }
  return apiFetch<DocumentSection[]>(`/projects/${projectId}/sections`);
}

export function listReports(projectId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve(demoReports.filter((report) => report.project_id === Number(projectId)));
  }
  return apiFetch<Report[]>(`/projects/${projectId}/reports`);
}

export function listEvidence(projectId: string | number) {
  if (isOfflineDemoMode()) return Promise.resolve([] satisfies EvidenceSource[]);
  return apiFetch<EvidenceSource[]>(`/projects/${projectId}/evidence`);
}

export function refreshOfficialEvidence(projectId: string | number) {
  if (isOfflineDemoMode()) return Promise.resolve([] satisfies EvidenceSource[]);
  return apiFetch<EvidenceSource[]>(`/projects/${projectId}/evidence/refresh-official`, {
    method: "POST",
  });
}

export function getReportQuality(reportId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve({
      ok: true,
      score: 82,
      issues: [],
      criteria: {
        evidence_count: 2,
        official_evidence_count: 1,
        has_human_verification: true,
      },
    } satisfies ReportQuality);
  }
  return apiFetch<ReportQuality>(`/reports/${reportId}/quality`);
}

export function listSuggestions(projectId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve(
      getDemoSuggestions().filter((suggestion) => suggestion.project_id === Number(projectId)),
    );
  }
  return apiFetch<Suggestion[]>(`/projects/${projectId}/suggestions`);
}

export function reviewSuggestion(
  suggestionId: number,
  payload: {
    status: "approved" | "rejected" | "edited" | "pending";
    teacher_notes?: string;
    proposed_change?: string;
  },
) {
  if (isOfflineDemoMode()) return Promise.resolve(updateDemoSuggestion(suggestionId, payload));
  return apiFetch<Suggestion>(`/suggestions/${suggestionId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function consolidateProject(projectId: string | number) {
  if (isOfflineDemoMode()) {
    const approved = getDemoSuggestions().filter(
      (suggestion) =>
        suggestion.project_id === Number(projectId) &&
        (suggestion.status === "approved" || suggestion.status === "edited"),
    );
    if (approved.length === 0)
      return Promise.reject(new Error("No hay sugerencias aprobadas o editadas para consolidar."));
    return Promise.resolve({ ...demoConsolidated, project_id: Number(projectId) });
  }
  return apiFetch<ConsolidatedDocument>(`/projects/${projectId}/consolidate`, {
    method: "POST",
  });
}

export function approveAllAndConsolidateProject(projectId: string | number) {
  if (isOfflineDemoMode()) {
    const suggestions = getDemoSuggestions().filter(
      (suggestion) => suggestion.project_id === Number(projectId),
    );
    for (const suggestion of suggestions) {
      if (suggestion.status === "pending") {
        updateDemoSuggestion(suggestion.id, {
          status: "approved",
          teacher_notes: "Validada en bloque por el docente antes de consolidar.",
        });
      }
    }
    return consolidateProject(projectId);
  }
  return apiFetch<ConsolidatedDocument>(`/projects/${projectId}/consolidate/approve-all`, {
    method: "POST",
  });
}

export function getConsolidated(projectId: string | number) {
  if (isOfflineDemoMode())
    return Promise.resolve({ ...demoConsolidated, project_id: Number(projectId) });
  return apiFetch<ConsolidatedDocument>(`/projects/${projectId}/consolidated`);
}

export function generateResource(projectId: string | number, resourceType: string) {
  if (isOfflineDemoMode()) return Promise.resolve(createDemoResource(projectId, resourceType));
  return apiFetch<GeneratedResource>(`/projects/${projectId}/resources`, {
    method: "POST",
    body: JSON.stringify({ resource_type: resourceType }),
  });
}

export function listResources(projectId: string | number) {
  if (isOfflineDemoMode()) {
    return Promise.resolve(
      demoResources.filter((resource) => resource.project_id === Number(projectId)),
    );
  }
  return apiFetch<GeneratedResource[]>(`/projects/${projectId}/resources`);
}
