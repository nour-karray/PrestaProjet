"""Add resilient CV pipeline states and error codes."""

import sqlalchemy as sa

from alembic import op

revision = "20260729_0011"
down_revision = "20260725_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "trainer_cvs", "extraction_status", existing_type=sa.String(20),
        type_=sa.String(32), existing_nullable=False,
    )
    op.add_column("trainer_cvs", sa.Column("extraction_error_code", sa.String(64)))
    op.execute(
        "UPDATE trainer_cvs SET extraction_status='AI_ANALYSIS_PENDING' "
        "WHERE extraction_status='PROCESSING'"
    )
    op.execute(
        "UPDATE trainer_cvs SET extraction_status='REVIEW_REQUIRED' "
        "WHERE extraction_status='COMPLETED'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE trainer_cvs SET extraction_status='PROCESSING' "
        "WHERE extraction_status IN ('TEXT_EXTRACTED','OCR_REQUIRED','OCR_COMPLETED',"
        "'AI_ANALYSIS_PENDING')"
    )
    op.execute(
        "UPDATE trainer_cvs SET extraction_status='COMPLETED' "
        "WHERE extraction_status IN ('AI_ANALYSIS_COMPLETED','REVIEW_REQUIRED')"
    )
    op.drop_column("trainer_cvs", "extraction_error_code")
    op.alter_column(
        "trainer_cvs", "extraction_status", existing_type=sa.String(32),
        type_=sa.String(20), existing_nullable=False,
    )
