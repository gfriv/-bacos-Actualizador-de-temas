# Model Router

El `ModelRouter` centraliza cualquier llamada a IA. Ningún documento debe enviarse a un proveedor externo fuera de este módulo.

## Interfaz

- `generate_text(prompt, system_prompt, model_config)`
- `generate_json(prompt, system_prompt, schema, model_config)`
- `summarize(text, instructions)`
- `extract_structured_data(text, schema)`
- `generate_document_resource(document, resource_type)`

El frontend mantiene un contrato TypeScript equivalente en `packages/shared/src/ai.ts`:

```ts
interface AIProvider {
  id: string;
  displayName: string;
  mode: "api" | "local";
  validateConnection(): Promise<ProviderValidationResult>;
  listModels(): Promise<ModelInfo[]>;
  generateText(input: GenerateTextInput): Promise<GenerateTextResult>;
  generateStructured<T>(input: GenerateStructuredInput<T>): Promise<T>;
  streamText?(input: GenerateTextInput): AsyncIterable<string>;
}
```

## Proveedor Por Defecto

`LLM_PROVIDER=mock` es el valor por defecto. No llama a modelos reales y sirve para desarrollo, tests y demos rápidas sin coste.

## Selección Por Sesión Desde La UI

La app permite elegir proveedor al inicio de cada sesión. El usuario puede usar:

- OpenAI, Gemini, Claude/Anthropic o un endpoint OpenAI-compatible con su propia API key.
- Ollama local, detectando modelos instalados mediante `/api/tags`.
- MockProvider para demo o desarrollo.

La configuración del usuario no se guarda en base de datos. El frontend la conserva en `sessionStorage` y la envía como `X-Abacos-AI-Config` solo a operaciones del pipeline. El backend valida esa cabecera con `AIProviderConfig` y construye un `ModelRouter(provider_config=...)`.

Los endpoints de catálogo y validación son:

```text
GET  /api/ai/providers
POST /api/ai/providers/validate
POST /api/ai/providers/models
```

Los endpoints de generación directa requieren autenticación para evitar un proxy público de LLM.

## Proveedor Compatible Con OpenAI

Variables:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

El proveedor llama a `${LLM_BASE_URL}/chat/completions`.

Ejemplos:

- OpenAI API: `https://api.openai.com/v1`
- vLLM local: `http://127.0.0.1:8001/v1`
- Ollama: `http://127.0.0.1:11434/v1`
- LM Studio: endpoint local compatible con OpenAI

## Ollama Local

Instalación mínima:

```bash
ollama serve
ollama pull qwen2.5:7b-instruct
```

Configuración recomendada para desarrollo:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_PULL_ENABLED=false
```

Modelos recomendados para análisis documental en equipos razonables: Qwen, Gemma y Llama Instruct. La descarga automática desde la app solo se permite si `OLLAMA_PULL_ENABLED=true` y el usuario confirma explícitamente el modelo, porque puede ocupar varios GB.

Ollama evita enviar documentos a terceros, aunque la calidad depende mucho del modelo local elegido. En Vercel, `localhost` pertenece al backend desplegado, no al ordenador del usuario.

## Seguridad

- No hardcodear claves.
- No exponer `LLM_API_KEY` al frontend.
- No registrar claves completas en logs.
- No pedir usuario/contraseña de ChatGPT, Gemini, Claude ni servicios externos.
- Si se usan proveedores externos con documentos reales, revisar RGPD, contratos de tratamiento de datos y política de retención.

## Proveedores Futuros

`gemini` y `anthropic` ya tienen adaptadores iniciales para API key. No deben incluir credenciales hardcodeadas ni lógica opaca en frontend. Si un proveedor no permite listar modelos o cambia su API, el sistema debe mostrar error claro y permitir modelo manual.

## Búsqueda Web Y Evidencias

El `ModelRouter` no navega por internet por sí mismo. La app añade una capa independiente en `app/research` para recuperar evidencias actuales antes de generar informes y sugerencias.

Variables:

```env
WEB_SEARCH_PROVIDER=duckduckgo
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_TIMEOUT_SECONDS=6
ANALYSIS_LLM_ENABLED=false
TAVILY_API_KEY=
BRAVE_SEARCH_API_KEY=
```

Proveedores:

- `disabled`: no busca; útil para tests.
- `duckduckgo`: proveedor sin clave para desarrollo local.
- `tavily`: búsqueda mediante API key de backend.
- `brave`: Brave Search API mediante API key de backend.

Las fuentes recuperadas se persisten en `Suggestion.source_reference`. En normativa, el servicio prioriza dominios oficiales como BOE, Ministerio de Educación, Educagob y EUR-Lex/Europa. La app no debe inventar legislación ni artículos: si no encuentra base suficiente, marca la sugerencia como baja confianza y pendiente de verificación docente.

`ANALYSIS_LLM_ENABLED=false` mantiene el análisis rápido y basado en búsqueda/API. Al activarlo, el ModelRouter intentará sintetizar las sugerencias con el LLM configurado usando únicamente las fuentes recuperadas como contexto. Si el proveedor no responde o devuelve JSON inválido, el backend vuelve al fallback trazable sin bloquear la revisión docente.
