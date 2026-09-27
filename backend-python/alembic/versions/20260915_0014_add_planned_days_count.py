"""Add the user-planned number of training days."""

import sqlalchemy as sa

from alembic import op

revision = "20260915_0014"
down_revision = "20260731_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("training_needs", sa.Column("planned_days_count", sa.Integer()))
    op.create_check_constraint(
        "ck_training_needs_planned_days_count_positive",
        "training_needs",
        "planned_days_count IS NULL OR planned_days_count > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_training_needs_planned_days_count_positive",
        "training_needs",
        type_="check",
    )
    op.drop_column("training_needs", "planned_days_count")
