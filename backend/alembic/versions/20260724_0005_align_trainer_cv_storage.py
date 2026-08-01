"""Align trainer CV storage with the Part 2.1 contract."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260724_0005"
down_revision: str | None = "20260724_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.rename_table("trainer_cv", "trainer_cvs")
    op.execute("ALTER INDEX ix_trainer_cv_sha256 RENAME TO ix_trainer_cvs_sha256")
    op.execute("ALTER INDEX ix_trainer_cv_trainer_id RENAME TO ix_trainer_cvs_trainer_id")
    op.add_column("trainer_cvs", sa.Column("extraction_error", sa.Text(), nullable=True))
    op.create_index("ix_trainers_company", "trainers", ["company"])
    op.create_check_constraint(
        "ck_trainers_years_experience_non_negative",
        "trainers",
        "years_experience IS NULL OR years_experience >= 0",
    )
    op.create_check_constraint(
        "ck_trainers_hourly_rate_non_negative",
        "trainers",
        "hourly_rate IS NULL OR hourly_rate >= 0",
    )
    op.create_check_constraint(
        "ck_trainers_daily_rate_non_negative",
        "trainers",
        "daily_rate IS NULL OR daily_rate >= 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_trainers_daily_rate_non_negative", "trainers", type_="check")
    op.drop_constraint("ck_trainers_hourly_rate_non_negative", "trainers", type_="check")
    op.drop_constraint("ck_trainers_years_experience_non_negative", "trainers", type_="check")
    op.drop_index("ix_trainers_company", table_name="trainers")
    op.drop_column("trainer_cvs", "extraction_error")
    op.execute("ALTER INDEX ix_trainer_cvs_trainer_id RENAME TO ix_trainer_cv_trainer_id")
    op.execute("ALTER INDEX ix_trainer_cvs_sha256 RENAME TO ix_trainer_cv_sha256")
    op.rename_table("trainer_cvs", "trainer_cv")
