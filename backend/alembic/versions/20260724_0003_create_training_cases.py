"""Create training cases, annual counters and activity logs."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260724_0003"
down_revision: str | None = "20260724_0002"
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
    "TARIFICATION_VALIDEE",
    "DOCUMENTS_A_GENERER",
    "DOCUMENTS_GENERES",
    "TERMINE",
    "ANNULE",
    "ARCHIVE",
)


def upgrade() -> None:
    op.create_table(
        "training_case_counters",
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("year"),
    )
    op.create_table(
        "training_cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reference", sa.String(length=20), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("primary_contact_id", sa.Uuid(), nullable=True),
        sa.Column("theme", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=40),
            server_default="BROUILLON",
            nullable=False,
        ),
        sa.Column("desired_start_date", sa.Date(), nullable=True),
        sa.Column("desired_end_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
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
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.CheckConstraint(
            f"status IN ({', '.join(repr(status) for status in STATUSES)})",
            name="ck_training_cases_status",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(
            ["primary_contact_id"],
            ["company_contacts.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["administrators.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reference"),
    )
    op.create_index("ix_training_cases_company_id", "training_cases", ["company_id"])
    op.create_index("ix_training_cases_created_at", "training_cases", ["created_at"])
    op.create_index("ix_training_cases_is_archived", "training_cases", ["is_archived"])
    op.create_index("ix_training_cases_status", "training_cases", ["status"])
    op.create_index("ix_training_cases_theme", "training_cases", ["theme"])
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("administrator_id", sa.Uuid(), nullable=True),
        sa.Column("training_case_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["administrator_id"], ["administrators.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["training_case_id"], ["training_cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_activity_logs_training_case_id",
        "activity_logs",
        ["training_case_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_training_case_id", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_index("ix_training_cases_theme", table_name="training_cases")
    op.drop_index("ix_training_cases_status", table_name="training_cases")
    op.drop_index("ix_training_cases_is_archived", table_name="training_cases")
    op.drop_index("ix_training_cases_created_at", table_name="training_cases")
    op.drop_index("ix_training_cases_company_id", table_name="training_cases")
    op.drop_table("training_cases")
    op.drop_table("training_case_counters")
