from datetime import date
from decimal import Decimal
from uuid import uuid4

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


def make_eligible_case(
    session: Session,
    administrator: Administrator,
    *,
    duration_hours: Decimal = Decimal("3"),
    planned_days_count: int = 1,
    status: TrainingCaseStatus = TrainingCaseStatus.BESOIN_COMPLETE,
    validated_need: bool = True,
    with_trainer: bool = True,
) -> TrainingCase:
    training_case = TrainingCase(
        reference=f"TR-2026-{str(uuid4().int)[:6]}",
        company=Company(name=f"Entreprise {uuid4()}"),
        trainer=Trainer(full_name="Formatrice Test") if with_trainer else None,
        theme="Audit des ressources humaines",
        status=status.value,
        created_by=administrator.id,
    )
    session.add(training_case)
    session.flush()
    session.add(
        TrainingNeed(
            training_case_id=training_case.id,
            target_audience="Responsables RH",
            level="INTERMEDIATE",
            location="Tunis",
            participant_count=8,
            delivery_mode="PRESENTIEL",
            duration_hours=duration_hours,
            planned_days_count=planned_days_count,
            objectives="Maîtriser les fondamentaux de l’audit RH.",
            desired_start_date=date(2026, 9, 1),
            desired_end_date=date(2026, 9, max(1, planned_days_count)),
            is_validated=validated_need,
        )
    )
    session.commit()
    session.refresh(training_case)
    return training_case


def create_program(client: TestClient, case_id) -> dict:
    response = client.post(
        f"/api/training-cases/{case_id}/program",
        json={
            "title": "Programme d’audit RH",
            "general_objectives": "Conduire un audit RH structuré.",
            "evaluation_method": "Mise en situation finale.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def add_day(client: TestClient, case_id, title: str = "Jour 1") -> dict:
    response = client.post(
        f"/api/training-cases/{case_id}/program/days",
        json={"title": title},
    )
    assert response.status_code == 200, response.text
    return response.json()


def add_item(
    client: TestClient,
    case_id,
    day_id,
    *,
    title: str,
    theory: int,
    practice: int,
    parent_id=None,
) -> dict:
    response = client.post(
        f"/api/training-cases/{case_id}/program/days/{day_id}/items",
        json={
            "item_type": "SUBMODULE" if parent_id else "MODULE",
            "parent_id": parent_id,
            "title": title,
            "content": f"Contenu de {title}",
            "theory_minutes": theory,
            "practice_minutes": practice,
            "methods": ["EXPOSE", "EXERCICE_PRATIQUE"],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_program_routes_require_authentication(client: TestClient) -> None:
    case_id = uuid4()
    assert client.get(f"/api/training-cases/{case_id}/program").status_code == 401
    assert client.post(f"/api/training-cases/{case_id}/program", json={}).status_code == 401


def test_creation_eligibility_and_uniqueness(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    login(client, active_administrator)
    eligible = make_eligible_case(db_session, active_administrator)
    created = create_program(client, eligible.id)
    assert created["title"] == "Programme d’audit RH"
    assert created["expected_total_minutes"] == 180
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, eligible.id)
    assert persisted_case is not None
    assert persisted_case.status == "PROGRAMME_EN_PREPARATION"

    duplicate = client.post(f"/api/training-cases/{eligible.id}/program", json={})
    assert duplicate.status_code == 409

    wrong_status = make_eligible_case(
        db_session,
        active_administrator,
        status=TrainingCaseStatus.BESOIN_A_COMPLETER,
    )
    assert client.post(f"/api/training-cases/{wrong_status.id}/program", json={}).status_code == 409

    accepted_only = make_eligible_case(
        db_session,
        active_administrator,
        status=TrainingCaseStatus.FORMATEUR_ACCEPTE,
    )
    accepted_response = client.post(
        f"/api/training-cases/{accepted_only.id}/program",
        json={},
    )
    assert accepted_response.status_code == 409
    assert accepted_response.json()["code"] == "INVALID_TRAINING_CASE_STATUS"

    no_trainer = make_eligible_case(db_session, active_administrator, with_trainer=False)
    assert client.post(f"/api/training-cases/{no_trainer.id}/program", json={}).status_code == 409

    unvalidated = make_eligible_case(db_session, active_administrator, validated_need=False)
    response = client.post(f"/api/training-cases/{unvalidated.id}/program", json={})
    assert response.status_code == 409
    assert response.json()["code"] == "TRAINING_NEED_NOT_VALIDATED"


def test_nested_crud_ordering_and_duration_without_double_count(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_eligible_case(db_session, active_administrator)
    login(client, active_administrator)
    create_program(client, training_case.id)
    first = add_day(client, training_case.id, "Jour A")
    second = add_day(client, training_case.id, "Jour B")
    first_day_id = first["days"][0]["id"]
    second_day_id = second["days"][1]["id"]

    moved = client.post(
        f"/api/training-cases/{training_case.id}/program/days/{second_day_id}/move-up"
    )
    assert [day["title"] for day in moved.json()["days"]] == ["Jour B", "Jour A"]

    module = add_item(
        client,
        training_case.id,
        first_day_id,
        title="Module parent",
        theory=0,
        practice=0,
    )
    module_id = module["days"][1]["items"][0]["id"]
    nested = add_item(
        client,
        training_case.id,
        first_day_id,
        parent_id=module_id,
        title="Sous-module",
        theory=60,
        practice=120,
    )
    assert nested["total_minutes"] == 180
    assert nested["days"][1]["items"][0]["total_minutes"] == 180

    invalid_duration = client.patch(
        f"/api/training-cases/{training_case.id}/program/items/{module_id}",
        json={"theory_minutes": 10},
    )
    assert invalid_duration.status_code == 400
    assert invalid_duration.json()["code"] == "MODULE_WITH_CHILDREN_HAS_DIRECT_DURATION"

    submodule_id = nested["days"][1]["items"][0]["children"][0]["id"]
    deleted = client.delete(f"/api/training-cases/{training_case.id}/program/items/{submodule_id}")
    assert deleted.status_code == 200
    assert deleted.json()["total_minutes"] == 0

    removed_day = client.delete(
        f"/api/training-cases/{training_case.id}/program/days/{second_day_id}"
    )
    assert removed_day.status_code == 200
    assert [day["position"] for day in removed_day.json()["days"]] == [1]

    first_module = add_item(
        client,
        training_case.id,
        first_day_id,
        title="Premier module",
        theory=30,
        practice=0,
    )
    second_module = add_item(
        client,
        training_case.id,
        first_day_id,
        title="Second module",
        theory=30,
        practice=0,
    )
    first_module_id = first_module["days"][0]["items"][1]["id"]
    second_module_id = second_module["days"][0]["items"][2]["id"]
    reordered = client.post(
        f"/api/training-cases/{training_case.id}/program/items/{second_module_id}/move-up"
    )
    assert [item["title"] for item in reordered.json()["days"][0]["items"]] == [
        "Module parent",
        "Second module",
        "Premier module",
    ]
    normalized = client.delete(
        f"/api/training-cases/{training_case.id}/program/items/{first_module_id}"
    )
    assert [item["position"] for item in normalized.json()["days"][0]["items"]] == [1, 2]


def test_submit_return_validate_and_immutability(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_eligible_case(db_session, active_administrator)
    login(client, active_administrator)
    create_program(client, training_case.id)
    program = add_day(client, training_case.id)
    day_id = program["days"][0]["id"]
    add_item(
        client,
        training_case.id,
        day_id,
        title="Audit RH",
        theory=60,
        practice=120,
    )

    submitted = client.post(f"/api/training-cases/{training_case.id}/program/submit")
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["is_submitted"] is True
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert persisted_case.status == "PROGRAMME_A_VALIDER"

    readonly = client.patch(
        f"/api/training-cases/{training_case.id}/program",
        json={"title": "Modification interdite"},
    )
    assert readonly.status_code == 409

    missing_reason = client.post(
        f"/api/training-cases/{training_case.id}/program/return",
        json={"reason": " "},
    )
    assert missing_reason.status_code == 422
    returned = client.post(
        f"/api/training-cases/{training_case.id}/program/return",
        json={"reason": "Ajouter un exemple pratique."},
    )
    assert returned.status_code == 200
    assert returned.json()["is_submitted"] is False
    assert returned.json()["return_reason"] == "Ajouter un exemple pratique."

    resubmitted = client.post(f"/api/training-cases/{training_case.id}/program/submit")
    assert resubmitted.status_code == 200
    validated = client.post(f"/api/training-cases/{training_case.id}/program/validate")
    assert validated.status_code == 200
    assert validated.json()["is_validated"] is True
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, training_case.id)
    assert persisted_case is not None
    assert persisted_case.status == "PROGRAMME_VALIDE"

    immutable = client.delete(f"/api/training-cases/{training_case.id}/program/days/{day_id}")
    assert immutable.status_code == 409
    assert immutable.json()["code"] == "TRAINING_PROGRAM_NOT_EDITABLE"


def test_submission_rejects_incomplete_or_wrong_duration(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_eligible_case(db_session, active_administrator)
    login(client, active_administrator)
    create_program(client, training_case.id)
    incomplete = client.post(f"/api/training-cases/{training_case.id}/program/submit")
    assert incomplete.status_code == 400
    assert incomplete.json()["code"] == "TRAINING_PROGRAM_INCOMPLETE"

    program = add_day(client, training_case.id)
    day_id = program["days"][0]["id"]
    add_item(
        client,
        training_case.id,
        day_id,
        title="Module trop court",
        theory=60,
        practice=60,
    )
    mismatch = client.post(f"/api/training-cases/{training_case.id}/program/submit")
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "PROGRAM_DURATION_MISMATCH"
    assert mismatch.json()["details"] == {
        "expected_minutes": 180,
        "actual_minutes": 120,
    }


def test_activity_logs_do_not_contain_program_content(
    client: TestClient,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    training_case = make_eligible_case(db_session, active_administrator)
    login(client, active_administrator)
    create_program(client, training_case.id)
    program = add_day(client, training_case.id, "Journée confidentielle")
    day_id = program["days"][0]["id"]
    add_item(
        client,
        training_case.id,
        day_id,
        title="Titre confidentiel",
        theory=180,
        practice=0,
    )
    logs = list(
        db_session.scalars(
            select(ActivityLog).where(ActivityLog.training_case_id == training_case.id)
        )
    )
    serialized = str([log.details for log in logs])
    assert "Titre confidentiel" not in serialized
    assert "Contenu de" not in serialized
