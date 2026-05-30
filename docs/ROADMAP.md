# Roadmap

## Phase 1

- Monorepo base.
- Visual identity and routes.
- FastAPI models, auth and migrations.
- Document extraction adapters.
- MockProvider.
- Tests mínimos.

## Phase 2

- Expand queued RQ processing beyond research/consolidation/resources with monitoring and retries.
- Improve scientific and curriculum report generation templates.
- Deploy frontend preview to Vercel with `NEXT_PUBLIC_API_URL` pointing to a reachable backend.
- Validate managed backend target for FastAPI, workers, PostgreSQL, Redis and document storage.

## Phase 3

- Rich Markdown preview/editor for approved suggestions.
- Reviewer assignment model.
- Worker monitoring, retry policy and shared object storage for generated artifacts.

## Phase 4

- OpenAI-compatible production pilot.
- Local/private model pilot with Ollama, vLLM or equivalent if documents cannot leave the client environment.
- Formal RGPD sign-off and retention/backups policy.
- OCR pipeline for scanned PDFs.
