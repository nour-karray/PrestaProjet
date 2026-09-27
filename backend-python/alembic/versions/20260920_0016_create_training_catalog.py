"""Create and populate the active training catalogue."""

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "20260920_0016"
down_revision = "20260916_0015"
branch_labels = None
depends_on = None


CATALOGUE: dict[str, tuple[str, ...]] = {
    "Management": ("Management d'équipe", "Leadership et posture managériale", "Conduite du changement", "Gestion des conflits", "Management à distance"),
    "Communication": ("Communication professionnelle", "Prise de parole en public", "Communication assertive", "Communication interpersonnelle", "Techniques de négociation"),
    "RH": ("Recrutement", "Gestion des compétences", "Administration du personnel", "Entretien annuel d'évaluation", "Paie et législation sociale"),
    "Gestion de projet": ("Fondamentaux de la gestion de projet", "Méthodes Agile et Scrum", "Planification de projet", "Gestion des risques projet", "Pilotage par les indicateurs"),
    "Bureautique": ("Excel débutant", "Excel intermédiaire", "Excel avancé", "Word professionnel", "PowerPoint efficace"),
    "Data/BI": ("Power BI débutant", "Power BI avancé", "Analyse de données avec Excel", "Tableaux de bord décisionnels", "SQL pour l'analyse de données"),
    "Développement": ("Python débutant", "Python avancé", "Développement web avec JavaScript", "Développement web avec React", "API REST avec FastAPI"),
    "IA": ("Initiation à l'intelligence artificielle", "IA générative en entreprise", "Prompt engineering", "Machine learning appliqué", "Gouvernance et éthique de l'IA"),
    "Cybersécurité": ("Sensibilisation à la cybersécurité", "Sécurité des systèmes d'information", "Protection des données personnelles", "Gestion des incidents de sécurité", "Sécurité des réseaux"),
    "Qualité": ("ISO 9001", "Audit interne qualité", "Amélioration continue", "Gestion documentaire qualité", "Résolution de problèmes et 8D"),
    "HSE": ("Santé et sécurité au travail", "Évaluation des risques professionnels", "ISO 45001", "Gestion environnementale ISO 14001", "Prévention incendie et évacuation"),
    "Finance": ("Comptabilité générale", "Analyse financière", "Contrôle de gestion", "Budgétisation et prévisions", "Fiscalité des entreprises"),
    "Vente": ("Techniques de vente", "Vente consultative", "Négociation commerciale", "Prospection commerciale", "Gestion des objections"),
    "Marketing": ("Marketing digital", "Stratégie marketing", "Community management", "Référencement naturel SEO", "Marketing de contenu"),
    "Logistique": ("Gestion des stocks", "Supply chain management", "Achats et approvisionnements", "Transport et distribution", "Lean logistique"),
    "Service client": ("Relation client", "Gestion des réclamations", "Accueil et orientation client", "Expérience client", "Service client omnicanal"),
    "Entrepreneuriat": ("Créer son entreprise", "Business plan", "Gestion d'une TPE/PME", "Pitch et présentation de projet", "Financement de projet entrepreneurial"),
}


def upgrade() -> None:
    op.create_table(
        "training_catalog_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", name="uq_training_catalog_items_title"),
    )
    op.create_index("ix_training_catalog_items_active_category", "training_catalog_items", ["is_active", "category"])
    table = sa.table(
        "training_catalog_items",
        sa.column("id", sa.Uuid()),
        sa.column("category", sa.String()),
        sa.column("title", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(table, [
        {"id": uuid4(), "category": category, "title": title, "is_active": True}
        for category, titles in CATALOGUE.items()
        for title in titles
    ])


def downgrade() -> None:
    op.drop_index("ix_training_catalog_items_active_category", table_name="training_catalog_items")
    op.drop_table("training_catalog_items")
