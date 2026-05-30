# RGPD Pilot Gate

This file defines the operational gate before processing real client documents with external AI or external search providers.

## Default State

The safe default is local/mock processing:

```env
LLM_PROVIDER=mock
EXTERNAL_AI_PROVIDERS_ENABLED=false
EXTERNAL_AI_DATA_PROCESSING_CONFIRMED=false
WEB_SEARCH_PROVIDER=disabled
EXTERNAL_WEB_SEARCH_ENABLED=false
```

With this configuration, the backend blocks OpenAI, Gemini, Anthropic and public OpenAI-compatible endpoints. It also disables external web search.

## Required Before Enabling External AI

- Client has been informed that documents or derived prompts may be processed by an external provider.
- Legal basis and purpose limitation are documented.
- Data processing agreement is reviewed and accepted.
- Provider region, retention, logging and training-use policy are reviewed.
- Internal retention and deletion process for uploaded/generated documents is defined.
- Production secrets are stored only in backend environment variables or a secret manager.
- Logs and error monitoring are configured to avoid document text, API keys and Authorization headers.

Only after those checks:

```env
EXTERNAL_AI_PROVIDERS_ENABLED=true
EXTERNAL_AI_DATA_PROCESSING_CONFIRMED=true
```

## Required Before Enabling External Search

- Queries sent to search providers are reviewed for possible confidential information.
- Redaction rules are defined if project titles or legal notes can include client-private data.
- Contractual API providers are preferred over scraping/no-key providers for production.

Only after those checks:

```env
EXTERNAL_WEB_SEARCH_ENABLED=true
```

## Local Models

Ollama/local OpenAI-compatible endpoints avoid sending documents to external providers, but they still require operational controls:

- backend must run in the same machine or trusted network as the model server;
- Vercel/serverless cannot reach the user's local Ollama;
- model downloads through `/api/ai/ollama/pull` stay disabled unless `OLLAMA_PULL_ENABLED=true` and the user confirms explicitly.
