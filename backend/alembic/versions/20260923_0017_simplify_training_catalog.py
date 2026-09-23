"""Replace detailed courses with the training families used by PrestaCode."""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "20260923_0017"
down_revision = "20260920_0016"
branch_labels = None
depends_on = None


# The catalogue is a persisted data source.  Each family is intentionally a
# single selectable item: detailed courses belong in the generated programme,
# not in the case theme selector.
TRAINING_FAMILIES = (
    "Management",
    "Communication",
    "Ressources humaines",
    "Gestion de projet",
    "Informatique",
    "Data & Business Intelligence",
    "Intelligence artificielle",
    "Cybersécurité",
    "Bureautique",
    "Qualité",
    "HSE / Sécurité au travail",
    "Finance & Comptabilité",
    "Commercial & Vente",
    "Marketing",
    "Achats & Logistique",
    "Service client",
    "Entrepreneuriat",
    "Leadership",
    "Développement personnel",
    "Langues",
)


def upgrade() -> None:
    table = sa.table(
        "training_catalog_items",
        sa.column("id", sa.Uuid()),
        sa.column("category", sa.String()),
        sa.column("title", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    op.execute(sa.text("DELETE FROM training_catalog_items"))
    op.bulk_insert(
        table,
        [
            {
                "id": uuid4(),
                "category": family,
                "title": family,
                "is_active": True,
            }
            for family in TRAINING_FAMILIES
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM training_catalog_items"))
