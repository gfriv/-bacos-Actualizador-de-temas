from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import select

from app.core.config import settings
from app.db.models import (
    AnalysisRun,
    AnalysisRunStatus,
    ConsolidatedDocument,
    DocumentSection,
    GeneratedResource,
    Project,
    ProjectStatus,
    ResourceType,
    Suggestion,
    SuggestionStatus,
)
from app.db.session import SessionLocal
from app.document_processing.docx_writer import write_markdown_docx
from app.llm.model_router import ModelRouter
from app.services.audit import audit
from app.services.consolidation import build_consolidated_markdown
from app.services.file_storage import save_managed_file, uses_database_storage
from app.services.report_quality_gate import assert_export_quality
from app.services.research_analysis import build_research_analysis
from app.services.resources import RESOURCE_TITLES, decorate_resource_markdown

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MARKDOWN_MEDIA_TYPE = "text/markdown; charset=utf-8"


def document_processing_worker(project_id: int) -> dict[str, int | str]:
    return {"worker": "DocumentProcessingWorker", "project_id": project_id, "status": "handled_by_api"}


def research_worker(
    analysis_run_id: int | None = None,
    project_id: int | None = None,
    user_id: int | None = None,
) -> dict[str, int | str]:
    if project_id is None:
        project_id = int(analysis_run_id or 0)
        analysis_run_id = None
    with SessionLocal() as db:
        try:
            run = _start_run(db, analysis_run_id, project_id)
            project = _get_project(db, project_id)
            sections = list(
                db.scalars(
                    select(DocumentSection)
                    .where(DocumentSection.project_id == project.id)
                    .order_by(DocumentSection.order_index.asc())
                )
            )
            if not sections:
                raise RuntimeError("No hay secciones documentales para analizar.")

            analysis = asyncio.run(build_research_analysis(project, sections))
            for report in analysis.reports:
                assert_export_quality(
                    report.content_markdown,
                    artifact_type=report.report_type.value,
                    require_sources=report.report_type.value
                    in {"scientific_update", "curriculum_mapping", "source_validation"},
                )
            db.add_all([*analysis.reports, *analysis.suggestions])
            project.status = ProjectStatus.under_review
            audit(
                db,
                "research_analysis_worker_completed",
                user_id=user_id,
                project_id=project.id,
                analysis_run_id=analysis_run_id,
                reports=len(analysis.reports),
                suggestions=len(analysis.suggestions),
            )
            _complete_run(run)
            db.commit()
            return {
                "worker": "ResearchWorker",
                "project_id": project.id,
                "reports": len(analysis.reports),
                "suggestions": len(analysis.suggestions),
                "status": "completed",
            }
        except Exception as exc:
            _fail_run(db, analysis_run_id, project_id, user_id, exc)
            raise


def curriculum_worker(
    analysis_run_id: int | None = None,
    project_id: int | None = None,
    user_id: int | None = None,
) -> dict[str, int | str]:
    return research_worker(analysis_run_id=analysis_run_id, project_id=project_id, user_id=user_id)


def consolidation_worker(
    analysis_run_id: int | None = None,
    project_id: int | None = None,
    user_id: int | None = None,
) -> dict[str, int | str]:
    if project_id is None:
        project_id = int(analysis_run_id or 0)
        analysis_run_id = None
    with SessionLocal() as db:
        try:
            run = _start_run(db, analysis_run_id, project_id)
            project = _get_project(db, project_id)
            sections = list(db.scalars(select(DocumentSection).where(DocumentSection.project_id == project.id)))
            suggestions = list(db.scalars(select(Suggestion).where(Suggestion.project_id == project.id)))
            approved_count = sum(
                1
                for suggestion in suggestions
                if suggestion.status in {SuggestionStatus.approved, SuggestionStatus.edited}
            )
            if approved_count == 0:
                raise RuntimeError("No hay sugerencias aprobadas o editadas para consolidar.")

            markdown = build_consolidated_markdown(sections, suggestions, project_title=project.title, provider="worker")
            assert_export_quality(markdown, artifact_type="consolidated_document")
            docx_path = _write_consolidated_docx(db, project.id, markdown)
            consolidated = ConsolidatedDocument(
                project_id=project.id,
                content_markdown=markdown,
                docx_path=docx_path,
            )
            db.add(consolidated)
            project.status = ProjectStatus.consolidated
            audit(
                db,
                "document_consolidated_worker_completed",
                user_id=user_id,
                project_id=project.id,
                approved_count=approved_count,
                analysis_run_id=analysis_run_id,
            )
            _complete_run(run)
            db.commit()
            return {"worker": "ConsolidationWorker", "project_id": project.id, "status": "completed"}
        except Exception as exc:
            _fail_run(db, analysis_run_id, project_id, user_id, exc)
            raise


def resource_generation_worker(
    analysis_run_id: int | None = None,
    project_id: int | None = None,
    resource_type: str = "esquema_desarrollado",
    user_id: int | None = None,
) -> dict[str, int | str]:
    if project_id is None:
        project_id = int(analysis_run_id or 0)
        analysis_run_id = None
    with SessionLocal() as db:
        try:
            run = _start_run(db, analysis_run_id, project_id)
            project = _get_project(db, project_id)
            resource_enum = ResourceType(resource_type)
            consolidated = db.scalar(
                select(ConsolidatedDocument)
                .where(ConsolidatedDocument.project_id == project.id)
                .order_by(ConsolidatedDocument.created_at.desc())
            )
            if consolidated is None:
                raise RuntimeError("Genera el documento consolidado antes de crear recursos didacticos.")

            raw_content = asyncio.run(
                ModelRouter().generate_document_resource(consolidated.content_markdown, resource_enum.value)
            )
            title = RESOURCE_TITLES[resource_enum]
            content = decorate_resource_markdown(
                content=raw_content,
                title=title,
                project_title=project.title,
                provider=settings.llm_provider,
                model=settings.llm_model or None,
            )
            assert_export_quality(content, artifact_type=resource_enum.value)
            resource = GeneratedResource(
                project_id=project.id,
                resource_type=resource_enum,
                title=title,
                content_markdown=content,
            )
            db.add(resource)
            db.flush()
            resource.file_path = save_managed_file(
                db,
                content.encode("utf-8"),
                root_dir=settings.generated_dir,
                filename=f"project-{project.id}-resource-{resource.id}-{resource_enum.value}.md",
                content_type=MARKDOWN_MEDIA_TYPE,
                namespace="generated",
            )
            project.status = ProjectStatus.resources_generated
            audit(
                db,
                "resource_generation_worker_completed",
                user_id=user_id,
                project_id=project.id,
                resource_type=resource_enum.value,
                analysis_run_id=analysis_run_id,
            )
            _complete_run(run)
            db.commit()
            return {
                "worker": "ResourceGenerationWorker",
                "project_id": project.id,
                "resource_type": resource_enum.value,
                "status": "completed",
            }
        except Exception as exc:
            _fail_run(db, analysis_run_id, project_id, user_id, exc)
            raise


def _start_run(db, analysis_run_id: int | None, project_id: int) -> AnalysisRun | None:
    project = _get_project(db, project_id)
    project.status = ProjectStatus.processing
    if analysis_run_id is None:
        db.commit()
        return None
    run = db.get(AnalysisRun, analysis_run_id)
    if run is None:
        raise RuntimeError("AnalysisRun no encontrado.")
    run.status = AnalysisRunStatus.running
    run.started_at = datetime.now(UTC)
    run.error_message = None
    db.commit()
    return run


def _complete_run(run: AnalysisRun | None) -> None:
    if run is None:
        return
    run.status = AnalysisRunStatus.completed
    run.completed_at = datetime.now(UTC)


def _fail_run(
    db,
    analysis_run_id: int | None,
    project_id: int | None,
    user_id: int | None,
    exc: Exception,
) -> None:
    db.rollback()
    run = db.get(AnalysisRun, analysis_run_id) if analysis_run_id is not None else None
    if run is not None:
        run.status = AnalysisRunStatus.failed
        run.completed_at = datetime.now(UTC)
        run.error_message = _safe_error_message(exc)
    project = db.get(Project, project_id) if project_id is not None else None
    if project is not None:
        project.status = ProjectStatus.error
    audit(
        db,
        "worker_failed",
        user_id=user_id,
        project_id=project_id,
        analysis_run_id=analysis_run_id,
        error=_safe_error_message(exc),
    )
    db.commit()


def _get_project(db, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise RuntimeError("Proyecto no encontrado.")
    return project


def _write_consolidated_docx(db, project_id: int, markdown: str) -> str:
    docx_filename = f"project-{project_id}-consolidated.docx"
    if uses_database_storage():
        with TemporaryDirectory() as tmp_dir:
            docx_path = Path(tmp_dir) / docx_filename
            write_markdown_docx(markdown, docx_path)
            return save_managed_file(
                db,
                docx_path.read_bytes(),
                root_dir=settings.generated_dir,
                filename=docx_filename,
                content_type=DOCX_MEDIA_TYPE,
                namespace="generated",
            )
    generated_dir = Path(settings.generated_dir).resolve()
    generated_dir.mkdir(parents=True, exist_ok=True)
    docx_path = generated_dir / docx_filename
    write_markdown_docx(markdown, docx_path)
    return str(docx_path)


def _safe_error_message(exc: Exception) -> str:
    message = str(exc).splitlines()[0][:500] or "Error del worker."
    if re.search(r"(?:[A-Za-z]:\\|/app/|/home/|/tmp/|sk-[A-Za-z0-9_-]{8,}|api[_-]?key)", message, re.I):
        return "Error interno del worker. Revisa logs privados del servidor."
    return message
