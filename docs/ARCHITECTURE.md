# Architecture

## Overview

Ábacos is a document-first educational AI application. It is not a generic chatbot or a full e-learning platform.

The system receives a teacher-authored DOCX/PDF, extracts text, splits sections, generates scientific and curriculum reports, creates reviewable suggestions, consolidates approved changes only, and derives teaching resources.

## Monorepo

- `apps/web`: Next.js App Router UI.
- `apps/api`: FastAPI backend with SQLAlchemy and Alembic.
- `workers`: RQ worker entrypoints.
- `packages/shared`: shared status contracts.
- `infra`: Docker and service configuration.
- `docs`: project decisions and operating docs.

## Data Flow

1. Teacher creates a project.
2. Teacher uploads DOCX/PDF.
3. API stores the file and extracts text.
4. Section splitter creates `DocumentSection` rows.
5. Workers generate structured reports and suggestions through `ModelRouter`.
6. Teacher reviews every suggestion.
7. Consolidation uses only `approved` and `edited` suggestions.
8. Resource generation starts from the consolidated document.
9. Downloads are served through authenticated API endpoints; internal file paths are never returned to the frontend.

## Key Boundary

The AI layer never owns final truth. It proposes structured suggestions. The teacher must validate before consolidation.

## Document Processing

The upload pipeline validates the actual container before extraction: DOCX must be a valid Word ZIP package and PDF must start as a PDF document. DOCX extraction preserves paragraph order, styled headings, body tables, headers and footers. PDF extraction uses `pdfplumber` first for layout-aware text and table recovery, then falls back to `pypdf`. OCR support is prepared but disabled by default with `OCR_ENABLED=false`; no OCR engine is installed automatically.

If OCR is explicitly enabled in a later phase, it is bounded by `OCR_MAX_PAGES`, `OCR_DPI` and `OCR_TIMEOUT_SECONDS` to avoid unbounded processing. The default language set is `spa+eng`; deployments must install Tesseract and the optional OCR adapter dependencies deliberately, or set `OCR_TESSERACT_CMD` to the executable path. If OCR is unavailable, the API returns a clear `422` instead of silently producing an empty analysis.

The section splitter understands Markdown headings, numbered/nested headings, topic-style headings and uppercase academic headings while avoiding table rows and page markers. Very long sections are chunked into ordered parts so downstream analysis remains manageable.

## AI Provider Boundary

The provider choice is centralized in `ModelRouter`, not scattered across UI components. The frontend exposes a session-level selector for API providers or Ollama local, but all document processing calls still go through the backend.

Flow:

1. UI validates the selected provider/model/key through authenticated backend endpoints.
2. FastAPI creates an in-memory `X-Abacos-AI-Session` token with TTL.
3. The browser stores provider/model/session id, never the full API key.
4. Pipeline calls attach `X-Abacos-AI-Session`; legacy `X-Abacos-AI-Config` remains as local fallback.
5. `ModelRouter` instantiates Mock, OpenAI-compatible, Gemini, Anthropic or Ollama provider.
6. Suggestions remain pending until teacher review.

Direct text-generation endpoints are authenticated. Provider validation/model listing require a backend session to avoid exposing the API as a public proxy. No generated educational content is persisted without a user/project context.

## Deployment Boundary

The frontend can run on Vercel. The backend needs a real service capable of running FastAPI, PostgreSQL, Redis, persistent document storage and an RQ worker. The Docker API image runs Alembic migrations on startup, and the worker command is `python /app/workers/worker.py`.

The synchronous endpoints remain available for demos. A persistent backend can use queued endpoints:

- `POST /api/projects/{project_id}/analysis/research/queue`
- `POST /api/projects/{project_id}/consolidate/queue`
- `POST /api/projects/{project_id}/resources/queue`
- `GET /api/analysis-runs/{analysis_run_id}`

Queued jobs do not accept BYOK headers because API keys must not be serialized into Redis.

## Research Layer

`apps/api/app/research` provides web search before report generation. The analysis service builds targeted queries from:

- project area;
- educational level;
- legal framework supplied by the teacher;
- detected section concepts.

The research layer has four explicit service steps before any LLM synthesis:

1. `ClaimExtractor` detects legal, curricular, scientific, bibliographic and didactic claims inside each section.
2. `NormativeEngine` builds the expected hierarchy of state law, state curriculum, regional curriculum, evaluation rules and opposition call when applicable.
3. `ResearchPlanner` converts claims and normative context into layered queries: official state, regional official, academic and bibliographic.
4. `SourceRanker` scores each evidence item by authority, recency, legal relevance, section/claim relevance and citation quality.

The LLM receives curated context from those services. It does not browse freely, choose sources opaquely or apply changes directly.

For curricular analysis, it prioritizes official domains such as BOE, DOE/Junta de Extremadura, Educarex, Educagob, Ministerio de Educación and EU legal sources. The same flow supports preparation for Spanish teaching exams, including Infantil, Primaria, Secundaria and FP, by adding official BOE references for the relevant stage and the state teaching-entry regulation when applicable. When the project mentions Extremadura, the curated evidence layer also adds Ley 4/2011 de Educación de Extremadura, consolidated Extremadura LOMLOE curriculum decrees by stage, evaluation rules and FP references where applicable. Search results are not applied automatically; they become traceable `EvidenceSource` rows, optional `SuggestionEvidence` links, report references and `Suggestion.source_reference`.

Providers are selected with `WEB_SEARCH_PROVIDER`: `disabled`, `duckduckgo`, `tavily` or `brave`. External search requires `EXTERNAL_WEB_SEARCH_ENABLED=true`; the default is disabled.

## Structured Reports And Quality Gate

The research pipeline now produces six report types:

- `initial_diagnosis`
- `scientific_update`
- `curriculum_mapping`
- `source_validation`
- `change_proposal`
- `technical_traceability`

Every exportable report, consolidated document and generated resource includes an AI assistance notice, generation metadata and the Ábacos corporate footer. `ReportQualityGate` blocks exports that contain likely API keys, internal storage paths, unresolved placeholders or missing required traceability. Academic quality is also exposed through `/api/reports/{report_id}/quality` with score, criteria and issues.

The research service also computes an `academic_score` with an automatic rubric. It flags missing bibliography, incomplete opposition framework, absent official curriculum evidence, outdated legal references, short sections and scientific/currentness claims without supporting evidence. The score is a triage signal for the teacher; it never authorizes automatic consolidation.

## Document Versions And Stale Outputs

Each uploaded document receives a `version_index` and an `is_active` flag. Uploading a new version marks previous reports, suggestions, consolidated documents and resources as stale. List endpoints hide stale outputs so the teacher cannot consolidate recommendations generated from an old document. The old data remains in the database for audit and traceability.

Consolidation uses only non-stale suggestions in `approved` or `edited` state. If the stored `original_fragment` no longer matches the active section context, the suggestion is marked with `anchor_status=failed` and is not inserted into the final document.

Successful integrations use a whitespace-tolerant anchor match and append internal change notes with before/after snippets so the generated DOCX remains traceable.

## Resource Generation

Resources are generated only from the consolidated document. `DocumentBlueprint` parses the Markdown structure, extracts the title, section map and key terms, then creates resource-specific prompt context. This prevents the provider from treating a test, a class presentation and an audio script as the same generic task. MockProvider mirrors the same contract for local demos and tests.
