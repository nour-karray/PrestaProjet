"""Create trainers and CV storage metadata."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260724_0004"
down_revision: str | None = "20260724_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trainers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("job_title", sa.String(200), nullable=True),
        sa.Column("years_experience", sa.Integer(), nullable=True),
        sa.Column("hourly_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("daily_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("country", sa.String(120), nullable=True),
        sa.Column("linkedin_url", sa.String(300), nullable=True),
        sa.Column("website", sa.String(300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trainers_full_name", "trainers", ["full_name"])
    op.create_index("ix_trainers_email", "trainers", ["email"])
    op.create_table(
        "trainer_cv",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trainer_id", sa.Uuid(), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("extraction_status", sa.String(20), server_default="UPLOADED", nullable=False),
        sa.Column("extraction_model", sa.String(120), nullable=True),
        sa.Column("extraction_duration_ms", sa.Integer(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "extraction_status IN ('UPLOADED','PROCESSING','COMPLETED','FAILED','VALIDATED')",
            name="ck_trainer_cv_extraction_status",
        ),
        sa.ForeignKeyConstraint(["trainer_id"], ["trainers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sha256"),
        sa.UniqueConstraint("storage_filename"),
    )
    op.create_index("ix_trainer_cv_sha256", "trainer_cv", ["sha256"])
    op.create_index("ix_trainer_cv_trainer_id", "trainer_cv", ["trainer_id"])
    op.add_column("training_cases", sa.Column("trainer_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_training_cases_trainer_id",
        "training_cases",
        "trainers",
        ["trainer_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_training_cases_trainer_id", "training_cases", ["trainer_id"])


def downgrade() -> None:
    op.drop_index("ix_training_cases_trainer_id", table_name="training_cases")
    op.drop_constraint("fk_training_cases_trainer_id", "training_cases", type_="foreignkey")
    op.drop_column("training_cases", "trainer_id")
    op.drop_index("ix_trainer_cv_trainer_id", table_name="trainer_cv")
    op.drop_index("ix_trainer_cv_sha256", table_name="trainer_cv")
    op.drop_table("trainer_cv")
    op.drop_index("ix_trainers_email", table_name="trainers")
    op.drop_index("ix_trainers_full_name", table_name="trainers")
    op.drop_table("trainers")
