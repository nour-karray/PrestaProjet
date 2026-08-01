from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.local_llm import OllamaLocalLLMClient, SchemaT, parse_json_response
from app.core.config import settings
from app.core.errors import ApiError
from app.models.administrator import Administrator
from app.models.trainer import Trainer, TrainerCV, TrainerCVExtractionStatus
from app.schemas.cv_extraction import TrainerCVExtractionResult
from app.services.cv_ocr import OCRExtractor
from app.services.cv_text_extractor import CVTextExtractionResult, CVTextExtractor
from app.services.trainer import TrainerCVExtractionService
from app.services.trainer_cv_extractor import _apply_deterministic_fallback


def test_identity_labels_keep_phone_and_gsm_separate() -> None:
    text = """Identité :
Nom et Prénom : WALID KARRAY Nationalité : Tunisienne
Date et lieu de Naissance : 1981-09-27 à Monastir N°CIN/Passeport : FICTIF-004981
Mail : walid.karray@example.test GSM : 29 710 553
Adresse : 10 boulevard Habib Bourguiba,
Monastir 5000
Employeur actuel : Project Bridge Consulting
Adresse de l'employeur : Monastir Téléphone : 73 460 721
Public Privé Indépendant [X]
"""

    result = _apply_deterministic_fallback(TrainerCVExtractionResult(), text)

    assert result.full_name == "WALID KARRAY"
    assert result.birth_date == "1981-09-27"
    assert result.birth_place == "Monastir"
    assert result.email == "walid.karray@example.test"
    assert result.address == "10 boulevard Habib Bourguiba, Monastir 5000"
    assert result.company == "Project Bridge Consulting"
    assert result.employer_address == "Monastir"
    assert result.phone == "73 460 721"
    assert result.mobile_phone == "29 710 553"


class FakeLLM:
    model_name: str | None = "qwen-test"

    def __init__(self, error: ApiError | None = None) -> None:
        self.error = error

    def generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict:
        del prompt, response_schema
        if self.error:
            raise self.error
        return {
            "first_name": "Karim",
            "last_name": "Test",
            "full_name": "Karim Test",
            "email": "karim@example.com",
            "phone": None,
            "company": None,
            "job_title": "Formateur",
            "years_experience": 8,
            "city": "Tunis",
            "country": "Tunisie",
            "linkedin_url": None,
            "website": None,
            "summary": None,
            "skills": [],
            "languages": [],
            "certifications": [],
            "education": [],
            "experiences": [],
            "confidence": {},
            "warnings": [],
        }


class NativeText(CVTextExtractor):
    def extract(self, path: Path, mime_type: str) -> CVTextExtractionResult:
        del path, mime_type
        text = "Karim Test formateur professionnel karim@example.com Tunis Tunisie"
        return CVTextExtractionResult(text, 1, len(text))


class NeedsOCR(CVTextExtractor):
    def extract(self, path: Path, mime_type: str) -> CVTextExtractionResult:
        del path, mime_type
        raise ApiError(422, "TEXT_EXTRACTION_EMPTY", "OCR requise.")


class FakeOCR(OCRExtractor):
    def extract(self, path: Path) -> str:
        del path
        return "Karim Test formateur professionnel karim@example.com Tunis Tunisie"


def uploaded_cv(
    db_session: Session, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> TrainerCV:
    monkeypatch.setattr(settings, "cv_storage_dir", tmp_path)
    stored = f"{uuid4()}.pdf"
    (tmp_path / stored).write_bytes(b"%PDF-test")
    cv = TrainerCV(
        original_filename="cv.pdf",
        storage_filename=stored,
        mime_type="application/pdf",
        file_size=9,
        sha256=uuid4().hex.ljust(64, "0"),
    )
    db_session.add(cv)
    db_session.commit()
    db_session.refresh(cv)
    return cv


def test_strict_json_response() -> None:
    assert parse_json_response('{"ok": true}') == {"ok": True}
    with pytest.raises(ApiError) as error:
        parse_json_response('avant {"ok": true} après')
    assert error.value.code == "LLM_INVALID_RESPONSE"


class _TagsResponse:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self) -> bytes:
        return self.body


def test_ollama_health_distinguishes_missing_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.ai.local_llm.urlopen",
        lambda *args, **kwargs: _TagsResponse(b'{"models":[{"name":"other:latest"}]}'),
    )
    health = OllamaLocalLLMClient().health()
    assert health.status == "unavailable"
    assert health.reason == "LLM_MODEL_NOT_FOUND"


def test_ollama_health_distinguishes_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args, **kwargs):
        raise TimeoutError

    monkeypatch.setattr("app.ai.local_llm.urlopen", timeout)
    health = OllamaLocalLLMClient().health()
    assert health.status == "unavailable"
    assert health.reason == "LLM_TIMEOUT"


def test_native_extraction_and_human_review_without_auto_creation(
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cv = uploaded_cv(db_session, tmp_path, monkeypatch)
    result = TrainerCVExtractionService(db_session, FakeLLM(), NativeText()).extract(
        cv.id, active_administrator.id
    )
    assert result.extraction_status == TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    assert result.raw_text
    assert result.parsed_json is not None
    assert result.parsed_json["full_name"] == "Karim Test"
    assert db_session.scalar(select(Trainer)) is None


def test_ocr_is_used_only_when_native_text_is_empty(
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cv = uploaded_cv(db_session, tmp_path, monkeypatch)
    result = TrainerCVExtractionService(
        db_session, FakeLLM(), NeedsOCR(), FakeOCR()
    ).extract(cv.id, active_administrator.id)
    assert result.extraction_status == TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    assert result.raw_text


@pytest.mark.parametrize("code", ["LLM_UNAVAILABLE", "LLM_TIMEOUT", "LLM_INVALID_RESPONSE"])
def test_llm_failure_preserves_text_and_allows_manual_review_and_retry(
    code: str,
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cv = uploaded_cv(db_session, tmp_path, monkeypatch)
    failed = TrainerCVExtractionService(
        db_session, FakeLLM(ApiError(503, code, "IA indisponible.")), NativeText()
    ).extract(cv.id, active_administrator.id)
    assert failed.extraction_status == TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    assert failed.extraction_error_code == code
    assert failed.raw_text
    assert db_session.scalar(select(Trainer)) is None

    retried = TrainerCVExtractionService(db_session, FakeLLM(), NativeText()).extract(
        cv.id, active_administrator.id
    )
    assert retried.parsed_json is not None
    assert retried.parsed_json["full_name"] == "Karim Test"
    assert retried.extraction_error_code is None


def test_ocr_failure_is_manual_review_not_terminal_failure(
    db_session: Session,
    active_administrator: Administrator,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cv = uploaded_cv(db_session, tmp_path, monkeypatch)
    result = TrainerCVExtractionService(db_session, FakeLLM(), NeedsOCR()).extract(
        cv.id, active_administrator.id
    )
    assert result.extraction_status == TrainerCVExtractionStatus.REVIEW_REQUIRED.value
    assert result.extraction_error_code == "OCR_FAILED"
