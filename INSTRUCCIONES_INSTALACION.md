# Instrucciones Basicas De Instalacion - Abacos IA

Esta guia explica como instalar y probar la aplicacion de escritorio de Abacos IA en Windows.

## Que Version Hay Ahora

El instalador actual crea una aplicacion de escritorio con Electron. La app abre la interfaz de Abacos y arranca un backend FastAPI local en el propio equipo.

Archivo:

```text
release/AbacosIA-Setup-0.1.0.exe
```

La version actual esta pensada para demo tecnica/local. Todavia no es un instalador completamente autonomo para cualquier ordenador limpio, porque el backend local necesita Python y uv disponibles en el sistema.

## Diferencia Entre Opciones

### 1. Instalador actual

Ventajas:

- Se instala como aplicacion de Windows.
- Guarda datos y documentos en el equipo del usuario.
- Puede usar MockProvider sin coste.
- Puede usar Ollama local si esta instalado.
- No depende necesariamente de Vercel para funcionar.

Limitaciones:

- Necesita Python 3.12 o superior instalado.
- Necesita uv instalado.
- No incluye todavia Python embebido dentro del instalador.
- No esta firmado digitalmente para distribucion publica amplia.

### 2. Instalador autonomo futuro

Ventajas:

- El usuario instalaria un solo `.exe`.
- No tendria que instalar Python ni uv manualmente.
- Mejor para distribuir a profesores no tecnicos.

Trabajo pendiente:

- Empaquetar Python y dependencias dentro del instalador.
- Ajustar rutas internas del backend embebido.
- Probar en una maquina limpia.
- Firmar el ejecutable si se va a distribuir fuera de entorno interno.

### 3. Version web con backend remoto

Ventajas:

- El usuario solo abre una URL.
- No instala nada.
- Actualizaciones centralizadas.
- Mejor para piloto controlado con varios usuarios.

Limitaciones:

- Requiere backend real desplegado con base de datos y almacenamiento persistente.
- Si se usan proveedores externos de IA con documentos reales, hace falta revision RGPD y contrato de tratamiento.
- Ollama local del usuario no puede usarse desde un backend remoto como Vercel.

## Requisitos Para Probar El Instalador Actual

En Windows:

1. Python 3.12 o superior.
2. uv instalado.
3. Opcional: Ollama, si se quiere usar IA local real.

Comprobar Python:

```powershell
python --version
```

Instalar uv si no existe:

```powershell
python -m pip install uv
```

Comprobar uv:

```powershell
python -m uv --version
```

## Instalacion

1. Abrir la carpeta del proyecto:

```text
C:\Users\gfriv\OneDrive\Desktop\codex\pacientes sinteticos nutricia\Abacos\release
```

2. Ejecutar:

```text
AbacosIA-Setup-0.1.0.exe
```

3. Seguir el asistente de instalacion.

4. Abrir la aplicacion desde el acceso directo de Windows.

## Primer Arranque

Al abrir la app:

1. Elegir modo de IA:
   - MockProvider para demo sin coste.
   - API propia si se dispone de clave.
   - Ollama local si Ollama esta instalado.
2. Entrar en modo demo o iniciar sesion.
3. Crear un proyecto.
4. Subir un DOCX o PDF con texto extraible.
5. Generar analisis.
6. Revisar sugerencias.
7. Aprobar o editar sugerencias.
8. Generar documento consolidado.
9. Generar recursos didacticos.

## Modo Recomendado Para Demo Rapida

Usar:

```text
MockProvider
```

No requiere API key, no consume creditos y permite probar el flujo completo.

## Modo Con IA Local

Instalar Ollama:

```text
https://ollama.com
```

Arrancar Ollama y descargar un modelo:

```powershell
ollama serve
ollama pull qwen2.5:7b-instruct
```

En la app, elegir modo local/Ollama. La aplicacion detecta modelos mediante:

```text
http://127.0.0.1:11434/api/tags
```

## Modo Con API Propia

En el selector de IA se puede elegir proveedor API y pegar una clave propia.

Reglas:

- La clave no se guarda en frontend como secreto permanente.
- No se debe introducir usuario ni contrasena de ChatGPT, Gemini o Claude.
- Solo se usan API keys o endpoints compatibles.
- Para documentos reales debe revisarse RGPD antes de enviar contenido a terceros.

## Problemas Frecuentes

### La app no arranca

Comprobar:

```powershell
python --version
python -m uv --version
```

Si Python o uv no existen, instalarlos y volver a abrir la app.

### Ollama no aparece

Comprobar:

```powershell
ollama serve
ollama list
```

La app solo puede detectar Ollama local si esta disponible en:

```text
http://127.0.0.1:11434
```

### El PDF no extrae texto

Si el PDF es escaneado, el MVP puede avisar de que sera necesario OCR. El OCR esta preparado como opcion tecnica, pero no se instala ni se activa por defecto.

### El instalador muestra aviso de Windows

Puede ocurrir porque el ejecutable todavia no esta firmado digitalmente. Para distribucion publica habria que firmarlo.

## Comprobacion Tecnica Del Instalador

El instalador actualizado se genero el 31/05/2026 e incluye el pipeline nuevo:

- ClaimExtractor.
- NormativeEngine.
- ResearchPlanner.
- SourceRanker.
- DocumentBlueprint para recursos.

## Recomendacion Para Siguiente Fase

Para que el instalador sea apto para usuarios no tecnicos, la mejor opcion es crear un instalador autonomo que incluya Python y dependencias del backend, o usar un backend remoto gestionado y dejar Electron como interfaz de escritorio.
