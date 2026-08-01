"""Create structured client training needs."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260724_0006"
down_revision: str | None = "20260724_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "training_needs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_case_id", sa.Uuid(), nullable=False),
        sa.Column("target_audience", sa.String(500), nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("participant_count", sa.Integer(), nullable=True),
        sa.Column("delivery_mode", sa.String(20), nullable=True),
        sa.Column("duration_hours", sa.Numeric(8, 2), nullable=True),
        sa.Column("objectives", sa.Text(), nullable=True),
        sa.Column("desired_start_date", sa.Date(), nullable=True),
        sa.Column("desired_end_date", sa.Date(), nullable=True),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("is_validated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "participant_count IS NULL OR participant_count > 0",
            name="ck_training_needs_participant_count_positive",
        ),
        sa.CheckConstraint(
            "duration_hours IS NULL OR duration_hours > 0",
            name="ck_training_needs_duration_hours_positive",
        ),
        sa.CheckConstraint(
            "delivery_mode IS NULL OR delivery_mode IN ('PRESENTIEL','DISTANCIEL','HYBRIDE')",
            name="ck_training_needs_delivery_mode",
        ),
        sa.CheckConstraint(
            "desired_end_date IS NULL OR desired_start_date IS NULL "
            "OR desired_end_date >= desired_start_date",
            name="ck_training_needs_date_range",
        ),
        sa.ForeignKeyConstraint(["training_case_id"], ["training_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_training_needs_training_case_id",
        "training_needs",
        ["training_case_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_training_needs_training_case_id", table_name="training_needs")
    op.drop_table("training_needs")
