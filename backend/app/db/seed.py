from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.administrator import Administrator
from app.models.company import Company, CompanyContact
from app.models.trainer import Trainer
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.repositories.administrator import AdministratorRepository
from app.repositories.company import CompanyRepository
from app.repositories.training_case import TrainingCaseRepository

DEMO_COMPANIES = (
    ("ABC Conseil", "Tunis", "Tunisie", False),
    ("Société XYZ", "Sfax", "Tunisie", False),
    ("Tech Plus", "Tunis", "Tunisie", False),
    ("Global Industrie", "Sousse", "Tunisie", False),
    ("Soft Net", "Ariana", "Tunisie", True),
)
DEMO_TRAINERS = (
    ("Naoufel Ben Labiedh", "Audit RH, GRH, Administration du personnel"),
    ("Karim Ben Salah", "Marketing digital, SEO"),
    ("Amina Zoghlami", "Management, Leadership, Communication"),
    ("Mourad Ellouze", "Sécurité, Prévention des risques"),
)


def seed_administrator(session: Session, email: str, password: str) -> Administrator:
    repository = AdministratorRepository(session)
    existing = repository.get_by_email(email)
    if existing is not None:
        return existing

    administrator = Administrator(
        full_name="Administrateur",
        email=email,
        password_hash=hash_password(password),
        is_active=True,
    )
    repository.add(administrator)
    session.commit()
    session.refresh(administrator)
    return administrator


def seed_companies(session: Session) -> None:
    repository = CompanyRepository(session)
    for index, (name, city, country, is_archived) in enumerate(DEMO_COMPANIES):
        company = repository.get_by_name(name)
        if company is None:
            company = Company(
                name=name,
                city=city,
                country=country,
                is_archived=is_archived,
            )
            repository.add(company)
        if index < 3 and not company.contacts:
            company.contacts.append(
                CompanyContact(
                    full_name=f"Contact {name}",
                    email=f"contact{index + 1}@formation.local",
                    job_title="Responsable formation",
                    is_primary=True,
                )
            )
    session.commit()


def seed_training_cases(session: Session, administrator: Administrator) -> None:
    cases = TrainingCaseRepository(session)
    companies = list(
        session.scalars(
            select(Company).where(Company.is_archived.is_(False)).order_by(Company.name).limit(4)
        )
    )
    demo_cases = (
        ("Audit des ressources humaines", TrainingCaseStatus.BROUILLON, False),
        ("Management d’équipe", TrainingCaseStatus.DEMANDE_RECUE, False),
        ("Marketing digital", TrainingCaseStatus.ANNULE, False),
        ("Sécurité au travail", TrainingCaseStatus.ARCHIVE, True),
    )
    now = datetime.now(UTC)
    for index, (theme, status, archived) in enumerate(demo_cases):
        existing = session.scalar(select(TrainingCase).where(TrainingCase.theme == theme))
        if existing is not None or index >= len(companies):
            continue
        company = companies[index]
        primary_contact = next(
            (contact for contact in company.contacts if contact.is_primary), None
        )
        training_case = TrainingCase(
            reference=cases.next_reference(now.year),
            company_id=company.id,
            primary_contact_id=primary_contact.id if primary_contact else None,
            theme=theme,
            description="Dossier de démonstration du Lot 4.",
            status=status.value,
            created_by=administrator.id,
            created_at=now - timedelta(days=index),
            is_archived=archived,
        )
        cases.add(training_case)
        session.add(
            ActivityLog(
                administrator_id=administrator.id,
                training_case_id=training_case.id,
                action="CREATION",
                entity_type="training_case",
                entity_id=training_case.id,
                details={"seed": True},
            )
        )
    session.commit()


def seed_trainers(session: Session) -> None:
    for full_name, job_title in DEMO_TRAINERS:
        if session.scalar(select(Trainer).where(Trainer.full_name == full_name)) is None:
            session.add(
                Trainer(
                    full_name=full_name,
                    job_title=job_title,
                    city="Tunis",
                    country="Tunisie",
                )
            )
    session.commit()


def main() -> None:
    if not settings.seed_demo_data:
        print("Données de démonstration désactivées.")
        return
    if not settings.demo_admin_email or not settings.demo_admin_password:
        raise RuntimeError(
            "DEMO_ADMIN_EMAIL et DEMO_ADMIN_PASSWORD sont requis "
            "lorsque SEED_DEMO_DATA=true."
        )
    with SessionLocal() as session:
        administrator = seed_administrator(
            session,
            settings.demo_admin_email,
            settings.demo_admin_password,
        )
        seed_companies(session)
        seed_training_cases(session, administrator)
        seed_trainers(session)
        print("Administrateur de démonstration prêt.")
        print("Entreprises de démonstration prêtes.")
        print("Dossiers de démonstration prêts.")
        print("Formateurs de démonstration prêts.")


if __name__ == "__main__":
    main()
