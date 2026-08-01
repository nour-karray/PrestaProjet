"""Create companies and company contacts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260724_0002"
down_revision: str | None = "20260724_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("postal_code", sa.String(length=30), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("tax_identifier", sa.String(length=80), nullable=True),
        sa.Column("website", sa.String(length=300), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
    op.create_index("ix_companies_city", "companies", ["city"])
    op.create_index("ix_companies_country", "companies", ["country"])
    op.create_index("ix_companies_is_archived", "companies", ["is_archived"])
    op.create_index("ix_companies_lower_name", "companies", [sa.text("lower(name)")], unique=True)
    op.create_table(
        "company_contacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("job_title", sa.String(length=150), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_contacts_company_id", "company_contacts", ["company_id"])
    op.create_index(
        "uq_company_contacts_primary",
        "company_contacts",
        ["company_id"],
        unique=True,
        postgresql_where=sa.text("is_primary IS true"),
    )


def downgrade() -> None:
    op.drop_index("uq_company_contacts_primary", table_name="company_contacts")
    op.drop_index("ix_company_contacts_company_id", table_name="company_contacts")
    op.drop_table("company_contacts")
    op.drop_index("ix_companies_lower_name", table_name="companies")
    op.drop_index("ix_companies_is_archived", table_name="companies")
    op.drop_index("ix_companies_country", table_name="companies")
    op.drop_index("ix_companies_city", table_name="companies")
    op.drop_table("companies")
