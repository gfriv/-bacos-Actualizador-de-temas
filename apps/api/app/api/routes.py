from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_ai_provider_config, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import (
    ConsolidatedDocument,
    Document,
    DocumentSection,
    GeneratedResource,
    Project,
    ProjectStatus,
    Report,
    Suggestion,
    SuggestionStatus,
    User,
    UserRole,
)
from app.db.session import get_db
from app.document_processing.docx_extractor import extract_docx_text
from app.document_processing.docx_writer import write_markdown_docx
from app.document_processing.pdf_extractor import extract_pdf_text
from app.document_processing.section_splitter import split_sections
from app.llm.model_router import ModelRouter
from app.llm.providers.ollama_provider import OllamaProvider
from app.llm.providers.registry import PROVIDER_DESCRIPTORS
from app.llm.runtime_policy import assert_provider_runtime_allowed, safe_provider_error
from app.llm.schemas import (
    AIProviderConfig,
    AIProviderDescriptor,
    GenerateStructuredRequest,
    GenerateTextRequest,
    GenerateTextResult,
    ModelListRequest,
    OllamaPullRequest,
    ProviderValidationRequest,
    ProviderValidationResult,
)
from app.schemas import (
    ConsolidatedDocumentRead,
    DocumentRead,
    DocumentSectionRead,
    GeneratedResourceRead,
    LoginRequest,
    MockAnalysisResponse,
    ProjectCreate,
    ProjectRead,
    ReportRead,
    ResearchAnalysisResponse,
    ResourceCreate,
    SuggestionCreate,
    SuggestionRead,
    SuggestionReview,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.services.audit import audit
from app.services.consolidation import build_consolidated_markdown
from app.services.demo_seed import get_or_create_demo_user
from app.services.file_storage import (
    managed_file_response,
    save_managed_file,
    uses_database_storage,
)
from app.services.research_analysis import build_research_analysis
from app.services.resources import RESOURCE_TITLES

router = APIRouter()

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MEDIA_TYPE = "application/pdf"
MARKDOWN_MEDIA_TYPE = "text/markdown; charset=utf-8"


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ai/providers", response_model=list[AIProviderDescriptor])
def list_ai_providers() -> list[AIProviderDescriptor]:
    return PROVIDER_DESCRIPTORS


@router.post("/ai/providers/validate", response_model=ProviderValidationResult)
async def validate_ai_provider(
    payload: ProviderValidationRequest,
    current_user: User = Depends(get_current_user),
) -> ProviderValidationResult:
    _require_roles(current_user, {UserRole.admin, UserRole.teacher, UserRole.reviewer})
    try:
        return await ModelRouter(provider_config=payload.config).validate_connection()
    except Exception as exc:
        return ProviderValidationResult(
            ok=False,
            provider_id=payload.config.provider_id,
            message=safe_provider_error(exc),
            models=[],
        )


@router.post("/ai/providers/models")
async def list_ai_models(
    payload: ModelListRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, list[dict[str, object]]]:
    _require_roles(current_user, {UserRole.admin, UserRole.teacher, UserRole.reviewer})
    try:
        models = await ModelRouter(provider_config=payload.config).list_models()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=safe_provider_error(exc)) from exc
    return {"models": [model.model_dump() for model in models]}


@router.post("/ai/generate-text", response_model=GenerateTextResult)
async def generate_ai_text(
    payload: GenerateTextRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateTextResult:
    _require_roles(current_user, {UserRole.admin, UserRole.teacher, UserRole.reviewer})
    try:
        router = ModelRouter(provider_config=payload.config)
        text = await router.generate_text(
            payload.input.prompt,
            payload.input.system_prompt,
            payload.input.generation_config,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=safe_provider_error(exc)) from exc
    return GenerateTextResult(text=text, provider_id=payload.config.provider_id, model=router.model_name)


@router.post("/ai/generate-structured")
async def generate_ai_structured(
    payload: GenerateStructuredRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    _require_roles(current_user, {UserRole.admin, UserRole.teacher, UserRole.reviewer})
    prompt = (
        f"{payload.input.prompt}\n\n"
        "Devuelve exclusivamente un objeto JSON valido. "
        "No incluyas explicaciones, markdown ni texto fuera del JSON."
    )
    try:
        text = await ModelRouter(provider_config=payload.config).generate_text(
            prompt,
            payload.input.system_prompt,
            payload.input.generation_config,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=safe_provider_error(exc)) from exc
    return {"raw": text}


@router.post("/ai/ollama/pull")
async def pull_ollama_model(
    payload: OllamaPullRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Confirma explÃ­citamente la descarga del modelo.")
    if not settings.ollama_pull_enabled:
        raise HTTPException(
            status_code=403,
            detail="La descarga automÃ¡tica de modelos Ollama estÃ¡ deshabilitada. Activa OLLAMA_PULL_ENABLED=true en entorno local.",
        )
    try:
        assert_provider_runtime_allowed(
            AIProviderConfig(provider_id="ollama", mode="local", base_url=settings.ollama_base_url)
        )
        return await OllamaProvider(base_url=settings.ollama_base_url).pull_model(payload.model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=safe_provider_error(exc)) from exc


@router.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="El email ya está registrado.")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=UserRole.teacher,
    )
    db.add(user)
    db.flush()
    audit(db, "user_registered", user_id=user.id)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales no válidas.")
    audit(db, "login", user_id=user.id)
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/auth/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.demo_access_enabled:
        raise HTTPException(status_code=404, detail="El acceso demo no está habilitado.")
    user = get_or_create_demo_user(db)
    audit(db, "demo_login", user_id=user.id)
    db.commit()
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/projects", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    project = Project(owner_id=current_user.id, status=ProjectStatus.draft, **payload.model_dump())
    db.add(project)
    db.flush()
    audit(db, "project_created", user_id=current_user.id, project_id=project.id)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    if current_user.role.value == "admin":
        return list(db.scalars(select(Project).order_by(Project.updated_at.desc())))
    return list(
        db.scalars(
            select(Project).where(Project.owner_id == current_user.id).order_by(Project.updated_at.desc())
        )
    )


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return _get_project_for_user(db, project_id, current_user)


@router.get("/projects/{project_id}/documents", response_model=list[DocumentRead])
def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    project = _get_project_for_user(db, project_id, current_user)
    return list(
        db.scalars(select(Document).where(Document.project_id == project.id).order_by(Document.created_at.desc()))
    )


@router.get("/documents/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    _get_project_for_user(db, document.project_id, current_user)
    media_type = DOCX_MEDIA_TYPE if document.file_type == "docx" else PDF_MEDIA_TYPE
    return managed_file_response(
        db,
        document.file_path,
        settings.upload_dir,
        document.original_filename,
        media_type,
    )


@router.get("/projects/{project_id}/sections", response_model=list[DocumentSectionRead])
def list_sections(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentSection]:
    project = _get_project_for_user(db, project_id, current_user)
    return list(
        db.scalars(
            select(DocumentSection)
            .where(DocumentSection.project_id == project.id)
            .order_by(DocumentSection.order_index.asc())
        )
    )


@router.post("/projects/{project_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    project = _get_project_for_user(db, project_id, current_user)
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    original_filename = Path(file.filename or "documento").name
    suffix = Path(original_filename).suffix.lower()
    if suffix not in {".docx", ".pdf"}:
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos DOCX o PDF.")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo supera el tamaño máximo permitido.")

    try:
        if uses_database_storage():
            with TemporaryDirectory() as tmp_dir:
                target = Path(tmp_dir) / f"upload{suffix}"
                target.write_bytes(content)
                extracted_text = extract_docx_text(target) if suffix == ".docx" else extract_pdf_text(target)
        else:
            upload_dir = Path(settings.upload_dir).resolve()
            upload_dir.mkdir(parents=True, exist_ok=True)
            target = upload_dir / f"{uuid4().hex}{suffix}"
            target.write_bytes(content)
            extracted_text = extract_docx_text(target) if suffix == ".docx" else extract_pdf_text(target)
    except ValueError as exc:
        if "target" in locals():
            target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        if "target" in locals():
            target.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail="El archivo no parece un DOCX/PDF vÃ¡lido o estÃ¡ daÃ±ado.",
        ) from exc

    file_path = (
        save_managed_file(
            db,
            content,
            root_dir=settings.upload_dir,
            filename=original_filename,
            content_type=DOCX_MEDIA_TYPE if suffix == ".docx" else PDF_MEDIA_TYPE,
            namespace="uploads",
        )
        if uses_database_storage()
        else str(target)
    )

    document = Document(
        project_id=project.id,
        original_filename=original_filename,
        file_path=file_path,
        file_type=suffix.removeprefix("."),
        extracted_text=extracted_text,
    )
    db.add(document)
    db.flush()

    for parsed in split_sections(extracted_text):
        db.add(
            DocumentSection(
                project_id=project.id,
                title=parsed.title,
                order_index=parsed.order_index,
                content=parsed.content,
                summary=parsed.summary,
                detected_concepts=parsed.detected_concepts,
            )
        )

    project.status = ProjectStatus.document_uploaded
    audit(db, "document_uploaded", user_id=current_user.id, project_id=project.id, filename=document.original_filename)
    db.commit()
    db.refresh(document)
    return document


@router.post("/projects/{project_id}/analysis/research", response_model=ResearchAnalysisResponse)
async def run_research_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_config: AIProviderConfig | None = Depends(get_ai_provider_config),
) -> dict[str, list[Report | Suggestion]]:
    return await _run_research_analysis(project_id, db, current_user, ai_config)


@router.post("/projects/{project_id}/analysis/mock", response_model=MockAnalysisResponse)
async def run_legacy_mock_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_config: AIProviderConfig | None = Depends(get_ai_provider_config),
) -> dict[str, list[Report | Suggestion]]:
    return await _run_research_analysis(project_id, db, current_user, ai_config)


async def _run_research_analysis(
    project_id: int,
    db: Session,
    current_user: User,
    ai_config: AIProviderConfig | None = None,
) -> dict[str, list[Report | Suggestion]]:
    project = _get_project_for_user(db, project_id, current_user)
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    sections = list(
        db.scalars(
            select(DocumentSection)
            .where(DocumentSection.project_id == project.id)
            .order_by(DocumentSection.order_index.asc())
        )
    )
    if not sections:
        raise HTTPException(status_code=400, detail="Sube un documento antes de generar informes.")

    analysis = await build_research_analysis(project, sections, provider_config=ai_config)
    db.add_all([*analysis.reports, *analysis.suggestions])
    project.status = ProjectStatus.under_review
    audit(
        db,
        "research_analysis_generated",
        user_id=current_user.id,
        project_id=project.id,
        queries=len(analysis.queries),
        evidence=len(analysis.evidence),
        web_search_provider=settings.web_search_provider,
    )
    db.commit()
    for item in [*analysis.reports, *analysis.suggestions]:
        db.refresh(item)
    return {
        "reports": analysis.reports,
        "suggestions": analysis.suggestions,
    }


@router.post("/projects/{project_id}/suggestions", response_model=SuggestionRead, status_code=status.HTTP_201_CREATED)
def create_suggestion(
    project_id: int,
    payload: SuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Suggestion:
    project = _get_project_for_user(db, project_id, current_user)
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    suggestion = Suggestion(project_id=project.id, status=SuggestionStatus.pending, **payload.model_dump())
    db.add(suggestion)
    db.flush()
    audit(db, "suggestion_created", user_id=current_user.id, project_id=project.id, suggestion_id=suggestion.id)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.get("/projects/{project_id}/suggestions", response_model=list[SuggestionRead])
def list_suggestions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Suggestion]:
    project = _get_project_for_user(db, project_id, current_user)
    return list(
        db.scalars(select(Suggestion).where(Suggestion.project_id == project.id).order_by(Suggestion.created_at.asc()))
    )


@router.patch("/suggestions/{suggestion_id}", response_model=SuggestionRead)
def review_suggestion(
    suggestion_id: int,
    payload: SuggestionReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Suggestion:
    suggestion = db.get(Suggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Sugerencia no encontrada.")
    _get_project_for_user(db, suggestion.project_id, current_user)
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    suggestion.status = SuggestionStatus(payload.status)
    suggestion.teacher_notes = payload.teacher_notes
    if payload.proposed_change:
        suggestion.proposed_change = payload.proposed_change
        suggestion.status = SuggestionStatus.edited
    suggestion.reviewed_at = datetime.now(UTC)
    audit(
        db,
        "suggestion_reviewed",
        user_id=current_user.id,
        project_id=suggestion.project_id,
        suggestion_id=suggestion.id,
        status=suggestion.status.value,
    )
    db.commit()
    db.refresh(suggestion)
    return suggestion


@router.get("/projects/{project_id}/reports", response_model=list[ReportRead])
def list_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Report]:
    project = _get_project_for_user(db, project_id, current_user)
    return list(db.scalars(select(Report).where(Report.project_id == project.id).order_by(Report.created_at.asc())))


@router.post("/projects/{project_id}/consolidate", response_model=ConsolidatedDocumentRead)
def consolidate_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsolidatedDocument:
    project = _get_project_for_user(db, project_id, current_user)
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    sections = list(db.scalars(select(DocumentSection).where(DocumentSection.project_id == project.id)))
    suggestions = list(db.scalars(select(Suggestion).where(Suggestion.project_id == project.id)))
    approved_count = sum(
        1 for suggestion in suggestions if suggestion.status in {SuggestionStatus.approved, SuggestionStatus.edited}
    )
    if approved_count == 0:
        raise HTTPException(status_code=400, detail="No hay sugerencias aprobadas o editadas para consolidar.")

    markdown = build_consolidated_markdown(sections, suggestions)
    docx_filename = f"project-{project.id}-consolidated.docx"
    if uses_database_storage():
        with TemporaryDirectory() as tmp_dir:
            docx_path = Path(tmp_dir) / docx_filename
            write_markdown_docx(markdown, docx_path)
            stored_docx_path = save_managed_file(
                db,
                docx_path.read_bytes(),
                root_dir=settings.generated_dir,
                filename=docx_filename,
                content_type=DOCX_MEDIA_TYPE,
                namespace="generated",
            )
    else:
        generated_dir = Path(settings.generated_dir).resolve()
        docx_path = generated_dir / docx_filename
        write_markdown_docx(markdown, docx_path)
        stored_docx_path = str(docx_path)
    consolidated = ConsolidatedDocument(project_id=project.id, content_markdown=markdown, docx_path=stored_docx_path)
    db.add(consolidated)
    project.status = ProjectStatus.consolidated
    audit(db, "document_consolidated", user_id=current_user.id, project_id=project.id, approved_count=approved_count)
    db.commit()
    db.refresh(consolidated)
    return consolidated


@router.get("/projects/{project_id}/consolidated", response_model=ConsolidatedDocumentRead)
def get_consolidated_document(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConsolidatedDocument:
    project = _get_project_for_user(db, project_id, current_user)
    consolidated = db.scalar(
        select(ConsolidatedDocument)
        .where(ConsolidatedDocument.project_id == project.id)
        .order_by(ConsolidatedDocument.created_at.desc())
    )
    if consolidated is None:
        raise HTTPException(status_code=404, detail="Documento consolidado no encontrado.")
    return consolidated


@router.get("/projects/{project_id}/consolidated/download")
def download_consolidated_document(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project = _get_project_for_user(db, project_id, current_user)
    consolidated = db.scalar(
        select(ConsolidatedDocument)
        .where(ConsolidatedDocument.project_id == project.id)
        .order_by(ConsolidatedDocument.created_at.desc())
    )
    if consolidated is None or consolidated.docx_path is None:
        raise HTTPException(status_code=404, detail="Documento consolidado no encontrado.")
    return managed_file_response(
        db,
        consolidated.docx_path,
        settings.generated_dir,
        f"proyecto-{project.id}-consolidado.docx",
        DOCX_MEDIA_TYPE,
    )


@router.post("/projects/{project_id}/resources", response_model=GeneratedResourceRead)
async def generate_resource(
    project_id: int,
    payload: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    ai_config: AIProviderConfig | None = Depends(get_ai_provider_config),
) -> GeneratedResource:
    project = _get_project_for_user(db, project_id, current_user)
    _require_roles(current_user, {UserRole.admin, UserRole.teacher})
    consolidated = db.scalar(
        select(ConsolidatedDocument)
        .where(ConsolidatedDocument.project_id == project.id)
        .order_by(ConsolidatedDocument.created_at.desc())
    )
    if consolidated is None:
        raise HTTPException(
            status_code=400,
            detail="Genera el documento consolidado antes de crear recursos didácticos.",
        )
    document_text = consolidated.content_markdown
    content = await ModelRouter(provider_config=ai_config).generate_document_resource(document_text, payload.resource_type.value)
    resource = GeneratedResource(
        project_id=project.id,
        resource_type=payload.resource_type,
        title=RESOURCE_TITLES[payload.resource_type],
        content_markdown=content,
    )
    db.add(resource)
    db.flush()
    resource_filename = f"project-{project.id}-resource-{resource.id}-{payload.resource_type.value}.md"
    resource.file_path = save_managed_file(
        db,
        content.encode("utf-8"),
        root_dir=settings.generated_dir,
        filename=resource_filename,
        content_type=MARKDOWN_MEDIA_TYPE,
        namespace="generated",
    )
    project.status = ProjectStatus.resources_generated
    audit(db, "resource_generated", user_id=current_user.id, project_id=project.id, resource_type=payload.resource_type.value)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("/projects/{project_id}/resources", response_model=list[GeneratedResourceRead])
def list_resources(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GeneratedResource]:
    project = _get_project_for_user(db, project_id, current_user)
    return list(
        db.scalars(
            select(GeneratedResource)
            .where(GeneratedResource.project_id == project.id)
            .order_by(GeneratedResource.created_at.desc())
        )
    )


@router.get("/resources/{resource_id}/download")
def download_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    resource = db.get(GeneratedResource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")
    _get_project_for_user(db, resource.project_id, current_user)
    if resource.file_path is None:
        raise HTTPException(status_code=404, detail="El recurso no tiene archivo descargable.")
    return managed_file_response(
        db,
        resource.file_path,
        settings.generated_dir,
        f"{resource.title}.md",
        MARKDOWN_MEDIA_TYPE,
    )


def _managed_file_response(
    stored_path: str,
    allowed_root: str,
    download_name: str,
    media_type: str,
) -> FileResponse:
    root = Path(allowed_root).resolve()
    path = Path(stored_path)
    resolved = path.resolve() if not path.is_absolute() else path.resolve()
    if not resolved.is_relative_to(root):
        raise HTTPException(status_code=403, detail="Archivo fuera del almacÃ©n permitido.")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return FileResponse(resolved, media_type=media_type, filename=download_name)


def _require_roles(user: User, allowed_roles: set[UserRole]) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Tu rol no permite realizar esta acciÃ³n.")


def _get_project_for_user(db: Session, project_id: int, user: User) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    if user.role.value != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para acceder a este proyecto.")
    return project
