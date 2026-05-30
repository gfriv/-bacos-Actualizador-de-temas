"""merge report type and file blob branches

Revision ID: 0003_merge_report_types_and_file_blobs
Revises: 0002_expand_report_types, 0002_file_blobs
Create Date: 2026-05-30
"""

from typing import Sequence, Union

revision: str = "0003_merge_report_types_and_file_blobs"
down_revision: Union[str, tuple[str, str], None] = ("0002_expand_report_types", "0002_file_blobs")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
