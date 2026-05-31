import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    reviewer = "reviewer"


class ProjectStatus(str, enum.Enum):
    draft = "draft"
    document_uploaded = "document_uploaded"
    processing = "processing"
    reports_generated = "reports_generated"
    under_review = "under_review"
    consolidated = "consolidated"
    resources_generated = "resources_generated"
    error = "error"


class AnalysisRunStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class SuggestionStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    edited = "edited"


class SuggestionType(str, enum.Enum):
    scientific_update = "scientific_update"
    legal_curricular = "legal_curricular"
    bibliographic_update = "bibliographic_update"
    didactic_improvement = "didactic_improvement"


class ReportType(str, enum.Enum):
    initial_diagnosis = "initial_diagnosis"
    scientific_update = "scientific_update"
    curriculum_mapping = "curriculum_mapping"
    source_validation = "source_validation"
    change_proposal = "change_proposal"
    technical_traceability = "technical_traceability"


class ResourceType(str, enum.Enum):
    esquema_desarrollado = "esquema_desarrollado"
    test_autoevaluacion = "test_autoevaluacion"
    presentacion_clase = "presentacion_clase"
    guion_audio = "guion_audio"
    guion_video = "guion_video"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.teacher, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    projects: Mapped[list["Project"]] = relationship(back_populates="owner")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    area: Mapped[str] = mapped_column(String(255), nullable=False)
    educational_level: Mapped[str] = mapped_column(String(255), nullable=False)
    legal_framework: Mapped[str] = mapped_column(Text, nullable=False)
    bibliography_notes: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.draft, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="projects")
    documents: Mapped[list["Document"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    sections: Mapped[list["DocumentSection"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    suggestions: Mapped[list["Suggestion"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    version_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extraction_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="documents")
    sections: Mapped[list["DocumentSection"]] = relationship(back_populates="document")


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    detected_concepts: Mapped[list[str] | None] = mapped_column(JSON)

    project: Mapped[Project] = relationship(back_populates="sections")
    document: Mapped[Document | None] = relationship(back_populates="sections")
    suggestions: Mapped[list["Suggestion"]] = relationship(back_populates="section")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    run_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[AnalysisRunStatus] = mapped_column(
        Enum(AnalysisRunStatus), default=AnalysisRunStatus.queued, nullable=False
    )
    model_provider: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(128))
    llm_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    web_search_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    official_sources_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_score: Mapped[int | None] = mapped_column(Integer)
    warnings_json: Mapped[list[str] | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"))
    section_id: Mapped[int | None] = mapped_column(ForeignKey("document_sections.id"))
    suggestion_type: Mapped[SuggestionType] = mapped_column(Enum(SuggestionType), nullable=False)
    original_fragment: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_change: Mapped[str] = mapped_column(Text, nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    source_reference: Mapped[str | None] = mapped_column(Text)
    anchor_context: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    anchor_status: Mapped[str] = mapped_column(String(32), default="unchecked", nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[SuggestionStatus] = mapped_column(
        Enum(SuggestionStatus), default=SuggestionStatus.pending, nullable=False
    )
    teacher_notes: Mapped[str | None] = mapped_column(Text)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="suggestions")
    section: Mapped[DocumentSection | None] = relationship(back_populates="suggestions")
    evidence_links: Mapped[list["SuggestionEvidence"]] = relationship(
        back_populates="suggestion", cascade="all, delete-orphan"
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"))
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="reports")


class ConsolidatedDocument(Base):
    __tablename__ = "consolidated_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    docx_path: Mapped[str | None] = mapped_column(String(512))
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GeneratedResource(Base):
    __tablename__ = "generated_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(Enum(ResourceType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(512))
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    analysis_run_id: Mapped[int | None] = mapped_column(ForeignKey("analysis_runs.id"))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    suggestion_links: Mapped[list["SuggestionEvidence"]] = relationship(
        back_populates="evidence_source", cascade="all, delete-orphan"
    )


class SuggestionEvidence(Base):
    __tablename__ = "suggestion_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    suggestion_id: Mapped[int] = mapped_column(ForeignKey("suggestions.id"), nullable=False)
    evidence_source_id: Mapped[int] = mapped_column(ForeignKey("evidence_sources.id"), nullable=False)
    relevance: Mapped[str] = mapped_column(String(32), default="supporting", nullable=False)

    suggestion: Mapped[Suggestion] = relationship(back_populates="evidence_links")
    evidence_source: Mapped[EvidenceSource] = relationship(back_populates="suggestion_links")


class FileBlob(Base):
    __tablename__ = "file_blobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
