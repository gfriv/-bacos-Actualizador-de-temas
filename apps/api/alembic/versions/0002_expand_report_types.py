"""expand report types

Revision ID: 0002_expand_report_types
Revises: 0001_initial
Create Date: 2026-05-30
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_expand_report_types"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_REPORT_TYPES = (
    "initial_diagnosis",
    "source_validation",
    "change_proposal",
    "technical_traceability",
)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            for report_type in NEW_REPORT_TYPES:
                op.execute(sa.text(f"ALTER TYPE reporttype ADD VALUE IF NOT EXISTS '{report_type}'"))


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without recreating the type.
    pass
