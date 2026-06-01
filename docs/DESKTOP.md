# Aplicacion De Escritorio

La adaptacion de escritorio usa Electron sobre la misma aplicacion Next.js y el mismo backend FastAPI. El objetivo es permitir una demo local con datos en el equipo del profesor, eleccion inicial de IA por API u Ollama y almacenamiento documental fuera del disco efimero de Vercel.

## Estado

Implementado:

- Proceso principal Electron con `contextIsolation` y preload controlado.
- IPC con lista blanca de canales.
- Arranque del backend FastAPI local en `127.0.0.1:8765`.
- Rutas locales de datos en el perfil de usuario para base de datos, subidas, generados y logs.
- Wizard de primer arranque para elegir API propia u Ollama local.
- Deteccion basica de hardware.
- Deteccion de Ollama mediante `http://127.0.0.1:11434/api/tags`.
- Recomendacion de modelos locales.
- Preparacion de instalador NSIS con directorio configurable.
- Runtime Python embebido para arrancar FastAPI sin Python/uv externos en el equipo del usuario.

Pendiente antes de considerar el `.exe` como demo instalable cerrada:

- Probar el instalador en una maquina limpia.
- Anadir tests automatizados de IPC, wizard y arranque de procesos.
- Revisar firma de codigo para distribucion fuera de entorno interno.

## Comandos

Desde la raiz del repositorio:

```bash
corepack pnpm desktop:compile
corepack pnpm desktop:dev
corepack pnpm desktop:build
corepack pnpm desktop:python-runtime
corepack pnpm installer:win
```

`desktop:dev` lanza Next.js en `127.0.0.1:3000` y abre Electron contra ese servidor.

`installer:win` compila Electron, genera el build standalone de Next.js, prepara el runtime Python embebido y crea un instalador NSIS en `release/`.

## Runtime Python Embebido

El script `scripts/prepare-python-runtime.ps1` prepara `desktop-runtime/python` copiando un runtime Python reducido y las dependencias de `apps/api/requirements.txt`. `electron-builder` lo empaqueta como `resources/python`.

En modo empaquetado, Electron intenta usar `resources/python/python.exe` y arranca FastAPI con `python -m uvicorn`, sin depender de `python -m uv run`. En desarrollo se mantiene el modo anterior con Python/uv del sistema.

Medidas verificadas el 31/05/2026:

- `desktop-runtime/python`: 132,7 MB.
- `release/win-unpacked/resources/python`: 133,5 MB.
- `release/AbacosIA-Setup-0.1.2.exe`: 230.199.558 bytes.
- SHA-256 del instalador `0.1.2`: `62963F501BFA21FA617B33B8ED1E5807C7E9213E300424390157C1B0D6B8227C`.

Prueba de paquete desempaquetado:

- Frontend local: `http://127.0.0.1:3765/login`.
- Backend local: `http://127.0.0.1:8765/api/health`.
- Resultado: el paquete contiene el backend corregido y el Python embebido valida que texto docente normal con "todo", URLs publicas con `/app/` y terminos academicos como "Null hypothesis" no bloquean la puerta de calidad, mientras `TODO` tecnico sigue bloqueado.

Ollama solo debe instalarse si se elige modo local real.

El OCR sigue desactivado por defecto. No se instala Tesseract ni se ejecuta OCR salvo que `OCR_ENABLED=true` y el entorno lo tenga preparado explicitamente.

## Datos Locales

Electron configura el backend para usar:

- SQLite local.
- Almacenamiento local para documentos originales.
- Almacenamiento local para recursos generados.
- Logs locales con redaccion de secretos.

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

La app empaquetada intenta arrancar el frontend standalone de Next en `127.0.0.1:3765` y el backend FastAPI con Python embebido. Para un instalador final de cliente queda pendiente:

1. Probar en una maquina limpia.
2. Reducir mas el runtime si el peso del instalador es excesivo.
3. Firmar el ejecutable.
4. Valorar backend remoto gestionado si se requiere uso multiusuario.

Para piloto real con documentos privados sigue siendo necesaria la revision RGPD y contractual si se usan proveedores externos de IA.
