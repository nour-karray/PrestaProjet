from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.local_llm import OllamaLocalLLMClient, SchemaT
from app.ai.program_context_builder import _trainer_profile
from app.ai.program_prompt_builder import build_program_prompt
from app.core.config import settings
from app.core.errors import ApiError
from app.models.administrator import Administrator
from app.models.training_case import ActivityLog, TrainingCase
from app.models.training_program import TrainingProgram
from app.services.program_generation import ProgramGenerationService
from app.tests.test_training_programs import make_eligible_case


class FakeLLM:
    model_name: str | None = "qwen3:8b"

    def __init__(self, response: dict | None = None, error: ApiError | None = None) -> None:
        self.response = response
        self.error = error
        self.calls = 0
        self.last_prompt: str | None = None

    def generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict:
        del response_schema
        self.calls += 1
        self.last_prompt = prompt
        if self.error:
            raise self.error
        if self.response is None:
            raise AssertionError("La réponse factice doit être configurée.")
        return self.response


class SequenceLLM:
    model_name: str | None = "qwen-prestacode-v3"

    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls = 0
        self.prompts: list[str] = []

    def generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict:
        del response_schema
        self.prompts.append(prompt)
        response = self.responses[self.calls]
        self.calls += 1
        return deepcopy(response)


def test_program_context_uses_only_structured_trainer_profile_fields() -> None:
    trainer = SimpleNamespace(
        full_name="Amira Bouzid",
        years_experience=12,
        cvs=[SimpleNamespace(
            uploaded_at=1,
            raw_text="Ce texte brut de CV ne doit jamais être envoyé au programme.",
            parsed_json={
                "skills": ["Cybersécurité", "Audit"],
                "certifications": [{"name": "ISO 27001"}],
                "experiences": [{"job_title": "Consultante cybersécurité"}],
            },
        )],
    )

    profile = _trainer_profile(trainer)

    assert profile == {
        "name": "Amira Bouzid",
        "specialties": ["Cybersécurité", "Audit"],
        "domains": ["Consultante cybersécurité"],
        "years_of_experience": 12,
        "certifications": ["ISO 27001"],
    }


def valid_draft(minutes: int = 180) -> dict:
    first_total = minutes // 2
    second_total = minutes - first_total
    return {
        "title": "Audit des ressources humaines",
        "general_objectives": "Conduire un audit RH structuré.",
        "prerequisites": "Aucun prérequis particulier.",
        "evaluation_method": (
            "Étude de cas finale avec restitution orale, grille d’observation et plan d’action."
        ),
        "days": [
            {
                "title": "Jour 1 — Fondamentaux",
                "position": 1,
                "modules": [
                    {
                        "title": "Conduire l’audit",
                        "content": (
                            "Notions : périmètre ; parties prenantes ; critères ; risques ; "
                            "preuves. Activité : analyser un dossier d’audit."
                        ),
                        "position": 1,
                        "theory_minutes": first_total // 2,
                        "practice_minutes": first_total - first_total // 2,
                        "methods": ["EXPOSE", "EXERCICE_PRATIQUE"],
                        "submodules": [],
                    },
                    {
                        "title": "Restituer les constats d’audit",
                        "content": (
                            "Notions : hiérarchisation ; écart ; cause ; recommandation ; suivi. "
                            "Activité : présenter des constats argumentés."
                        ),
                        "position": 2,
                        "theory_minutes": second_total // 2,
                        "practice_minutes": second_total - second_total // 2,
                        "methods": ["ETUDE_DE_CAS", "ECHANGE_COLLECTIF"],
                        "submodules": [],
                    },
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


def test_poor_program_is_corrected_once_and_corrected_version_is_used(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    poor = valid_draft()
    poor["days"][0]["modules"][0]["content"] = "Notions : audit ; contrôle."
    corrected = valid_draft()
    corrected["days"][0]["modules"][0]["content"] = (
        "Notions : périmètre ; acteurs ; preuves ; critères ; risques ; écarts. "
        "Activité : analyser un dossier et restituer les constats."
    )
    llm = SequenceLLM([poor, corrected])

    result = ProgramGenerationService(db_session, llm).generate(
        case.id, active_administrator.id
    )

    assert llm.calls == 2
    assert "ANOMALIES À CORRIGER" in llm.prompts[1]
    assert "RUBRIC_CONTENT_TOO_POOR" in llm.prompts[1]
    assert result.days[0].items[0].content == corrected["days"][0]["modules"][0]["content"]
    assert result.pedagogical_correction_performed is True
    assert result.pedagogical_warning is None


def test_imperfect_correction_is_kept_as_draft_with_warning_and_no_third_call(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    poor = valid_draft()
    poor["days"][0]["modules"][0]["content"] = "Notions : audit ; contrôle."
    still_poor = deepcopy(poor)
    llm = SequenceLLM([poor, still_poor])

    result = ProgramGenerationService(db_session, llm).generate(
        case.id, active_administrator.id
    )

    assert llm.calls == 2
    assert result.days[0].items[0].content == "Notions : audit ; contrôle."
    assert result.pedagogical_warning == (
        "Le programme a été généré mais certains éléments méritent une vérification "
        "pédagogique."
    )
    actions = [
        row.action
        for row in db_session.query(ActivityLog)
        .filter(ActivityLog.training_case_id == case.id)
        .all()
    ]
    assert "TrainingProgramInitialGenerated" in actions
    assert "TrainingProgramPedagogicalCorrectionPerformed" in actions


def test_correction_cannot_change_duration_or_day_count(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    poor = valid_draft()
    poor["days"][0]["modules"][0]["content"] = "Notions : audit ; contrôle."
    invalid_correction = valid_draft(240)
    extra_day = deepcopy(invalid_correction["days"][0])
    extra_day["position"] = 2
    extra_day["title"] = "Jour 2 — Ajout interdit"
    invalid_correction["days"].append(extra_day)
    llm = SequenceLLM([poor, invalid_correction])

    result = ProgramGenerationService(db_session, llm).generate(
        case.id, active_administrator.id
    )

    assert llm.calls == 2
    assert result.total_minutes == 180
    assert len(result.days) == 1
    assert result.pedagogical_warning is not None


def test_generation_completes_content_omitted_by_fine_tuned_model(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    response = valid_draft()
    del response["days"][0]["modules"][0]["content"]

    result = ProgramGenerationService(db_session, FakeLLM(response)).generate(
        case.id, active_administrator.id
    )

    assert result.days[0].items[0].content == (
        "Apports, consignes et activités du module : Conduire l’audit."
    )


@pytest.mark.parametrize(
    ("theme", "level", "days", "minutes"),
    [
        ("Communication", "INTERMEDIATE", 5, 2700),
        ("Cybersécurité", "BEGINNER", 6, 1800),
        ("Ressources humaines", "INTERMEDIATE", 3, 1080),
    ],
)
def test_quality_prompt_covers_representative_programs(
    theme: str, level: str, days: int, minutes: int
) -> None:
    prompt = build_program_prompt(
        {
            "theme": theme,
            "client_need": f"Appliquer {theme} au contexte métier.",
            "target_audience": "Équipe opérationnelle",
            "level": level,
            "pedagogical_objectives": "Produire un livrable professionnel.",
            "planned_days_count": days,
            "total_minutes": minutes,
            "delivery_mode": "PRESENTIEL",
            "constraints": "Cas adaptés au public.",
            "trainer_profile": {"skills": [theme], "years_of_experience": 10},
            "allowed_methods": ["EXPOSE", "EXERCICE_PRATIQUE", "ETUDE_DE_CAS"],
        }
    )

    assert theme in prompt
    assert level in prompt
    assert f'"planned_days_count": {days}' in prompt
    assert "2 à 5 rubriques" in prompt
    assert "4 à 10 notions concrètes" in prompt
    assert "Notions : indicateurs pertinents" in prompt
    assert "EXACTEMENT planned_days_count" in prompt
    assert "Évite de répéter exactement la même combinaison" in prompt
    assert "modalité concrète" in prompt
    assert "dernière journée" in prompt
    assert "Structurer un message professionnel" in prompt


def test_program_generation_uses_configured_local_llm_timeout(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "local_llm_timeout_seconds", 300)
    service = ProgramGenerationService(db_session)
    assert isinstance(service.llm, OllamaLocalLLMClient)
    assert service.llm.timeout_seconds == 300


def test_program_generation_uses_the_dedicated_program_model(db_session: Session) -> None:
    service = ProgramGenerationService(db_session)

    assert isinstance(service.llm, OllamaLocalLLMClient)
    assert service.llm.model_name == settings.local_llm_model


@pytest.mark.parametrize("minutes", [179, 181])
def test_generated_duration_is_normalized_before_persistence(
    db_session: Session, active_administrator: Administrator, minutes: int
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    result = ProgramGenerationService(db_session, FakeLLM(valid_draft(minutes))).generate(
        case.id, active_administrator.id
    )
    assert result.total_minutes == 180
    assert db_session.query(TrainingProgram).filter_by(training_case_id=case.id).count() == 1


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


@pytest.mark.parametrize(
    ("status_code", "code"),
    [
        (504, "LLM_TIMEOUT"),
        (503, "LLM_MODEL_NOT_FOUND"),
        (503, "LLM_UNAVAILABLE"),
        (502, "LLM_GENERATION_FAILED"),
    ],
)
def test_program_generation_preserves_distinct_ollama_errors(
    status_code: int,
    code: str,
    db_session: Session,
    active_administrator: Administrator,
) -> None:
    case = make_eligible_case(db_session, active_administrator)
    with pytest.raises(ApiError) as raised:
        ProgramGenerationService(
            db_session,
            FakeLLM(error=ApiError(status_code, code, "Erreur Ollama")),
        ).generate(case.id, active_administrator.id)
    assert raised.value.status_code == status_code
    assert raised.value.code == code
    assert db_session.query(TrainingProgram).filter_by(training_case_id=case.id).count() == 0


def test_generation_rejects_wrong_day_count_without_persisting(
    db_session: Session, active_administrator: Administrator
) -> None:
    case = make_eligible_case(
        db_session,
        active_administrator,
        duration_hours=Decimal("35"),
        planned_days_count=5,
    )
    with pytest.raises(ApiError) as raised:
        ProgramGenerationService(db_session, FakeLLM(valid_draft(2100))).generate(
            case.id, active_administrator.id
        )
    assert raised.value.code == "PROGRAM_DAY_COUNT_MISMATCH"
    assert raised.value.details == {"expected_days": 5, "actual_days": 1}
    assert db_session.query(TrainingProgram).filter_by(training_case_id=case.id).count() == 0


def test_route_requires_authentication_and_matching_is_absent(client: TestClient) -> None:
    case_id = uuid4()
    assert client.post(f"/api/training-cases/{case_id}/program/generate-draft").status_code == 401
    assert client.post(f"/api/training-cases/{case_id}/trainer-matching").status_code == 404
