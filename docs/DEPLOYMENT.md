# Deployment

## Frontend

El frontend se despliega en Vercel desde `apps/web`.

```powershell
npx vercel deploy apps/web --yes --project abacos-academic-update-system --prod --scope guillermo-colegionazars-projects
```

URL pública:

```text
https://abacos-academic-update-system.vercel.app
```

## Backend Real

FastAPI necesita un servicio persistente con:

- PostgreSQL;
- Redis;
- worker RQ;
- almacenamiento persistente para documentos;
- variables de entorno privadas.

Vercel no es el destino recomendado para este backend porque el pipeline documental necesita workers, Redis y almacenamiento persistente. La plantilla raíz `render.yaml` prepara un despliegue Git-backed en Render con:

- `abacos-api`;
- `abacos-worker`;
- `abacos-postgres`;
- `abacos-redis`;
- disco persistente de 1 GB para `/app/storage` en la API.

## Backend Serverless En Vercel

También se ha preparado `apps/api` como proyecto FastAPI serverless para Vercel:

- `apps/api/index.py` expone `app.main:app` y ejecuta migraciones si `RUN_MIGRATIONS_ON_STARTUP=true`;
- `apps/api/vercel.json` usa la detección nativa de FastAPI en Vercel;
- `apps/api/requirements.txt` instala dependencias Python;
- `STORAGE_BACKEND=database` guarda DOCX/PDF y recursos en la tabla `file_blobs`, evitando depender del disco efímero.

Este modo permite probar un backend público funcional, pero no sustituye al despliegue con worker persistente para producción completa.

Despliegue público actual:

```text
Frontend: https://abacos-academic-update-system.vercel.app
Backend:  https://abacos-api.vercel.app/api
```

Pasos:

1. Acepta los términos de Neon Marketplace en Vercel si aún no están aceptados:

```text
https://vercel.com/guillermo-colegionazars-projects/~/integrations/accept-terms/neon?source=cli
```

2. Provisiona Neon para el proyecto `abacos-api`:

```powershell
npx vercel install neon --name abacos-postgres --plan free -e production -e preview --cwd apps/api --scope guillermo-colegionazars-projects
```

Si la CLI indica que el plan `free` no existe, usa el plan vigente `free_v3`:

```powershell
npx vercel install neon --name abacos-postgres --plan free_v3 -e production -e preview --cwd apps/api --scope guillermo-colegionazars-projects
```

3. Configura las variables restantes:

```powershell
.\infra\scripts\configure-vercel-api-env.ps1
```

Si Neon no sincroniza `DATABASE_URL`, pásala explícitamente:

```powershell
.\infra\scripts\configure-vercel-api-env.ps1 -DatabaseUrl "postgresql://..."
```

4. Despliega el backend:

```powershell
npx vercel deploy apps/api --yes --project abacos-api --prod --scope guillermo-colegionazars-projects
```

5. Copia la URL resultante y conéctala al frontend:

```powershell
.\infra\scripts\connect-vercel-api-url.ps1 -ApiUrl "https://abacos-api.vercel.app/api"
npx vercel deploy apps/web --yes --project abacos-academic-update-system --prod --scope guillermo-colegionazars-projects
```

## Pasos Render

Render Blueprints requieren un repositorio Git remoto.

1. Crea un repositorio Git privado o público y sube este proyecto.
2. En Render, crea un Blueprint desde ese repositorio.
3. Render detectará `render.yaml` en la raíz del repositorio.
4. Espera a que `abacos-api` termine el build y pase `/api/health`.
5. Copia la URL pública de la API, por ejemplo:

```text
https://abacos-api.onrender.com/api
```

6. Configura Vercel con esa URL:

```powershell
.\infra\scripts\connect-vercel-api-url.ps1 -ApiUrl "https://abacos-api.onrender.com/api"
```

7. Redespliega Vercel:

```powershell
npx vercel deploy apps/web --yes --project abacos-academic-update-system --prod --scope guillermo-colegionazars-projects
```

## Variables Críticas

Backend:

```env
DATABASE_URL=
REDIS_URL=
JWT_SECRET=
CORS_ORIGINS=["https://abacos-academic-update-system.vercel.app"]
UPLOAD_DIR=/app/storage/uploads
GENERATED_DIR=/app/storage/generated
LLM_PROVIDER=mock
DEMO_ACCESS_ENABLED=false
```

Frontend:

```env
NEXT_PUBLIC_API_URL=https://tu-api-publica/api
```

## Limitaciones Actuales

- El disco de Render está montado en la API. Si en el futuro los workers procesan documentos en segundo plano, conviene mover documentos a object storage compartido.
- Ollama local no funciona desde Vercel contra el ordenador del usuario. Para Ollama, el backend debe correr en la misma máquina o red que Ollama.
- Antes de piloto real con documentos privados hay que revisar RGPD, retención, backups y cifrado.
