from datetime import date
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.administrator import Administrator
from app.models.company import Company
from app.models.trainer import Trainer
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.models.training_need import TrainingNeed


def login(client: TestClient, administrator: Administrator) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": administrator.email, "password": "Admin123!"},
    )
    assert response.status_code == 200


def make_case(
    session: Session,
    administrator: Administrator,
    status: TrainingCaseStatus = TrainingCaseStatus.FORMATEUR_ACCEPTE,
    *,
    with_trainer: bool = True,
    archived: bool = False,
) -> TrainingCase:
    company = Company(name=f"Entreprise {uuid4()}")
    trainer = Trainer(full_name="Formateur Test") if with_trainer else None
    training_case = TrainingCase(
        reference=f"TR-2026-{str(uuid4().int)[:6]}",
        company=company,
        trainer=trainer,
        theme="Audit RH",
        status=status.value,
        created_by=administrator.id,
        is_archived=archived,
    )
    session.add(training_case)
    session.commit()
    session.refresh(training_case)
    return training_case


def complete_payload() -> dict:
    return {
        "target_audience": "Cadres et responsables RH",
        "level": "INTERMEDIATE",
        "location": "Sur site client",
        "participant_count": 12,
        "delivery_mode": "PRESENTIEL",
        "duration_hours": 21,
        "planned_days_count": 3,
        "objectives": "Connaître les techniques essentielles de l’audit RH.",
        "desired_start_date": "2026-09-01",
        "desired_end_date": "2026-09-03",
        "constraints": "",
    }


@pytest.mark.parametrize("duration", [0.02, 1.5])
def test_duration_requires_at_least_one_complete_hour(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
    duration: float,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    payload = complete_payload()
    payload["duration_hours"] = duration

    response = client.post(f"/api/training-cases/{training_case.id}/need", json=payload)

    assert response.status_code == 422


def test_training_need_routes_require_authentication(client: TestClient) -> None:
    case_id = uuid4()
    assert client.get(f"/api/training-cases/{case_id}/need").status_code == 401
    assert client.post(f"/api/training-cases/{case_id}/need", json={}).status_code == 401
    assert client.patch(f"/api/training-cases/{case_id}/need", json={}).status_code == 401
    assert client.post(f"/api/training-cases/{case_id}/need/validate").status_code == 401


def test_create_read_update_draft_and_activity(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)

    created = client.post(
        f"/api/training-cases/{training_case.id}/need",
        json={"target_audience": "  Responsables RH  ", "participant_count": 8},
    )
    assert created.status_code == 201
    assert created.json()["target_audience"] == "Responsables RH"
    assert created.json()["is_validated"] is False
    db_session.refresh(training_case)
    assert training_case.status == TrainingCaseStatus.BESOIN_A_COMPLETER.value

    read = client.get(f"/api/training-cases/{training_case.id}/need")
    assert read.status_code == 200
    assert read.json()["id"] == created.json()["id"]

    updated = client.patch(
        f"/api/training-cases/{training_case.id}/need",
        json={"location": " Tunis ", "participant_count": 10},
    )
    assert updated.status_code == 200
    assert updated.json()["location"] == "Tunis"
    assert updated.json()["participant_count"] == 10
    assert updated.json()["is_validated"] is False

    activities = list(
        db_session.scalars(
            select(ActivityLog).where(ActivityLog.training_case_id == training_case.id)
        )
    )
    assert [item.action for item in activities] == [
        "TrainingNeedCreated",
        "TrainingNeedUpdated",
    ]
    assert "target_audience" not in str(activities[0].details)


def test_second_need_and_invalid_period_are_rejected(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    assert client.post(f"/api/training-cases/{training_case.id}/need", json={}).status_code == 201
    duplicate = client.post(f"/api/training-cases/{training_case.id}/need", json={})
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "TRAINING_NEED_ALREADY_EXISTS"

    other_case = make_case(db_session, active_administrator)
    invalid = client.post(
        f"/api/training-cases/{other_case.id}/need",
        json={"desired_start_date": "2026-09-03", "desired_end_date": "2026-09-01"},
    )
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "INVALID_TRAINING_NEED_PERIOD"


def test_end_date_must_match_start_and_planned_days(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    payload = complete_payload()
    payload["desired_start_date"] = "2026-09-23"
    payload["planned_days_count"] = 3
    payload["desired_end_date"] = "2026-09-26"

    invalid = client.post(f"/api/training-cases/{training_case.id}/need", json=payload)
    assert invalid.status_code == 400
    assert invalid.json()["code"] == "INVALID_TRAINING_NEED_PLANNED_PERIOD"
    assert invalid.json()["details"]["expected_end_date"] == "2026-09-25"

    payload["desired_end_date"] = "2026-09-25"
    valid = client.post(f"/api/training-cases/{training_case.id}/need", json=payload)
    assert valid.status_code == 201


def test_validation_is_atomic_and_validated_need_is_immutable(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(db_session, active_administrator)
    login(client, active_administrator)
    created = client.post(
        f"/api/training-cases/{training_case.id}/need",
        json={"target_audience": "Cadres"},
    )
    need_id = UUID(created.json()["id"])

    incomplete = client.post(f"/api/training-cases/{training_case.id}/need/validate")
    assert incomplete.status_code == 400
    assert incomplete.json()["code"] == "TRAINING_NEED_INCOMPLETE"
    assert incomplete.json()["details"]["missing_fields"] == [
        "level",
        "location",
        "participant_count",
        "delivery_mode",
        "duration_hours",
        "planned_days_count",
        "objectives",
        "desired_start_date",
        "desired_end_date",
    ]
    db_session.expire_all()
    need = db_session.get(TrainingNeed, need_id)
    current_case = db_session.get(TrainingCase, training_case.id)
    assert need is not None and need.is_validated is False
    assert current_case is not None
    assert current_case.status == TrainingCaseStatus.BESOIN_A_COMPLETER.value

    assert (
        client.patch(
            f"/api/training-cases/{training_case.id}/need", json=complete_payload()
        ).status_code
        == 200
    )
    validated = client.post(f"/api/training-cases/{training_case.id}/need/validate")
    assert validated.status_code == 200
    assert validated.json()["is_validated"] is True
    assert validated.json()["validated_at"] is not None
    db_session.expire_all()
    current_case = db_session.get(TrainingCase, training_case.id)
    assert current_case is not None
    assert current_case.status == TrainingCaseStatus.BESOIN_COMPLETE.value

    update = client.patch(
        f"/api/training-cases/{training_case.id}/need", json={"location": "Autre lieu"}
    )
    assert update.status_code == 409
    assert update.json()["code"] == "TRAINING_NEED_ALREADY_VALIDATED"
    repeated = client.post(f"/api/training-cases/{training_case.id}/need/validate")
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "TRAINING_NEED_ALREADY_VALIDATED"
    actions = list(
        db_session.scalars(
            select(ActivityLog.action).where(ActivityLog.training_case_id == training_case.id)
        )
    )
    assert "TrainingNeedValidated" in actions


def test_cancelled_and_archived_cases_reject_need_changes(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    cancelled = make_case(db_session, active_administrator, TrainingCaseStatus.ANNULE)
    archived = make_case(
        db_session,
        active_administrator,
        TrainingCaseStatus.ARCHIVE,
        archived=True,
    )
    login(client, active_administrator)

    cancelled_response = client.post(f"/api/training-cases/{cancelled.id}/need", json={})
    assert cancelled_response.status_code == 409
    assert cancelled_response.json()["code"] == "CANCELLED_TRAINING_CASE"
    archived_response = client.post(f"/api/training-cases/{archived.id}/need", json={})
    assert archived_response.status_code == 409
    assert archived_response.json()["code"] == "ARCHIVED_TRAINING_CASE"


def test_trainer_workflow_requires_trainer_and_strict_order(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    without_trainer = make_case(
        db_session,
        active_administrator,
        TrainingCaseStatus.RECHERCHE_FORMATEUR,
        with_trainer=False,
    )
    with_trainer = make_case(
        db_session,
        active_administrator,
        TrainingCaseStatus.RECHERCHE_FORMATEUR,
    )
    login(client, active_administrator)

    missing = client.post(
        f"/api/training-cases/{without_trainer.id}/change-status",
        json={"status": "FORMATEUR_PROPOSE"},
    )
    assert missing.status_code == 409
    assert missing.json()["code"] == "TRAINER_REQUIRED"

    out_of_order = client.post(
        f"/api/training-cases/{with_trainer.id}/change-status",
        json={"status": "FORMATEUR_ACCEPTE"},
    )
    assert out_of_order.status_code == 409

    proposed = client.post(
        f"/api/training-cases/{with_trainer.id}/change-status",
        json={"status": "FORMATEUR_PROPOSE"},
    )
    assert proposed.status_code == 200
    assert proposed.json()["status"] == "FORMATEUR_PROPOSE"
    accepted = client.post(
        f"/api/training-cases/{with_trainer.id}/change-status",
        json={"status": "FORMATEUR_ACCEPTE"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "FORMATEUR_ACCEPTE"
    opened = client.post(
        f"/api/training-cases/{with_trainer.id}/change-status",
        json={"status": "BESOIN_A_COMPLETER"},
    )
    assert opened.status_code == 200
    assert opened.json()["status"] == "BESOIN_A_COMPLETER"
    actions = list(
        db_session.scalars(
            select(ActivityLog.action).where(ActivityLog.training_case_id == with_trainer.id)
        )
    )
    assert actions == ["TrainerProposed", "TrainerAccepted", "CHANGEMENT_STATUT"]


def test_request_trainer_need_agreement_program_order(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_case(
        db_session,
        active_administrator,
        TrainingCaseStatus.DEMANDE_RECUE,
    )
    login(client, active_administrator)

    premature_need = client.post(f"/api/training-cases/{training_case.id}/need", json={})
    assert premature_need.status_code == 409
    assert premature_need.json()["code"] == "INVALID_TRAINING_CASE_STATUS"

    for status in ("RECHERCHE_FORMATEUR", "FORMATEUR_PROPOSE", "FORMATEUR_ACCEPTE"):
        response = client.post(
            f"/api/training-cases/{training_case.id}/change-status",
            json={"status": status},
        )
        assert response.status_code == 200

    created = client.post(
        f"/api/training-cases/{training_case.id}/need",
        json=complete_payload(),
    )
    assert created.status_code == 201
    validated = client.post(f"/api/training-cases/{training_case.id}/need/validate")
    assert validated.status_code == 200

    program = client.post(
        f"/api/training-cases/{training_case.id}/change-status",
        json={"status": "PROGRAMME_EN_PREPARATION"},
    )
    assert program.status_code == 200
    assert program.json()["status"] == "PROGRAMME_EN_PREPARATION"


def test_program_status_requires_an_existing_validated_need(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    without_need = make_case(
        db_session,
        active_administrator,
        TrainingCaseStatus.BESOIN_COMPLETE,
    )
    login(client, active_administrator)

    missing = client.post(
        f"/api/training-cases/{without_need.id}/change-status",
        json={"status": "PROGRAMME_EN_PREPARATION"},
    )
    assert missing.status_code == 409
    assert missing.json()["code"] == "TRAINING_NEED_REQUIRED"
    db_session.refresh(without_need)
    assert without_need.status == TrainingCaseStatus.BESOIN_COMPLETE.value

    unvalidated = make_case(
        db_session,
        active_administrator,
        TrainingCaseStatus.BESOIN_COMPLETE,
    )
    db_session.add(
        TrainingNeed(
            training_case_id=unvalidated.id,
            **{
                key: value
                for key, value in complete_payload().items()
                if key not in {"desired_start_date", "desired_end_date"}
            },
            desired_start_date=date.fromisoformat(complete_payload()["desired_start_date"]),
            desired_end_date=date.fromisoformat(complete_payload()["desired_end_date"]),
            is_validated=False,
        )
    )
    db_session.commit()
    rejected = client.post(
        f"/api/training-cases/{unvalidated.id}/change-status",
        json={"status": "PROGRAMME_EN_PREPARATION"},
    )
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "TRAINING_NEED_NOT_VALIDATED"
