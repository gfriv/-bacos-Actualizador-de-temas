from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import (
    ConsolidatedDocument,
    Document,
    DocumentSection,
    GeneratedResource,
    Project,
    ProjectStatus,
    Report,
    ReportType,
    ResourceType,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
    User,
    UserRole,
)
from app.services.audit import audit
from app.services.resources import RESOURCE_TITLES


def get_or_create_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == settings.demo_user_email))
    if user is not None:
        ensure_demo_projects(db, user)
        return user

    user = User(
        email=settings.demo_user_email,
        password_hash=hash_password("demo-access-disabled-for-ui"),
        full_name="Docente Demo Ábacos",
        role=UserRole.teacher,
    )
    db.add(user)
    db.flush()
    audit(db, "demo_user_created", user_id=user.id)
    ensure_demo_projects(db, user)
    return user


def ensure_demo_projects(db: Session, user: User) -> None:
    existing = list(db.scalars(select(Project).where(Project.owner_id == user.id)))
    if existing:
        _repair_demo_copy(db, existing)
        _ensure_opposition_demo_project(db, user, existing)
        return

    review_project = _create_project(
        db,
        user,
        title="La célula y la organización celular",
        area="Biología y Geología",
        level="ESO",
        status=ProjectStatus.under_review,
    )
    _add_document_flow(db, review_project, filename="tema-celula-demo.docx")

    consolidated_project = _create_project(
        db,
        user,
        title="Ecosistemas, energía y sostenibilidad",
        area="Biología y Geología",
        level="Bachillerato",
        status=ProjectStatus.resources_generated,
    )
    _add_document_flow(db, consolidated_project, filename="tema-ecosistemas-demo.docx")
    suggestions = list(
        db.scalars(select(Suggestion).where(Suggestion.project_id == consolidated_project.id))
    )
    if suggestions:
        suggestions[0].status = SuggestionStatus.approved
        suggestions[0].teacher_notes = "Aceptada para la versión consolidada de demostración."
    if len(suggestions) > 1:
        suggestions[1].status = SuggestionStatus.rejected
        suggestions[1].teacher_notes = "No se integra porque requiere normativa más específica."
    consolidated = ConsolidatedDocument(
        project_id=consolidated_project.id,
        content_markdown=(
            "# Ecosistemas, energía y sostenibilidad\n\n"
            "Documento consolidado de demostración con cambios aprobados por el docente.\n\n"
            "## Cambios integrados\n"
            "- Actualización científica validada.\n"
            "- Contextualización curricular revisada por el profesor.\n"
        ),
        docx_path=None,
    )
    db.add(consolidated)
    db.add(
        GeneratedResource(
            project_id=consolidated_project.id,
            resource_type=ResourceType.esquema_desarrollado,
            title=RESOURCE_TITLES[ResourceType.esquema_desarrollado],
            content_markdown=(
                "# Esquema desarrollado\n\n"
                "1. Concepto de ecosistema.\n"
                "2. Flujo de energía.\n"
                "3. Sostenibilidad y aplicación didáctica.\n"
            ),
        )
    )

    draft_project = _create_project(
        db,
        user,
        title="La literatura del Siglo de Oro",
        area="Lengua Castellana y Literatura",
        level="Bachillerato",
        status=ProjectStatus.draft,
    )

    opposition_project = _create_project(
        db,
        user,
        title="Tema 3. Desarrollo evolutivo de 0 a 6 años",
        area="Educación Infantil",
        level="Oposiciones Educación Infantil",
        status=ProjectStatus.reports_generated,
        legal_framework=(
            "LOMLOE, Real Decreto 95/2022, convocatoria de oposiciones y normativa autonómica "
            "aportada por el docente."
        ),
        bibliography_notes="Temario base de preparación de oposiciones y materiales de academia revisados.",
        instructions="Orientar las sugerencias a defensa ante tribunal y programación didáctica.",
    )
    _add_document_flow(db, opposition_project, filename="tema-desarrollo-evolutivo-infantil-demo.docx")
    audit(db, "demo_projects_seeded", user_id=user.id, project_id=draft_project.id)


def _create_project(
    db: Session,
    user: User,
    *,
    title: str,
    area: str,
    level: str,
    status: ProjectStatus,
    legal_framework: str = "LOMLOE y normativa autonómica aportada por el docente.",
    bibliography_notes: str = "Bibliografía base pendiente de verificación por el profesor.",
    instructions: str = "Mantener cambios localizados y revisión docente obligatoria.",
) -> Project:
    project = Project(
        owner_id=user.id,
        title=title,
        area=area,
        educational_level=level,
        legal_framework=legal_framework,
        bibliography_notes=bibliography_notes,
        instructions=instructions,
        status=status,
    )
    db.add(project)
    db.flush()
    return project


def _add_document_flow(db: Session, project: Project, *, filename: str) -> None:
    text = _demo_text(project.title)
    document = Document(
        project_id=project.id,
        original_filename=filename,
        file_path=f"demo://{filename}",
        file_type="docx",
        extracted_text=text,
    )
    db.add(document)
    db.flush()

    section = DocumentSection(
        project_id=project.id,
        title="Introducción",
        order_index=0,
        content=text,
        summary="Apartado inicial para revisión científica y curricular localizada.",
        detected_concepts=["actualización científica", "currículo", "validación docente"],
    )
    db.add(section)
    db.flush()

    db.add_all(
        [
            Report(
                project_id=project.id,
                report_type=ReportType.scientific_update,
                title="Informe de actualización científica",
                content_markdown=(
                    "## Diagnóstico inicial\n\n"
                    "- Hay conceptos que deben verificarse con bibliografía actual.\n"
                    "- No se inventan referencias.\n"
                    "- Las propuestas son localizadas y requieren validación docente.\n"
                ),
            ),
            Report(
                project_id=project.id,
                report_type=ReportType.curriculum_mapping,
                title="Informe legislativo y curricular",
                content_markdown=(
                    "## Contextualización curricular\n\n"
                    "- El análisis usa la normativa introducida por el profesor.\n"
                    "- La relación con competencias y saberes debe aprobarla el docente.\n"
                ),
            ),
            Suggestion(
                project_id=project.id,
                section_id=section.id,
                suggestion_type=SuggestionType.scientific_update,
                original_fragment="El tema contiene conceptos que deben verificarse con bibliografía científica actual.",
                proposed_change="Actualizar este fragmento con una formulación científica vigente y verificable.",
                justification="Sugerencia demo para validar revisión humana antes de consolidar.",
                source_reference="DemoProvider; requiere fuente real antes de aprobación.",
                confidence_level="medium",
                status=SuggestionStatus.pending,
            ),
            Suggestion(
                project_id=project.id,
                section_id=section.id,
                suggestion_type=SuggestionType.legal_curricular,
                original_fragment="La conexión curricular debe apoyarse en la normativa aportada.",
                proposed_change="Relacionar el apartado con competencias, criterios y saberes cuando haya base normativa suficiente.",
                justification="La contextualización curricular debe estar trazada a normativa validada.",
                source_reference=project.legal_framework,
                confidence_level="medium",
                status=SuggestionStatus.pending,
            ),
        ]
    )


def _demo_text(title: str) -> str:
    return (
        f"# {title}\n\n"
        "## Introducción\n"
        "El tema contiene conceptos que deben verificarse con bibliografía científica actual antes de integrarse.\n\n"
        "## Marco curricular\n"
        "La conexión curricular debe apoyarse en la normativa aportada y validarse por el profesor.\n\n"
        "## Aplicación didáctica\n"
        "El documento consolidado permitirá crear esquema desarrollado, test y guiones de apoyo para el aula."
    )


def _repair_demo_copy(db: Session, projects: list[Project]) -> None:
    for project in projects:
        if "oposiciones" in f"{project.title} {project.educational_level}".lower():
            project.legal_framework = (
                "LOMLOE, convocatoria de oposiciones y normativa autonómica aportada por el docente."
            )
            project.instructions = "Orientar las sugerencias a defensa ante tribunal y programación didáctica."
        else:
            project.legal_framework = "LOMLOE y normativa autonómica aportada por el docente."
            project.instructions = "Mantener cambios localizados y revisión docente obligatoria."
        project.bibliography_notes = "Bibliografía base pendiente de verificación por el profesor."
        for suggestion in db.scalars(select(Suggestion).where(Suggestion.project_id == project.id)):
            if "?" in suggestion.original_fragment:
                suggestion.original_fragment = (
                    "El tema contiene conceptos que deben verificarse con bibliografía científica actual."
                )


def _ensure_opposition_demo_project(db: Session, user: User, projects: list[Project]) -> None:
    has_opposition_project = any(
        "oposiciones" in f"{project.title} {project.educational_level}".lower() for project in projects
    )
    if has_opposition_project:
        return

    project = _create_project(
        db,
        user,
        title="Tema 3. Desarrollo evolutivo de 0 a 6 años",
        area="Educación Infantil",
        level="Oposiciones Educación Infantil",
        status=ProjectStatus.reports_generated,
        legal_framework=(
            "LOMLOE, Real Decreto 95/2022, convocatoria de oposiciones y normativa autonómica "
            "aportada por el docente."
        ),
        bibliography_notes="Temario base de preparación de oposiciones y materiales de academia revisados.",
        instructions="Orientar las sugerencias a defensa ante tribunal y programación didáctica.",
    )
    _add_document_flow(db, project, filename="tema-desarrollo-evolutivo-infantil-demo.docx")
    audit(db, "demo_opposition_project_seeded", user_id=user.id, project_id=project.id)
