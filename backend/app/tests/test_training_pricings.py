from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.administrator import Administrator
from app.models.company import Company
from app.models.trainer import Trainer
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.models.training_program import (
    TrainingProgram,
    TrainingProgramDay,
    TrainingProgramItem,
)


def login(client: TestClient, administrator: Administrator) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": administrator.email, "password": "Admin123!"},
    )
    assert response.status_code == 200


def make_case(
    session: Session,
    administrator: Administrator,
    *,
    daily_rate: Decimal | None = Decimal("400"),
    hourly_rate: Decimal | None = Decimal("50"),
    day_count: int = 3,
    minutes_per_day: int = 60,
    status: TrainingCaseStatus = TrainingCaseStatus.PROGRAMME_VALIDE,
    validated_program: bool = True,
    with_trainer: bool = True,
    archived: bool = False,
) -> TrainingCase:
    trainer = (
        Trainer(
            full_name="Formateur Tarification",
            daily_rate=daily_rate,
            hourly_rate=hourly_rate,
        )
        if with_trainer
        else None
    )
    training_case = TrainingCase(
        reference=f"TR-2026-{str(uuid4().int)[:6]}",
        company=Company(name=f"Entreprise {uuid4()}"),
        trainer=trainer,
        theme="Audit RH",
        status=status.value,
        created_by=administrator.id,
        is_archived=archived,
    )
    program = TrainingProgram(
        training_case=training_case,
        title="Programme Audit RH",
        general_objectives="Conduire un audit.",
        is_submitted=True,
        is_validated=validated_program,
    )
    for position in range(1, day_count + 1):
        day = TrainingProgramDay(
            program=program,
            title=f"Jour {position}",
            position=position,
        )
        day.items.append(
            TrainingProgramItem(
                item_type="MODULE",
                title=f"Module {position}",
                content="Contenu",
                theory_minutes=minutes_per_day,
                practice_minutes=0,
                position=1,
            )
        )
    session.add(training_case)
    session.commit()
    session.refresh(training_case)
    return training_case


def create_pricing(client: TestClient, case_id) -> dict:
    response = client.post(f"/api/training-cases/{case_id}/pricing", json={})
    assert response.status_code == 201, response.text
    return response.json()


def amount(payload: dict, field: str) -> Decimal:
    return Decimal(str(payload[field]))


def test_pricing_routes_require_authentication(client: TestClient) -> None:
    case_id = uuid4()
    assert client.get(f"/api/training-cases/{case_id}/pricing").status_code == 401
    assert client.post(f"/api/training-cases/{case_id}/pricing", json={}).status_code == 401
    assert client.patch(f"/api/training-cases/{case_id}/pricing", json={}).status_code == 401


def test_creation_uses_daily_rate_and_preserves_snapshots(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    pricing = create_pricing(client, training_case.id)

    assert amount(pricing, "trainer_cost") == Decimal("1200.000")
    assert amount(pricing, "trainer_daily_rate_snapshot") == Decimal("400.000")
    assert amount(pricing, "trainer_hourly_rate_snapshot") == Decimal("50.000")
    assert pricing["program_day_count_snapshot"] == 3
    assert pricing["program_duration_minutes_snapshot"] == 180
    assert pricing["trainer_cost_initialization_method"] == "DAILY_RATE"
    assert amount(pricing, "vat_rate") == Decimal("19.000")
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert (
        persisted_case.status
        == TrainingCaseStatus.TARIFICATION_EN_PREPARATION.value
    )

    duplicate = client.post(f"/api/training-cases/{training_case.id}/pricing", json={})
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "TRAINING_PRICING_ALREADY_EXISTS"


def test_hourly_fallback_and_no_rate_initialization(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    hourly_case = make_case(
        db_session,
        active_administrator,
        daily_rate=None,
        hourly_rate=Decimal("42.500"),
        day_count=2,
        minutes_per_day=90,
    )
    no_rate_case = make_case(
        db_session,
        active_administrator,
        daily_rate=None,
        hourly_rate=None,
    )
    login(client, active_administrator)

    hourly = create_pricing(client, hourly_case.id)
    assert amount(hourly, "trainer_cost") == Decimal("127.500")
    assert hourly["trainer_cost_initialization_method"] == "HOURLY_RATE"
    none = create_pricing(client, no_rate_case.id)
    assert amount(none, "trainer_cost") == Decimal("0.000")
    assert none["trainer_cost_initialization_method"] == "NONE"


def test_creation_requires_validated_program_trainer_and_status(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    wrong_status = make_case(
        db_session,
        active_administrator,
        status=TrainingCaseStatus.PROGRAMME_EN_PREPARATION,
    )
    invalid_program = make_case(
        db_session,
        active_administrator,
        validated_program=False,
    )
    no_trainer = make_case(db_session, active_administrator, with_trainer=False)
    archived = make_case(db_session, active_administrator, archived=True)
    login(client, active_administrator)

    assert client.post(f"/api/training-cases/{wrong_status.id}/pricing", json={}).status_code == 409
    response = client.post(f"/api/training-cases/{invalid_program.id}/pricing", json={})
    assert response.status_code == 409
    assert response.json()["code"] == "TRAINING_PROGRAM_NOT_VALIDATED"
    assert client.post(f"/api/training-cases/{no_trainer.id}/pricing", json={}).status_code == 409
    assert client.post(f"/api/training-cases/{archived.id}/pricing", json={}).status_code == 409


def test_financial_calculations_rounding_and_allowed_vat_rates(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    create_pricing(client, training_case.id)

    response = client.patch(
        f"/api/training-cases/{training_case.id}/pricing",
        json={
            "trainer_cost": "1200.000",
            "transport_cost": "200.000",
            "room_cost": "300.000",
            "meal_cost": "150.000",
            "other_cost": "100.000",
            "margin_rate": "20.000",
            "vat_rate": "19.000",
        },
    )
    assert response.status_code == 200, response.text
    pricing = response.json()
    assert amount(pricing, "total_costs") == Decimal("1950.000")
    assert amount(pricing, "margin_amount") == Decimal("390.000")
    assert amount(pricing, "total_excluding_tax") == Decimal("2340.000")
    assert amount(pricing, "vat_amount") == Decimal("444.600")
    assert amount(pricing, "total_including_tax") == Decimal("2784.600")

    rounded = client.patch(
        f"/api/training-cases/{training_case.id}/pricing",
        json={"trainer_cost": "1.2345", "margin_rate": "33.333", "vat_rate": "7.000"},
    ).json()
    assert amount(rounded, "trainer_cost") == Decimal("1.235")
    assert amount(rounded, "vat_rate") == Decimal("7.000")

    invalid_rate = client.patch(
        f"/api/training-cases/{training_case.id}/pricing",
        json={"vat_rate": "5.000"},
    )
    assert invalid_rate.status_code == 422


def test_zero_vat_requires_fiscal_justification(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    create_pricing(client, training_case.id)

    missing = client.patch(
        f"/api/training-cases/{training_case.id}/pricing",
        json={"vat_rate": "0.000"},
    )
    assert missing.status_code == 400
    assert missing.json()["code"] == "VAT_EXEMPTION_JUSTIFICATION_REQUIRED"
    accepted = client.patch(
        f"/api/training-cases/{training_case.id}/pricing",
        json={
            "vat_rate": "0.000",
            "vat_exemption_reason": "Opération exonérée après vérification.",
        },
    )
    assert accepted.status_code == 200
    assert amount(accepted.json(), "vat_amount") == Decimal("0.000")


def test_submit_return_validate_and_immutability(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    pricing = create_pricing(client, training_case.id)
    pricing_id = pricing["id"]

    submitted = client.post(f"/api/training-cases/{training_case.id}/pricing/submit")
    assert submitted.status_code == 200
    assert submitted.json()["is_submitted"] is True
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert (
        persisted_case.status
        == TrainingCaseStatus.TARIFICATION_A_VALIDER.value
    )
    readonly = client.patch(
        f"/api/training-cases/{training_case.id}/pricing",
        json={"room_cost": "10.000"},
    )
    assert readonly.status_code == 409

    assert (
        client.post(
            f"/api/training-cases/{training_case.id}/pricing/return",
            json={"reason": " "},
        ).status_code
        == 422
    )
    returned = client.post(
        f"/api/training-cases/{training_case.id}/pricing/return",
        json={"reason": "Vérifier les frais de salle."},
    )
    assert returned.status_code == 200
    assert returned.json()["return_reason"] == "Vérifier les frais de salle."
    assert returned.json()["is_submitted"] is False

    assert (
        client.patch(
            f"/api/training-cases/{training_case.id}/pricing",
            json={"room_cost": "10.000"},
        ).status_code
        == 200
    )
    assert client.post(f"/api/training-cases/{training_case.id}/pricing/submit").status_code == 200
    validated = client.post(f"/api/training-cases/{training_case.id}/pricing/validate")
    assert validated.status_code == 200
    assert validated.json()["is_validated"] is True
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert (
        persisted_case.status
        == TrainingCaseStatus.TARIFICATION_VALIDEE.value
    )
    assert (
        client.post(f"/api/training-cases/{training_case.id}/pricing/validate").status_code == 409
    )
    assert (
        client.post(
            f"/api/training-cases/{training_case.id}/pricing/return",
            json={"reason": "Interdit"},
        ).status_code
        == 409
    )
    assert client.get(f"/api/training-cases/{training_case.id}/pricing").json()["id"] == pricing_id

    actions = list(
        db_session.scalars(
            select(ActivityLog.action).where(ActivityLog.training_case_id == training_case.id)
        )
    )
    assert {
        "TrainingPricingCreated",
        "TrainingPricingUpdated",
        "TrainingPricingSubmitted",
        "TrainingPricingReturned",
        "TrainingPricingValidated",
    }.issubset(actions)


def test_empty_pricing_cannot_be_submitted_and_snapshots_do_not_change(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(
        db_session,
        active_administrator,
        daily_rate=None,
        hourly_rate=None,
    )
    login(client, active_administrator)
    created = create_pricing(client, training_case.id)
    trainer = db_session.get(Trainer, training_case.trainer_id)
    assert trainer is not None
    trainer.daily_rate = Decimal("999.000")
    db_session.commit()

    empty = client.post(f"/api/training-cases/{training_case.id}/pricing/submit")
    assert empty.status_code == 400
    assert empty.json()["code"] == "TRAINING_PRICING_EMPTY"
    reloaded = client.get(f"/api/training-cases/{training_case.id}/pricing").json()
    assert reloaded["trainer_daily_rate_snapshot"] is None
    assert amount(reloaded, "trainer_cost") == amount(created, "trainer_cost")
