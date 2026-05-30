# Ábacos Academic Update System

Sistema de actualización científica de temas académicos y generación automática de recursos didácticos mediante IA.

El núcleo del producto es:

`DOCX/PDF -> análisis -> informe científico -> informe curricular -> revisión docente -> consolidación aprobada -> recursos didácticos`.

La IA propone. El profesor valida. El sistema solo consolida cambios aprobados o editados por el docente.

También contempla preparación de oposiciones docentes: Infantil, Primaria, Secundaria, Formación Profesional, EOI y especialidades como PT, AL, Inglés, Música o Educación Física. La normativa de convocatoria y la normativa autonómica deben aportarse o verificarse siempre por el profesor.

## Requisitos

- Node.js 22 o superior.
- Corepack para ejecutar pnpm: `corepack pnpm --version`.
- Python 3.12 o superior.
- uv para Python: `python -m pip install uv`.
- Docker Desktop para el arranque con Docker.
- Opcional para IA local real: Ollama con un modelo compatible, por ejemplo `llama3.2:1b`.

## Instalación

```bash
cd Abacos
corepack pnpm install
cd apps/api
python -m uv sync
```

## Frontend local

```bash
cd Abacos
corepack pnpm dev:web
```

Abrir `http://localhost:3000`.

## Backend local

```bash
cd Abacos/apps/api
python -m uv run alembic upgrade head
python -m uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API en `http://localhost:8000/api/health`.

## Acceso Demo

La pantalla de login incluye `Entrar en demo docente`. Ese acceso no exige registro y crea una cartera de proyectos de prueba con documentos, informes, sugerencias y recursos.

Variables relevantes:

```env
DEMO_ACCESS_ENABLED=true
DEMO_USER_EMAIL=demo@abacos.test
```

El acceso demo es para desarrollo, presentaciones y validación de flujo. En producción debe revisarse antes de exponer datos reales.

En preview de Vercel, si no existe una API pública accesible, el botón demo activa un dataset local de solo frontend para poder enseñar el panel, la revisión y los recursos sin registro.

## Selector De IA En La Aplicación

La pantalla de acceso incluye un selector de motor de IA. En cada sesión se puede elegir:

- `API`: OpenAI, Gemini, Claude/Anthropic u otro endpoint compatible con OpenAI.
- `Local`: Ollama en `http://localhost:11434`.
- `MockProvider`: modo de desarrollo sin coste.

La clave API introducida por el usuario se guarda solo en `sessionStorage` del navegador y se envía al backend en la cabecera efímera `X-Abacos-AI-Config` únicamente para operaciones del pipeline: análisis e informes, y generación de recursos. No se persiste en base de datos ni se expone en respuestas públicas.

Endpoints de soporte:

```text
GET  /api/ai/providers
POST /api/ai/providers/validate
POST /api/ai/providers/models
POST /api/ai/ollama/pull
```

Los endpoints genéricos de generación (`/api/ai/generate-text` y `/api/ai/generate-structured`) requieren autenticación para evitar que la API actúe como proxy público de LLM.

## IA Local Con Ollama

Para usar un modelo local real:

```bash
ollama serve
ollama pull qwen2.5:7b-instruct
```

Configura `apps/api/.env` si quieres que el backend local use Ollama por defecto:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:7b-instruct
```

El selector de la interfaz lista modelos instalados usando `/api/tags`. La descarga desde la app mediante `/api/pull` exige confirmación explícita y está deshabilitada por defecto con `OLLAMA_PULL_ENABLED=false`.

No se piden usuarios ni contraseñas de ChatGPT, Gemini, Claude ni servicios similares. Solo se admiten API keys, variables de entorno o endpoints locales.

## Búsqueda Actualizada Para Informes

El análisis incorpora una capa de búsqueda web antes de crear informes y sugerencias. Las fuentes localizadas se guardan en `source_reference` para revisión docente. Si `ANALYSIS_LLM_ENABLED=true` y `LLM_PROVIDER` apunta a un endpoint compatible con OpenAI, el ModelRouter sintetiza sugerencias con esas fuentes como contexto; si el LLM está desactivado o falla, la API conserva un fallback trazable basado en las evidencias recuperadas.

Modo local sin clave:

```env
WEB_SEARCH_PROVIDER=duckduckgo
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_TIMEOUT_SECONDS=6
ANALYSIS_LLM_ENABLED=false
```

Proveedores API preparados:

```env
WEB_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=...
```

```env
WEB_SEARCH_PROVIDER=brave
BRAVE_SEARCH_API_KEY=...
```

Para tests o entornos sin internet:

```env
WEB_SEARCH_PROVIDER=disabled
```

Las sugerencias curriculares priorizan fuentes oficiales como `boe.es`, `doe.juntaex.es`, `educarex.es`, `educagob.educacionfpydeportes.gob.es`, `educacionfpydeportes.gob.es` y dominios europeos oficiales. Para oposiciones, el sistema añade como contraste el reglamento estatal de ingreso docente y, según el nivel, fuentes BOE de Infantil, Primaria, ESO, Bachillerato o Formación Profesional.

Si el profesor indica Extremadura, se añaden fuentes autonómicas oficiales: Ley 4/2011 de Educación de Extremadura, currículos LOMLOE consolidados de Infantil, Primaria, ESO y Bachillerato, normativa de evaluación y referencias de FP cuando proceda. Si no hay fuente oficial suficiente, la sugerencia queda con confianza baja y requiere verificación manual.

## Docker

```bash
cd Abacos/infra
docker compose up --build
```

Servicios:

- web: `http://localhost:3000`
- api: `http://localhost:8000`
- postgres: `localhost:5432`
- redis: `localhost:6379`
- minio: `http://localhost:9001`

El contenedor de API ejecuta `alembic upgrade head` al arrancar. El worker usa el mismo entrypoint y después lanza RQ sobre las colas documentales. Docker no debe recibir documentos reales en el contexto de build; `.dockerignore` excluye `storage`, `.venv`, `node_modules` y logs.

## Migraciones

```bash
cd Abacos/apps/api
python -m uv run alembic revision --autogenerate -m "describe change"
python -m uv run alembic upgrade head
```

## Crear Usuario Inicial

El registro público siempre crea usuarios `teacher`. No se puede escalar a `admin` enviando `role=admin` al endpoint de registro.

Para crear o actualizar el admin inicial, ejecuta el script desde el backend:

```bash
cd Abacos/apps/api
python -m uv run python scripts/create_admin.py \
  --email admin@abacos.local \
  --password "change-me-secure" \
  --full-name "Admin Abacos"
```

Si `uv` no está en PATH, usa `.\.venv\Scripts\python.exe scripts/create_admin.py ...`.

## Cambiar De MockProvider A Proveedor Real

Por defecto:

```env
LLM_PROVIDER=mock
```

Para usar un endpoint compatible con OpenAI:

```env
LLM_PROVIDER=openai_compatible
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=...
```

También puede apuntar a vLLM, Ollama o LM Studio si exponen `/chat/completions`.

## Vercel

El frontend se despliega desde `apps/web`, que es donde vive la app Next.js:

```bash
npx vercel deploy apps/web --yes --project abacos-academic-update-system --prod
```

URL pública actual:

```text
https://abacos-academic-update-system.vercel.app
```

Backend público actual:

```text
https://abacos-api.vercel.app/api
```

El frontend está configurado en Vercel con:

```env
NEXT_PUBLIC_API_URL=https://abacos-api.vercel.app/api
```

El backend serverless de Vercel usa FastAPI, Neon Postgres y `STORAGE_BACKEND=database`, de modo que los documentos generados se guardan en base de datos y no dependen del disco efímero.

Ollama local tampoco funciona desde Vercel contra el ordenador del usuario: el backend desplegado no puede acceder al `localhost` del navegador. Para usar Ollama, ejecuta frontend y backend en local o publica un backend que tenga acceso al servidor Ollama correspondiente.

Para producción completa con colas persistentes se recomienda desplegar también API, worker, PostgreSQL, Redis y almacenamiento documental compartido. Vercel serverless sirve para demo funcional y piloto controlado, pero no sustituye a un backend con worker RQ persistente.

Hay un blueprint inicial en `render.yaml` para desplegar API, worker, PostgreSQL y Redis en Render. Antes de usarlo con documentos reales, revisa almacenamiento persistente, object storage y RGPD.

La guía operativa está en `docs/DEPLOYMENT.md`. Incluye el script `infra/scripts/connect-vercel-api-url.ps1` para configurar `NEXT_PUBLIC_API_URL` en Vercel cuando exista una URL pública del backend.

## Descargas Seguras

La API no expone rutas internas como `file_path` o `docx_path` en sus respuestas públicas. Las descargas pasan por endpoints autenticados:

```text
GET /api/documents/{document_id}/download
GET /api/projects/{project_id}/consolidated/download
GET /api/resources/{resource_id}/download
```

Cada endpoint valida permisos del proyecto y comprueba que el archivo esté dentro del directorio gestionado configurado.

## Tests Y Calidad

Frontend:

```bash
cd Abacos
corepack pnpm lint:web
corepack pnpm typecheck:web
corepack pnpm test:web
```

Backend:

```bash
cd Abacos/apps/api
python -m uv run ruff check
python -m uv run pytest
```

## Estado Actual

La base incluye arquitectura, dependencias, diseño visual Ábacos, rutas, modelos, ModelRouter, workers, docs y tests mínimos. El frontend conecta con la API para login local/demo, creación de proyecto, subida DOCX/PDF, análisis con búsqueda trazable, revisión de sugerencias, consolidación y recursos.

Pendiente para piloto real: colas asíncronas completas, despliegue backend gestionado, RGPD/contratos de tratamiento, OCR para PDFs escaneados y evaluación pedagógica con docentes.
