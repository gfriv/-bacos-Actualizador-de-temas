# Roadmap

## Phase 1

- Monorepo base.
- Visual identity and routes.
- FastAPI models, auth and migrations.
- Document extraction adapters.
- MockProvider.
- Tests mínimos.

## Phase 2

- Real async processing through RQ.
- Replace the synchronous research-analysis endpoint with queued workers.
- Improve scientific and curriculum report generation templates.
- Deploy frontend preview to Vercel with `NEXT_PUBLIC_API_URL` pointing to a reachable backend.
- Choose managed backend target for FastAPI, workers, PostgreSQL, Redis and document storage.

## Phase 3

- Rich Markdown preview/editor for approved suggestions.
- Reviewer assignment model.
- Backend deployment target with managed PostgreSQL, Redis, persistent document storage and worker monitoring.

## Phase 4

- OpenAI-compatible production pilot.
- Local/private model pilot with Ollama, vLLM or equivalent if documents cannot leave the client environment.
- Security hardening.
- RGPD review.
- OCR pipeline for scanned PDFs.
