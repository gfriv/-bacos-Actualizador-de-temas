# Aplicación De Escritorio

La adaptación de escritorio usa Electron sobre la misma aplicación Next.js y el mismo backend FastAPI. El objetivo es permitir una demo local con datos en el equipo del profesor, elección inicial de IA por API u Ollama y almacenamiento documental fuera del disco efímero de Vercel.

## Estado

Implementado:

- Proceso principal Electron con `contextIsolation` y preload controlado.
- IPC con lista blanca de canales.
- Arranque del backend FastAPI local en `127.0.0.1:8765`.
- Rutas locales de datos en el perfil de usuario para base de datos, subidas, generados y logs.
- Wizard de primer arranque para elegir API propia u Ollama local.
- Detección básica de hardware.
- Detección de Ollama mediante `http://127.0.0.1:11434/api/tags`.
- Recomendación de modelos locales.
- Preparación de instalador NSIS con directorio configurable.

Pendiente antes de considerar el `.exe` como demo instalable cerrada:

- Probar el instalador en una máquina limpia.
- Decidir si se embebe Python/uv o si se documenta como requisito externo.
- Añadir tests automatizados de IPC, wizard y arranque de procesos.
- Revisar firma de código para distribución fuera de entorno interno.

## Comandos

Desde la raíz del repositorio:

```bash
corepack pnpm desktop:compile
corepack pnpm desktop:dev
corepack pnpm desktop:build
corepack pnpm installer:win
```

`desktop:dev` lanza Next.js en `127.0.0.1:3000` y abre Electron contra ese servidor.

`installer:win` compila Electron, genera el build standalone de Next.js y crea un instalador NSIS en `release/`.

## Requisitos Locales

La versión actual no es todavía completamente autónoma. Para funcionar en escritorio necesita:

- Node/Electron incluidos por el instalador.
- Python 3.12 o superior disponible en el equipo.
- `uv` disponible como módulo Python: `python -m uv`.
- Dependencias Python sincronizadas o descargables por `uv`.
- Ollama instalado solo si se elige modo local real.

El OCR sigue desactivado por defecto. No se instala Tesseract ni se ejecuta OCR salvo que `OCR_ENABLED=true` y el entorno lo tenga preparado explícitamente.

## Datos Locales

Electron configura el backend para usar:

- SQLite local.
- Almacenamiento local para documentos originales.
- Almacenamiento local para recursos generados.
- Logs locales con redacción de secretos.

Las rutas se calculan con APIs del sistema operativo y no dependen del usuario de Windows ni de rutas absolutas del repositorio.

## Seguridad

- El renderer no tiene `nodeIntegration`.
- El preload expone solo `window.abacosDesktop`.
- Los canales IPC pasan por lista blanca.
- Los permisos del navegador se deniegan por defecto.
- Las claves API no deben imprimirse en logs.
- Los logs pasan por `redactSecrets`.
- El modo Ollama solo apunta a `127.0.0.1:11434` en escritorio.

## Limitaciones Actuales

La app empaquetada ya intenta arrancar el frontend standalone de Next en `127.0.0.1:3765`, pero el backend FastAPI aún depende de Python/uv externos. Para un instalador final de cliente hay que decidir una de estas estrategias:

1. Incluir runtime Python y dependencias dentro del instalador.
2. Distribuir un instalador técnico con prerequisitos.
3. Usar backend remoto gestionado y dejar escritorio como shell local.

Para piloto real con documentos privados sigue siendo necesaria la revisión RGPD y contractual si se usan proveedores externos de IA.
