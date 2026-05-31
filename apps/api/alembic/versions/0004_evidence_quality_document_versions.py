"""evidence quality and document versions

Revision ID: 0004_evidence_quality_docs
Revises: 0003_merge_reports_files
Create Date: 2026-05-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0004_evidence_quality_docs"
down_revision: Union[str, None] = "0003_merge_reports_files"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("version_index", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("documents", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("documents", sa.Column("extraction_metadata", sa.JSON(), nullable=True))

    with op.batch_alter_table("document_sections") as batch:
        batch.add_column(sa.Column("document_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_document_sections_document_id_documents",
            "documents",
            ["document_id"],
            ["id"],
        )

    op.add_column("analysis_runs", sa.Column("llm_used", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("analysis_runs", sa.Column("web_search_used", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "analysis_runs",
        sa.Column("official_sources_used", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("analysis_runs", sa.Column("quality_score", sa.Integer(), nullable=True))
    op.add_column("analysis_runs", sa.Column("warnings_json", sa.JSON(), nullable=True))

    with op.batch_alter_table("reports") as batch:
        batch.add_column(sa.Column("analysis_run_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_foreign_key("fk_reports_analysis_run_id_analysis_runs", "analysis_runs", ["analysis_run_id"], ["id"])

    with op.batch_alter_table("suggestions") as batch:
        batch.add_column(sa.Column("analysis_run_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("anchor_context", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("anchor_status", sa.String(length=32), nullable=False, server_default="unchecked"))
        batch.add_column(sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.create_foreign_key(
            "fk_suggestions_analysis_run_id_analysis_runs", "analysis_runs", ["analysis_run_id"], ["id"]
        )

    op.add_column(
        "consolidated_documents", sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    op.add_column("generated_resources", sa.Column("is_stale", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("analysis_run_id", sa.Integer(), sa.ForeignKey("analysis_runs.id"), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "suggestion_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("suggestion_id", sa.Integer(), sa.ForeignKey("suggestions.id"), nullable=False),
        sa.Column("evidence_source_id", sa.Integer(), sa.ForeignKey("evidence_sources.id"), nullable=False),
        sa.Column("relevance", sa.String(length=32), nullable=False, server_default="supporting"),
    )


def downgrade() -> None:
    op.drop_table("suggestion_evidence")
    op.drop_table("evidence_sources")
    op.drop_column("generated_resources", "is_stale")
    op.drop_column("consolidated_documents", "is_stale")
    with op.batch_alter_table("suggestions") as batch:
        batch.drop_constraint("fk_suggestions_analysis_run_id_analysis_runs", type_="foreignkey")
        batch.drop_column("is_stale")
        batch.drop_column("anchor_status")
        batch.drop_column("anchor_context")
        batch.drop_column("analysis_run_id")
    with op.batch_alter_table("reports") as batch:
        batch.drop_constraint("fk_reports_analysis_run_id_analysis_runs", type_="foreignkey")
        batch.drop_column("is_stale")
        batch.drop_column("analysis_run_id")
    op.drop_column("analysis_runs", "warnings_json")
    op.drop_column("analysis_runs", "quality_score")
    op.drop_column("analysis_runs", "official_sources_used")
    op.drop_column("analysis_runs", "web_search_used")
    op.drop_column("analysis_runs", "llm_used")
    with op.batch_alter_table("document_sections") as batch:
        batch.drop_constraint("fk_document_sections_document_id_documents", type_="foreignkey")
        batch.drop_column("document_id")
    op.drop_column("documents", "extraction_metadata")
    op.drop_column("documents", "is_active")
    op.drop_column("documents", "version_index")
