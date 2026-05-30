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
- Opcional, si se decide activar OCR en otra fase: Tesseract OCR con idiomas `spa` y `eng`.
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

## OCR Para PDF Escaneado

El backend intenta extraer texto con `pdfplumber` y `pypdf`. El OCR queda preparado pero desactivado por defecto. Si en otra fase se activa `OCR_ENABLED=true`, renderizará páginas y ejecutará Tesseract OCR, siempre que el motor esté instalado explícitamente en el entorno.

Variables relevantes:

```env
OCR_ENABLED=false
OCR_LANGUAGES=spa+eng
OCR_DPI=200
OCR_MAX_PAGES=40
OCR_TIMEOUT_SECONDS=30
OCR_TESSERACT_CMD=
```

No se instala Tesseract automáticamente. Si más adelante se decide usar OCR, instala Tesseract manualmente o en una imagen específica, instala la dependencia opcional `pytesseract` y define `OCR_TESSERACT_CMD` si el ejecutable no está en `PATH`.

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

## Busqueda Actualizada Para Informes

El analisis incorpora una capa opcional de busqueda web antes de crear informes y sugerencias. Por privacidad, queda desactivada por defecto. Las fuentes localizadas se guardan en `source_reference` para revision docente. Si `ANALYSIS_LLM_ENABLED=true` y `LLM_PROVIDER` apunta a un proveedor permitido, el ModelRouter sintetiza sugerencias con esas fuentes como contexto; si el LLM esta desactivado o falla, la API conserva un fallback trazable basado en las evidencias recuperadas.

Modo seguro por defecto:

```env
WEB_SEARCH_PROVIDER=disabled
EXTERNAL_WEB_SEARCH_ENABLED=false
WEB_SEARCH_MAX_RESULTS=5
WEB_SEARCH_TIMEOUT_SECONDS=6
ANALYSIS_LLM_ENABLED=false
```

Modo local con busqueda web sin clave, solo si el operador acepta enviar consultas a un buscador externo:

```env
WEB_SEARCH_PROVIDER=duckduckgo
EXTERNAL_WEB_SEARCH_ENABLED=true
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
EXTERNAL_WEB_SEARCH_ENABLED=false
```

Las sugerencias curriculares priorizan fuentes oficiales como `boe.es`, `doe.juntaex.es`, `educarex.es`, `educagob.educacionfpydeportes.gob.es`, `educacionfpydeportes.gob.es` y dominios europeos oficiales. Para oposiciones, el sistema añade como contraste el reglamento estatal de ingreso docente y, según el nivel, fuentes BOE de Infantil, Primaria, ESO, Bachillerato o Formación Profesional.

Si el profesor indica Extremadura, se añaden fuentes autonómicas oficiales: Ley 4/2011 de Educación de Extremadura, currículos LOMLOE consolidados de Infantil, Primaria, ESO y Bachillerato, normativa de evaluación y referencias de FP cuando proceda. Si no hay fuente oficial suficiente, la sugerencia queda con confianza baja y requiere verificación manual.

El pipeline genera seis informes diferenciados: diagnóstico inicial, actualización científica, mapeo curricular, validación de fuentes, propuestas de cambio y trazabilidad técnica. Antes de descargar informes, consolidado o recursos, `ReportQualityGate` bloquea claves, rutas internas, placeholders y contenido sin aviso de asistencia de IA.

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

Verificacion completa en una maquina con Docker Desktop:

```powershell
.\infra\scripts\verify-docker.ps1
```

El repositorio incluye tambien `.github/workflows/ci.yml`, que valida backend, frontend, migraciones Alembic y `docker compose` en runners con Docker. En esta maquina local el script fallara mientras Docker no este en `PATH`; ese fallo es de entorno, no del compose.

## Migraciones

```bash
cd Abacos/apps/api
python -m uv run alembic revision --autogenerate -m "describe change"
python -m uv run alembic upgrade head
```

La historia Alembic queda linealizada con una revision de merge `0003_merge_report_types_and_file_blobs`; `alembic heads` debe devolver una sola cabeza.

## Workers RQ

El backend conserva endpoints sincronos para demo y anade endpoints asincronos para un backend con Redis/worker persistente:

```text
POST /api/projects/{project_id}/analysis/research/queue
POST /api/projects/{project_id}/consolidate/queue
POST /api/projects/{project_id}/resources/queue
GET  /api/analysis-runs/{analysis_run_id}
```

Por seguridad, las rutas `/queue` no aceptan configuracion BYOK por `X-Abacos-AI-Config`, porque una clave API podria quedar persistida en Redis. Los jobs usan el proveedor configurado en variables de entorno del backend.

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
EXTERNAL_AI_PROVIDERS_ENABLED=true
EXTERNAL_AI_DATA_PROCESSING_CONFIRMED=true
```

Tambien puede apuntar a vLLM, Ollama o LM Studio si exponen `/chat/completions`. Si el endpoint es publico o de un proveedor externo, el backend exige activar los dos flags anteriores para dejar constancia operativa de la revision RGPD/contrato de tratamiento. Los endpoints locales o privados solo se permiten cuando el backend se ejecuta en entorno local compatible; Vercel no puede llamar al `localhost` del usuario.

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

La guía operativa está en `docs/DEPLOYMENT.md`. Incluye el script `infra/scripts/connect-vercel-api-url.ps1` para configurar `NEXT_PUBLIC_API_URL` en Vercel cuando exista una URL pública del backend. La puerta operativa para RGPD/IA externa está en `docs/RGPD_PILOT.md`.

## Descargas Seguras

La API no expone rutas internas como `file_path` o `docx_path` en sus respuestas públicas. Las descargas pasan por endpoints autenticados:

```text
GET /api/documents/{document_id}/download
GET /api/reports/{report_id}/download
GET /api/projects/{project_id}/consolidated/download
GET /api/resources/{resource_id}/download
```

Cada endpoint valida permisos del proyecto y comprueba que el archivo esté dentro del directorio gestionado configurado. Los informes, recursos y consolidados también pasan por `ReportQualityGate` para evitar filtraciones de rutas internas o claves.

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

La base incluye arquitectura, dependencias, diseño visual Ábacos, rutas, modelos, ModelRouter, workers RQ, docs y tests mínimos. El frontend conecta con la API para login local/demo, creación de proyecto, subida DOCX/PDF, análisis con búsqueda trazable opcional, revisión de sugerencias, consolidación y recursos.

El backend deja preparada una integración OCR opcional para PDFs escaneados, pero `OCR_ENABLED=false` por defecto y no se instala Tesseract automáticamente.

Pendiente para piloto real: activar un backend gestionado con el blueprint `render.yaml` o servicio equivalente, configurar almacenamiento documental compartido/object storage si API y worker no comparten disco, cerrar revisión RGPD formal antes de documentos reales, aislar OCR con límites de CPU/memoria en producción y evaluación pedagógica con docentes.
