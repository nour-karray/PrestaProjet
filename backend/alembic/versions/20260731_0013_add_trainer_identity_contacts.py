"""Add trainer identity and distinct phone contact fields."""

import sqlalchemy as sa
from alembic import op

revision = "20260731_0013"
down_revision = "20260730_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trainers", sa.Column("mobile_phone", sa.String(length=50)))
    op.add_column("trainers", sa.Column("birth_date", sa.String(length=50)))
    op.add_column("trainers", sa.Column("birth_place", sa.String(length=150)))
    op.add_column("trainers", sa.Column("address", sa.String(length=300)))
    op.add_column("trainers", sa.Column("employer_address", sa.String(length=300)))


def downgrade() -> None:
    op.drop_column("trainers", "employer_address")
    op.drop_column("trainers", "address")
    op.drop_column("trainers", "birth_place")
    op.drop_column("trainers", "birth_date")
    op.drop_column("trainers", "mobile_phone")
