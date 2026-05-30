"""add file blob storage

Revision ID: 0002_file_blobs
Revises: 0001_initial
Create Date: 2026-05-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_file_blobs"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "file_blobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_file_blobs_id", "file_blobs", ["id"])
    op.create_index("ix_file_blobs_storage_key", "file_blobs", ["storage_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_file_blobs_storage_key", table_name="file_blobs")
    op.drop_index("ix_file_blobs_id", table_name="file_blobs")
    op.drop_table("file_blobs")
