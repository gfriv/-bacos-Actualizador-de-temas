"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-29
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("admin", "teacher", "reviewer", name="userrole"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("area", sa.String(length=255), nullable=False),
        sa.Column("educational_level", sa.String(length=255), nullable=False),
        sa.Column("legal_framework", sa.Text(), nullable=False),
        sa.Column("bibliography_notes", sa.Text()),
        sa.Column("instructions", sa.Text()),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "document_uploaded",
                "processing",
                "reports_generated",
                "under_review",
                "consolidated",
                "resources_generated",
                "error",
                name="projectstatus",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_type", sa.String(length=16), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "document_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("detected_concepts", sa.JSON()),
    )

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("run_type", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "completed", "failed", name="analysisrunstatus"),
            nullable=False,
        ),
        sa.Column("model_provider", sa.String(length=64)),
        sa.Column("model_name", sa.String(length=128)),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_message", sa.Text()),
    )

    op.create_table(
        "suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("section_id", sa.Integer(), sa.ForeignKey("document_sections.id")),
        sa.Column(
            "suggestion_type",
            sa.Enum(
                "scientific_update",
                "legal_curricular",
                "bibliographic_update",
                "didactic_improvement",
                name="suggestiontype",
            ),
            nullable=False,
        ),
        sa.Column("original_fragment", sa.Text(), nullable=False),
        sa.Column("proposed_change", sa.Text(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.Text()),
        sa.Column("confidence_level", sa.String(length=16), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", "edited", name="suggestionstatus"),
            nullable=False,
        ),
        sa.Column("teacher_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "report_type",
            sa.Enum(
                "initial_diagnosis",
                "scientific_update",
                "curriculum_mapping",
                "source_validation",
                "change_proposal",
                "technical_traceability",
                name="reporttype",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "consolidated_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("docx_path", sa.String(length=512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "generated_resources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column(
            "resource_type",
            sa.Enum(
                "esquema_desarrollado",
                "test_autoevaluacion",
                "presentacion_clase",
                "guion_audio",
                "guion_video",
                name="resourcetype",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id")),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in [
        "audit_logs",
        "generated_resources",
        "consolidated_documents",
        "reports",
        "suggestions",
        "analysis_runs",
        "document_sections",
        "documents",
        "projects",
        "users",
    ]:
        op.drop_table(table)
