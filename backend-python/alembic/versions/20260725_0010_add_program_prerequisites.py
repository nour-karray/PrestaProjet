"""add program prerequisites

Revision ID: 20260725_0010
Revises: 20260725_0009
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260725_0010"
down_revision: str | None = "20260725_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("training_programs", sa.Column("prerequisites", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("training_programs", "prerequisites")
