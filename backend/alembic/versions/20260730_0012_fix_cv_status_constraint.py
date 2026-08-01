"""Allow every resilient CV pipeline status on PostgreSQL."""

from alembic import op

revision = "20260730_0012"
down_revision = "20260729_0011"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "ck_trainer_cv_extraction_status"
NEW_STATUSES = (
    "UPLOADED",
    "TEXT_EXTRACTED",
    "OCR_REQUIRED",
    "OCR_COMPLETED",
    "AI_ANALYSIS_PENDING",
    "AI_ANALYSIS_COMPLETED",
    "REVIEW_REQUIRED",
    "VALIDATED",
    "FAILED",
)


def _status_check(statuses: tuple[str, ...]) -> str:
    values = ",".join(f"'{status}'" for status in statuses)
    return f"extraction_status IN ({values})"


def upgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "trainer_cvs", type_="check")
    op.create_check_constraint(
        CONSTRAINT_NAME,
        "trainer_cvs",
        _status_check(NEW_STATUSES),
    )


def downgrade() -> None:
    op.execute(
        "UPDATE trainer_cvs SET extraction_status = 'FAILED' "
        "WHERE extraction_status NOT IN "
        "('UPLOADED','PROCESSING','COMPLETED','FAILED','VALIDATED')"
    )
    op.drop_constraint(CONSTRAINT_NAME, "trainer_cvs", type_="check")
    op.create_check_constraint(
        CONSTRAINT_NAME,
        "trainer_cvs",
        _status_check(("UPLOADED", "PROCESSING", "COMPLETED", "FAILED", "VALIDATED")),
    )
