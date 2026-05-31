# Instrucciones Basicas De Instalacion - Abacos IA

Esta guia explica como instalar y probar la aplicacion de escritorio de Abacos IA en Windows.

## Que Version Hay Ahora

El instalador actual crea una aplicacion de escritorio con Electron. La app abre la interfaz de Abacos y arranca un backend FastAPI local en el propio equipo.

Archivo:

```text
release/AbacosIA-Setup-0.1.1.exe
```

La version actual esta pensada para demo tecnica/local. El instalador generado con el runtime embebido incluye Python y las dependencias del backend, por lo que el usuario final no deberia tener que instalar Python ni uv para arrancar la aplicacion.

## Diferencia Entre Opciones

### 1. Instalador actual autonomo

Ventajas:

- Se instala como aplicacion de Windows.
- Guarda datos y documentos en el equipo del usuario.
- Puede usar MockProvider sin coste.
- Puede usar Ollama local si esta instalado.
- No depende necesariamente de Vercel para funcionar.
- Incluye Python 3.12 y dependencias del backend dentro del instalador.

Limitaciones:

- El instalador pesa mas porque incluye Python y dependencias del backend.
- No esta firmado digitalmente para distribucion publica amplia.
- Sigue siendo recomendable probarlo en una maquina limpia antes de entregarlo a usuarios finales.

### 2. Version web con backend remoto

Ventajas:

- El usuario solo abre una URL.
- No instala nada.
- Actualizaciones centralizadas.
- Mejor para piloto controlado con varios usuarios.

Limitaciones:

- Requiere backend real desplegado con base de datos y almacenamiento persistente.
- Si se usan proveedores externos de IA con documentos reales, hace falta revision RGPD y contrato de tratamiento.
- Ollama local del usuario no puede usarse desde un backend remoto como Vercel.

### 3. Instalador tecnico sin Python embebido

Ventajas:

- Pesa menos.
- Es util para desarrollo o equipos tecnicos.

Limitaciones:

- Requiere Python y uv instalados manualmente.
- No es recomendable para profesorado no tecnico.

## Requisitos Para Probar El Instalador Actual

En Windows:

1. Ejecutar el instalador.
2. Opcional: instalar Ollama, si se quiere usar IA local real.

Python y uv solo son necesarios para desarrollo o para generar de nuevo el instalador desde el repositorio.

## Instalacion

1. Abrir la carpeta del proyecto:

```text
C:\Users\gfriv\OneDrive\Desktop\codex\pacientes sinteticos nutricia\Abacos\release
```

2. Ejecutar:

```text
AbacosIA-Setup-0.1.1.exe
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
%APPDATA%\AbacosIA\logs
```

Revisar `desktop-backend.log`. Si el instalador no se ha generado con runtime embebido, entonces si haran falta Python y uv.

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
- Runtime Python embebido para arrancar FastAPI sin Python externo.

Tamanos verificados:

- Instalador: `230.191.110 bytes` (`219,5 MB` aprox.).
- Runtime Python incluido en `win-unpacked`: `133,5 MB` aprox.
- SHA-256: `9E7CBB4583BE660A8EA95CDF4C2CD1DDB635B5F55FC6DD2D42589017DA6470AC`.

Pruebas realizadas:

- `resources/python/python.exe` importa FastAPI, Uvicorn y Alembic.
- El paquete contiene la puerta de calidad corregida: acepta texto docente normal con "todo", URLs publicas con `/app/` y terminos academicos como "Null hypothesis".
- El mismo paquete sigue bloqueando placeholders tecnicos reales como `TODO`.

## Recomendacion Para Siguiente Fase

Para que el instalador sea apto para usuarios no tecnicos, queda pendiente probarlo en una maquina limpia y firmar el ejecutable. Para entornos multiusuario o piloto real, sigue siendo recomendable valorar backend remoto gestionado con almacenamiento persistente.
