from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.local_llm import SchemaT
from app.core.errors import ApiError
from app.models.administrator import Administrator
from app.models.training_case import TrainingCase
from app.models.training_program import TrainingProgram
from app.services.program_generation import ProgramGenerationService
from app.tests.test_training_programs import make_eligible_case


class FakeLLM:
    model_name: str | None = "qwen3:8b"

    def __init__(
        self, response: dict | None = None, error: ApiError | None = None
    ) -> None:
        self.response = response
        self.error = error
        self.calls = 0

    def generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict:
        del prompt, response_schema
        self.calls += 1
        if self.error:
            raise self.error
        if self.response is None:
            raise AssertionError("La réponse factice doit être configurée.")
        return self.response


def valid_draft(minutes: int = 180) -> dict:
    return {
        "title": "Audit des ressources humaines",
        "general_objectives": "Conduire un audit RH structuré.",
        "prerequisites": "Aucun prérequis particulier.",
        "evaluation_method": "Étude de cas et mise en situation.",
        "days": [
            {
                "title": "Jour 1 — Fondamentaux",
                "position": 1,
                "modules": [
                    {
                        "title": "Conduire l’audit",
                        "content": "Principes et exercice pratique.",
                        "position": 1,
                        "theory_minutes": minutes // 2,
                        "practice_minutes": minutes - minutes // 2,
                        "methods": ["EXPOSE", "EXERCICE_PRATIQUE"],
                        "submodules": [],
                    }
                ],
            }
        ],
    }


def test_generation_creates_editable_draft_in_one_llm_call(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    llm = FakeLLM(valid_draft())
    result = ProgramGenerationService(db_session, llm).generate(case.id, active_administrator.id)
    assert llm.calls == 1
    assert result.prerequisites == "Aucun prérequis particulier."
    assert result.total_minutes == 180
    assert result.is_submitted is False
    assert result.is_validated is False
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, case.id)
    assert persisted_case is not None
    assert persisted_case.status == "PROGRAMME_EN_PREPARATION"


@pytest.mark.parametrize("minutes", [179, 181])
def test_invalid_duration_rolls_back_completely(
    db_session: Session, active_administrator: Administrator, minutes: int
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    with pytest.raises(ApiError) as raised:
        ProgramGenerationService(db_session, FakeLLM(valid_draft(minutes))).generate(
            case.id, active_administrator.id
        )
    assert raised.value.code == "PROGRAM_DURATION_MISMATCH"
    assert db_session.query(TrainingProgram).filter_by(training_case_id=case.id).count() == 0
    db_session.expire_all()
    persisted_case = db_session.get(TrainingCase, case.id)
    assert persisted_case is not None
    assert persisted_case.status == "BESOIN_COMPLETE"


def test_ollama_error_creates_nothing(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    error = ApiError(503, "LOCAL_LLM_UNAVAILABLE", "Ollama indisponible.")
    with pytest.raises(ApiError) as raised:
        ProgramGenerationService(db_session, FakeLLM(error=error)).generate(
            case.id, active_administrator.id
        )
    assert raised.value.status_code == 503
    assert db_session.query(TrainingProgram).count() == 0


def test_route_requires_authentication_and_matching_is_absent(client: TestClient) -> None:
    case_id = uuid4()
    assert client.post(f"/api/training-cases/{case_id}/program/generate-draft").status_code == 401
    assert client.post(f"/api/training-cases/{case_id}/trainer-matching").status_code == 404
