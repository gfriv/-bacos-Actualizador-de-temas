# AGENTS.md

## Identidad del proyecto

Este repositorio contiene una aplicación para Ábacos destinada a la actualización científica de temas académicos y generación automática de recursos didácticos mediante IA.

La aplicación no es un chatbot general, una plataforma e-learning completa, un CRM ni una app comercial de captación de alumnos.

La aplicación sí es un sistema documental docente: analiza DOCX/PDF, genera informes científicos y curriculares, exige revisión humana y consolida solo cambios aprobados.

## Principio rector

La IA propone. El profesor valida. El sistema solo consolida cambios aprobados.

Nunca debe integrarse automáticamente una modificación no revisada.

## Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, pnpm.
- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic, uv.
- Infra: PostgreSQL, Redis, Docker Compose, almacenamiento local o MinIO.
- IA: ModelRouter con MockProvider por defecto y proveedor OpenAI-compatible configurable por variables de entorno.

## Seguridad

- No hardcodear secretos.
- No registrar claves API en logs.
- No exponer documentos privados.
- Validar extensión y tamaño de archivos.
- Registrar acciones importantes en AuditLog.
- No pedir usuario/contraseña de ChatGPT, Gemini, Claude ni otros servicios externos.

## Flujo esperado

1. Crear proyecto.
2. Subir documento.
3. Extraer texto.
4. Dividir secciones.
5. Generar informes.
6. Crear sugerencias.
7. Revisar sugerencias.
8. Consolidar cambios aprobados.
9. Generar recursos.

## Definición de terminado

Una tarea está terminada cuando compila, tiene tests básicos, no introduce secretos, mantiene la validación docente y deja README actualizado.
