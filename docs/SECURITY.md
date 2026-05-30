# Security

## Implemented Baseline

- Password hashing with `pwdlib`.
- JWT-based local authentication.
- CORS restricted to local frontend origins by default.
- File extension validation for DOCX/PDF.
- Upload size limit through `MAX_UPLOAD_MB`.
- Safe generated filenames to avoid path traversal.
- AuditLog model for key actions.
- LLM keys read only from backend environment variables.
- Search API keys read only from backend environment variables.
- External LLM providers are blocked by default through `EXTERNAL_AI_PROVIDERS_ENABLED=false` and `EXTERNAL_AI_DATA_PROCESSING_CONFIRMED=false`.
- External web search is blocked by default through `EXTERNAL_WEB_SEARCH_ENABLED=false`.
- Optional user-supplied AI keys are kept in browser `sessionStorage` and sent only as an ephemeral `X-Abacos-AI-Config` header for pipeline calls.
- Queued worker endpoints reject `X-Abacos-AI-Config` so API keys cannot be serialized into Redis jobs.
- AI provider validation, model listing, generation and Ollama pull endpoints require authenticated backend sessions. The public catalog only returns provider metadata.
- Remote/serverless runtimes block Ollama and private/local LLM endpoints to avoid SSRF and false attempts to reach the user's local machine from Vercel.
- Optional demo access seeded by backend only, controlled through `DEMO_ACCESS_ENABLED`.
- Public registration always creates `teacher`; `admin` is created only by server-side script.
- Public response schemas do not expose internal storage paths.
- Authenticated download endpoints validate project access and path containment before serving files.
- Report, consolidated-document and resource downloads pass through `ReportQualityGate` before export.
- Legacy exports missing only formal metadata are repaired with an explicit compatibility note; exports containing secrets, internal paths or placeholders remain blocked.
- `ReportQualityGate` blocks likely API keys, bearer tokens, internal storage paths, unresolved placeholders and missing required traceability.
- Invalid or damaged DOCX/PDF uploads return `422` without leaking filesystem paths.
- PDF OCR is prepared but disabled by default. If explicitly enabled, it runs locally in the backend process, is bounded by `OCR_MAX_PAGES`, `OCR_DPI` and `OCR_TIMEOUT_SECONDS`, and returns OCR errors without filesystem paths.
- Generic AI generation endpoints require authentication so the API cannot be abused as a public LLM proxy.
- Provider error responses are sanitized so API keys are not reflected in HTTP responses, UI toasts or logs.

## AI Credentials

The application must never ask for personal usernames or passwords for ChatGPT, Gemini, Claude or similar services.

Allowed configuration:
- backend API keys in environment variables;
- user BYOK API keys for the current browser session only;
- local OpenAI-compatible endpoints;
- Ollama local through the backend process;
- search-provider API keys in backend variables such as `TAVILY_API_KEY` or `BRAVE_SEARCH_API_KEY`;
- future BYOK with encryption, not implemented in this MVP base.

Current BYOK limitations:

- session keys are not encrypted at rest because they are not persisted server-side;
- the browser can still expose sessionStorage to malicious scripts, so keep CSP and dependency hygiene strict before production;
- do not log request headers in reverse proxies;
- do not enable `/api/ai/ollama/pull` in public deployments without additional rate limits and operator controls.

## Demo Access

The demo endpoint is intended for local development and guided product presentations. It creates non-sensitive sample projects for a demo teacher account.

Before any production deployment:

- disable demo access unless the business explicitly wants a public sandbox;
- never seed real client documents through demo data;
- ensure demo projects cannot expose uploaded private files;
- log demo logins separately from normal teacher logins.

## Documents and External Providers

Documents must not be sent to external providers except through the configured `ModelRouter`. Production cannot use external LLM providers unless both flags are enabled:

```env
EXTERNAL_AI_PROVIDERS_ENABLED=true
EXTERNAL_AI_DATA_PROCESSING_CONFIRMED=true
```

Those flags are an operational gate, not a legal substitute. Before enabling them, Ábacos must inform the client and review GDPR/RGPD obligations, data processing agreements, retention policy and provider region/model settings.

Search providers may receive query strings derived from project area, level, legal framework and detected concepts. External search stays disabled unless:

```env
EXTERNAL_WEB_SEARCH_ENABLED=true
```

Before enabling it in production, review whether those queries can contain confidential client information and configure redaction or a contractual provider if needed.

## Export Quality Gate

The backend checks generated Markdown before allowing report/resource downloads or DOCX consolidation. This is not a substitute for teacher review; it prevents obvious technical leaks:

- no API-key-like strings;
- no `file_path`, `docx_path`, `db://` or local filesystem paths;
- no unresolved placeholders such as `undefined`;
- required AI assistance notice;
- required Ábacos corporate footer;
- required sources for scientific, curriculum and validation reports.

## Production Hardening Pending

- HTTPS-only deployment.
- Strong JWT secret rotation.
- Encrypted object storage.
- Malware scanning for uploads.
- Stronger OCR isolation for production, for example a sandboxed worker/container with CPU and memory limits.
- Full role-based assignment model for reviewers.
- Structured log redaction policy.
- Backup and retention policy.
- Formal RGPD/legal sign-off before processing real client documents with external providers.
