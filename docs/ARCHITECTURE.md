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

## AI Provider Boundary

The provider choice is centralized in `ModelRouter`, not scattered across UI components. The frontend exposes a session-level selector for API providers or Ollama local, but all document processing calls still go through the backend.

Flow:

1. UI stores the selected provider/model/key in browser `sessionStorage`.
2. Pipeline calls attach `X-Abacos-AI-Config`.
3. FastAPI validates the header as `AIProviderConfig`.
4. `ModelRouter` instantiates Mock, OpenAI-compatible, Gemini, Anthropic or Ollama provider.
5. Suggestions remain pending until teacher review.

Direct text-generation endpoints are authenticated. Provider validation/model listing can be used from the setup screen before login, but no generated educational content is persisted without a user/project context.

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

For curricular analysis, it prioritizes official domains such as BOE, DOE/Junta de Extremadura, Educarex, Educagob, Ministerio de Educación and EU legal sources. The same flow supports preparation for Spanish teaching exams, including Infantil, Primaria, Secundaria and FP, by adding official BOE references for the relevant stage and the state teaching-entry regulation when applicable. When the project mentions Extremadura, the curated evidence layer also adds Ley 4/2011 de Educación de Extremadura, consolidated Extremadura LOMLOE curriculum decrees by stage, evaluation rules and FP references where applicable. Search results are not applied automatically; they become traceable evidence in reports and `Suggestion.source_reference`.

Providers are selected with `WEB_SEARCH_PROVIDER`: `disabled`, `duckduckgo`, `tavily` or `brave`. External search requires `EXTERNAL_WEB_SEARCH_ENABLED=true`; the default is disabled.

## Structured Reports And Quality Gate

The research pipeline now produces six report types:

- `initial_diagnosis`
- `scientific_update`
- `curriculum_mapping`
- `source_validation`
- `change_proposal`
- `technical_traceability`

Every exportable report, consolidated document and generated resource includes an AI assistance notice, generation metadata and the Ábacos corporate footer. `ReportQualityGate` blocks exports that contain likely API keys, internal storage paths, unresolved placeholders or missing required traceability.
