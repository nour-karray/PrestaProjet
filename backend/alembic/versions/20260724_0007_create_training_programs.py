"""Create structured training programs."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260724_0007"
down_revision: str | None = "20260724_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "training_programs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_case_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("general_objectives", sa.Text(), nullable=True),
        sa.Column("evaluation_method", sa.Text(), nullable=True),
        sa.Column("is_submitted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_validated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_reason", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["training_case_id"], ["training_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_training_programs_training_case_id",
        "training_programs",
        ["training_case_id"],
        unique=True,
    )
    op.create_table(
        "training_program_days",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_program_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
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
        sa.CheckConstraint("position > 0", name="ck_training_program_days_position_positive"),
        sa.ForeignKeyConstraint(
            ["training_program_id"], ["training_programs.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "training_program_id", "position", name="uq_training_program_days_program_position"
        ),
    )
    op.create_index(
        "ix_training_program_days_training_program_id",
        "training_program_days",
        ["training_program_id"],
    )
    op.create_table(
        "training_program_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_program_day_id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("item_type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("theory_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("practice_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
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
            "item_type IN ('MODULE','SUBMODULE')", name="ck_training_program_items_type"
        ),
        sa.CheckConstraint(
            "theory_minutes >= 0 AND practice_minutes >= 0",
            name="ck_training_program_items_durations_non_negative",
        ),
        sa.CheckConstraint("position > 0", name="ck_training_program_items_position_positive"),
        sa.CheckConstraint(
            """
            (item_type = 'MODULE' AND parent_id IS NULL)
            OR (item_type = 'SUBMODULE' AND parent_id IS NOT NULL)
            """,
            name="ck_training_program_items_parent_by_type",
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["training_program_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["training_program_day_id"], ["training_program_days.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_training_program_items_day_id", "training_program_items", ["training_program_day_id"]
    )
    op.create_index("ix_training_program_items_parent_id", "training_program_items", ["parent_id"])
    op.create_index(
        "uq_training_program_modules_day_position",
        "training_program_items",
        ["training_program_day_id", "position"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NULL"),
    )
    op.create_index(
        "uq_training_program_submodules_parent_position",
        "training_program_items",
        ["parent_id", "position"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NOT NULL"),
    )
    op.create_table(
        "training_program_item_methods",
        sa.Column("training_program_item_id", sa.Uuid(), nullable=False),
        sa.Column("method", sa.String(40), nullable=False),
        sa.CheckConstraint(
            """
            method IN (
                'EXPOSE', 'DEMONSTRATION', 'EXERCICE_PRATIQUE',
                'ETUDE_DE_CAS', 'MISE_EN_SITUATION',
                'ECHANGE_COLLECTIF', 'EVALUATION'
            )
            """,
            name="ck_training_program_item_methods_method",
        ),
        sa.ForeignKeyConstraint(
            ["training_program_item_id"], ["training_program_items.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("training_program_item_id", "method"),
    )


def downgrade() -> None:
    op.drop_table("training_program_item_methods")
    op.drop_index(
        "uq_training_program_submodules_parent_position", table_name="training_program_items"
    )
    op.drop_index("uq_training_program_modules_day_position", table_name="training_program_items")
    op.drop_index("ix_training_program_items_parent_id", table_name="training_program_items")
    op.drop_index("ix_training_program_items_day_id", table_name="training_program_items")
    op.drop_table("training_program_items")
    op.drop_index(
        "ix_training_program_days_training_program_id", table_name="training_program_days"
    )
    op.drop_table("training_program_days")
    op.drop_index("ix_training_programs_training_case_id", table_name="training_programs")
    op.drop_table("training_programs")
