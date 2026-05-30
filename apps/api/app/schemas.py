from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.db.models import (
    AnalysisRunStatus,
    ProjectStatus,
    ReportType,
    ResourceType,
    SuggestionStatus,
    SuggestionType,
    UserRole,
)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    title: str
    area: str
    educational_level: str
    legal_framework: str
    bibliography_notes: str | None = None
    instructions: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    area: str
    educational_level: str
    legal_framework: str
    bibliography_notes: str | None
    instructions: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    original_filename: str
    file_type: str
    extracted_text: str
    created_at: datetime


class DocumentSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    order_index: int
    content: str
    summary: str | None
    detected_concepts: list[str] | None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    report_type: ReportType
    title: str
    content_markdown: str
    created_at: datetime


class SuggestionCreate(BaseModel):
    section_id: int | None = None
    suggestion_type: SuggestionType
    original_fragment: str
    proposed_change: str
    justification: str
    source_reference: str | None = None
    confidence_level: Literal["low", "medium", "high"]


class SuggestionReview(BaseModel):
    status: Literal["approved", "rejected", "edited", "pending"]
    teacher_notes: str | None = None
    proposed_change: str | None = None


class SuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    section_id: int | None
    suggestion_type: SuggestionType
    original_fragment: str
    proposed_change: str
    justification: str
    source_reference: str | None
    confidence_level: str
    status: SuggestionStatus
    teacher_notes: str | None
    created_at: datetime
    reviewed_at: datetime | None


class ConsolidatedDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    content_markdown: str
    created_at: datetime


class ResourceCreate(BaseModel):
    resource_type: ResourceType


class GeneratedResourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    resource_type: ResourceType
    title: str
    content_markdown: str
    created_at: datetime


class AnalysisRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    run_type: str
    status: AnalysisRunStatus
    model_provider: str | None
    model_name: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class ResearchAnalysisResponse(BaseModel):
    reports: list[ReportRead]
    suggestions: list[SuggestionRead]


class MockAnalysisResponse(ResearchAnalysisResponse):
    """Compatibility response for the old analysis/mock endpoint."""
