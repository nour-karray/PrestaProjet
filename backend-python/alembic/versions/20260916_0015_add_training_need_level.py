"""Add the requested training level to client needs."""

import sqlalchemy as sa

from alembic import op

revision = "20260916_0015"
down_revision = "20260915_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("training_needs", sa.Column("level", sa.String(length=20)))
    op.create_check_constraint(
        "ck_training_needs_level",
        "training_needs",
        "level IS NULL OR level IN ('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_training_needs_level", "training_needs", type_="check")
    op.drop_column("training_needs", "level")
