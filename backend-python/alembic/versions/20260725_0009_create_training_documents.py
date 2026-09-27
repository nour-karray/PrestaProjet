"""create training documents

Revision ID: 20260725_0009
Revises: 20260725_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260725_0009"
down_revision: str | None = "20260725_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "training_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_case_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("internal_filename", sa.String(length=255), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("relative_path", sa.String(length=500), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "snapshot_data",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("generation_error", sa.Text(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "document_type IN ('PROGRAM','QUOTE','AGREEMENT','ATTENDANCE_SHEET','CERTIFICATE')",
            name="ck_training_documents_type",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING','GENERATED','FAILED')",
            name="ck_training_documents_status",
        ),
        sa.ForeignKeyConstraint(["training_case_id"], ["training_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "training_case_id", "document_type", name="uq_training_documents_case_type"
        ),
    )
    op.create_index(
        "ix_training_documents_training_case_id",
        "training_documents",
        ["training_case_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_training_documents_training_case_id", table_name="training_documents")
    op.drop_table("training_documents")
