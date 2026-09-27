"""Create training pricings and add the pricing review status."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260725_0008"
down_revision: str | None = "20260724_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STATUSES = (
    "BROUILLON",
    "DEMANDE_RECUE",
    "RECHERCHE_FORMATEUR",
    "FORMATEUR_PROPOSE",
    "FORMATEUR_ACCEPTE",
    "BESOIN_A_COMPLETER",
    "BESOIN_COMPLETE",
    "PROGRAMME_EN_PREPARATION",
    "PROGRAMME_A_VALIDER",
    "PROGRAMME_VALIDE",
    "TARIFICATION_EN_PREPARATION",
    "TARIFICATION_A_VALIDER",
    "TARIFICATION_VALIDEE",
    "DOCUMENTS_A_GENERER",
    "DOCUMENTS_GENERES",
    "TERMINE",
    "ANNULE",
    "ARCHIVE",
)
OLD_STATUSES = tuple(status for status in STATUSES if status != "TARIFICATION_A_VALIDER")


def status_constraint(statuses: tuple[str, ...]) -> str:
    return f"status IN ({', '.join(repr(status) for status in statuses)})"


def upgrade() -> None:
    op.drop_constraint("ck_training_cases_status", "training_cases", type_="check")
    op.create_check_constraint(
        "ck_training_cases_status",
        "training_cases",
        status_constraint(STATUSES),
    )
    op.create_table(
        "training_pricings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_case_id", sa.Uuid(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="TND", nullable=False),
        sa.Column("trainer_cost", sa.Numeric(15, 3), server_default="0", nullable=False),
        sa.Column("transport_cost", sa.Numeric(15, 3), server_default="0", nullable=False),
        sa.Column("room_cost", sa.Numeric(15, 3), server_default="0", nullable=False),
        sa.Column("meal_cost", sa.Numeric(15, 3), server_default="0", nullable=False),
        sa.Column("other_cost", sa.Numeric(15, 3), server_default="0", nullable=False),
        sa.Column("margin_rate", sa.Numeric(6, 3), server_default="0", nullable=False),
        sa.Column("vat_rate", sa.Numeric(6, 3), server_default="19", nullable=False),
        sa.Column("vat_exemption_reason", sa.Text(), nullable=True),
        sa.Column("vat_legal_reference", sa.String(500), nullable=True),
        sa.Column("trainer_daily_rate_snapshot", sa.Numeric(15, 3), nullable=True),
        sa.Column("trainer_hourly_rate_snapshot", sa.Numeric(15, 3), nullable=True),
        sa.Column("program_day_count_snapshot", sa.Integer(), nullable=False),
        sa.Column("program_duration_minutes_snapshot", sa.Integer(), nullable=False),
        sa.Column("trainer_cost_initialization_method", sa.String(20), nullable=False),
        sa.Column("is_submitted", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_validated", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("currency = 'TND'", name="ck_training_pricings_currency"),
        sa.CheckConstraint(
            "trainer_cost >= 0 AND transport_cost >= 0 AND room_cost >= 0 "
            "AND meal_cost >= 0 AND other_cost >= 0",
            name="ck_training_pricings_costs_non_negative",
        ),
        sa.CheckConstraint(
            "margin_rate >= 0 AND margin_rate <= 100",
            name="ck_training_pricings_margin_rate",
        ),
        sa.CheckConstraint(
            "vat_rate IN (19.000, 13.000, 7.000, 0.000)",
            name="ck_training_pricings_vat_rate",
        ),
        sa.CheckConstraint(
            "vat_rate <> 0 OR vat_exemption_reason IS NOT NULL OR vat_legal_reference IS NOT NULL",
            name="ck_training_pricings_zero_vat_justification",
        ),
        sa.CheckConstraint(
            "program_day_count_snapshot >= 0 AND program_duration_minutes_snapshot >= 0",
            name="ck_training_pricings_program_snapshots_non_negative",
        ),
        sa.CheckConstraint(
            "trainer_cost_initialization_method IN ('DAILY_RATE','HOURLY_RATE','NONE')",
            name="ck_training_pricings_initialization_method",
        ),
        sa.ForeignKeyConstraint(["training_case_id"], ["training_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_training_pricings_training_case_id",
        "training_pricings",
        ["training_case_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_training_pricings_training_case_id", table_name="training_pricings")
    op.drop_table("training_pricings")
    op.execute(
        "UPDATE training_cases SET status = 'TARIFICATION_EN_PREPARATION' "
        "WHERE status = 'TARIFICATION_A_VALIDER'"
    )
    op.drop_constraint("ck_training_cases_status", "training_cases", type_="check")
    op.create_check_constraint(
        "ck_training_cases_status",
        "training_cases",
        status_constraint(OLD_STATUSES),
    )
