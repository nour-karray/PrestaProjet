import time
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.local_llm import LocalLLMClient, OllamaLocalLLMClient
from app.core.errors import ApiError
from app.models.trainer import Trainer, TrainerCV, TrainerCVExtractionStatus
from app.models.training_case import ActivityLog, TrainingCase
from app.repositories.trainer import CVRepository, TrainerRepository
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.schemas.trainer import TrainerCreate, TrainerUpdate
from app.services.cv_ocr import OCRExtractor, OptionalOCRExtractor
from app.services.cv_text_extractor import CVTextExtractor
from app.services.trainer_cv_extractor import TrainerCVExtractor, extract_labeled_identity
from app.storage.cv import CVStorageService, validate_cv_file


class TrainerService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.trainers = TrainerRepository(session)
        self.activities = ActivityRepository(session)

    def get(self, trainer_id: UUID) -> Trainer:
        trainer = self.trainers.get(trainer_id)
        if trainer is None:
            raise ApiError(404, "TRAINER_NOT_FOUND", "Le formateur est introuvable.")
        return trainer

    def create(self, payload: TrainerCreate, administrator_id: UUID) -> Trainer:
        trainer = Trainer(**payload.model_dump())
        self.trainers.add(trainer)
        self._log(administrator_id, "TrainerCreated", "trainer", trainer.id)
        self.session.commit()
        self.session.refresh(trainer)
        return trainer

    def update(self, trainer_id: UUID, payload: TrainerUpdate) -> Trainer:
        trainer = self.get(trainer_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(trainer, field, value)
        self.session.commit()
        self.session.refresh(trainer)
        return trainer

    def archive(self, trainer_id: UUID, administrator_id: UUID) -> Trainer:
        trainer = self.get(trainer_id)
        trainer.is_active = False
        self._log(administrator_id, "TrainerArchived", "trainer", trainer.id)
        self.session.commit()
        self.session.refresh(trainer)
        return trainer

    def assign_to_case(
        self, case_id: UUID, trainer_id: UUID | None, administrator_id: UUID
    ) -> TrainingCase:
        training_case = TrainingCaseRepository(self.session).get(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        if training_case.is_archived:
            raise ApiError(409, "CASE_ARCHIVED", "Un dossier archivé ne peut plus être modifié.")
        trainer = self.get(trainer_id) if trainer_id else None
        if trainer is not None and not trainer.is_active:
            raise ApiError(409, "TRAINER_INACTIVE", "Ce formateur est inactif.")
        training_case.trainer = trainer
        self._log(
            administrator_id,
            "TrainerAssigned" if trainer else "TrainerUnassigned",
            "training_case",
            training_case.id,
            training_case.id,
            {"trainer_id": str(trainer.id) if trainer else None},
        )
        self.session.commit()
        refreshed = TrainingCaseRepository(self.session).get(case_id)
        if refreshed is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        return refreshed

    def _log(
        self,
        administrator_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
        training_case_id: UUID | None = None,
        details: dict | None = None,
    ) -> None:
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                training_case_id=training_case_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details or {},
            )
        )


class CVService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.cvs = CVRepository(session)
        self.storage = CVStorageService()
        self.activities = ActivityRepository(session)

    def get(self, cv_id: UUID) -> TrainerCV:
        cv = self.cvs.get(cv_id)
        if cv is None:
            raise ApiError(404, "CV_NOT_FOUND", "Le CV est introuvable.")
        return cv

    def upload(
        self, filename: str | None, mime_type: str, content: bytes, administrator_id: UUID
    ) -> TrainerCV:
        extension = validate_cv_file(filename, mime_type, content)
        digest = self.storage.compute_sha256(content)
        if self.cvs.get_by_hash(digest) is not None:
            raise ApiError(409, "CV_ALREADY_EXISTS", "Ce CV a déjà été importé.")
        storage_filename = self.storage.save(content, extension)
        try:
            cv = TrainerCV(
                original_filename=filename or "",
                storage_filename=storage_filename,
                mime_type=mime_type,
                file_size=len(content),
                sha256=digest,
            )
            self.cvs.add(cv)
            self.activities.add(
                ActivityLog(
                    administrator_id=administrator_id,
                    action="CVUploaded",
                    entity_type="trainer_cv",
                    entity_id=cv.id,
                    details={"sha256": digest},
                )
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            self.storage.delete(storage_filename)
            raise
        self.session.refresh(cv)
        return cv

    def delete(self, cv_id: UUID, administrator_id: UUID) -> None:
        cv = self.get(cv_id)
        self.storage.delete(cv.storage_filename)
        self.cvs.delete(cv)
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                action="CVDeleted",
                entity_type="trainer_cv",
                entity_id=cv.id,
                details={"storage_filename": cv.storage_filename},
            )
        )
        self.session.commit()

    def validate(self, cv_id: UUID, payload: TrainerCreate, administrator_id: UUID) -> Trainer:
        cv = self.get(cv_id)
        if cv.extraction_status not in {
            TrainerCVExtractionStatus.REVIEW_REQUIRED.value,
            TrainerCVExtractionStatus.AI_ANALYSIS_COMPLETED.value,
        }:
            raise ApiError(409, "CV_NOT_READY", "Le CV doit d’abord être vérifié manuellement.")
        trainer = Trainer(**payload.model_dump())
        TrainerRepository(self.session).add(trainer)
        cv.trainer = trainer
        cv.extraction_status = TrainerCVExtractionStatus.VALIDATED.value
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                action="TrainerCreated",
                entity_type="trainer",
                entity_id=trainer.id,
                details={"source": "validated_cv", "cv_id": str(cv.id)},
            )
        )
        self.session.commit()
        self.session.refresh(trainer)
        return trainer


class TrainerCVExtractionService:
    def __init__(
        self,
        session: Session,
        llm_client: LocalLLMClient | None = None,
        text_extractor: CVTextExtractor | None = None,
        ocr_extractor: OCRExtractor | None = None,
    ) -> None:
        self.session = session
        self.cvs = CVRepository(session)
        self.storage = CVStorageService()
        self.llm_client = llm_client or OllamaLocalLLMClient()
        self.text_extractor = text_extractor or CVTextExtractor()
        self.ocr_extractor = ocr_extractor or OptionalOCRExtractor()

    def extract(self, cv_id: UUID, administrator_id: UUID) -> TrainerCV:
        cv = self.cvs.get(cv_id)
        if cv is None:
            raise ApiError(404, "CV_NOT_FOUND", "Le CV est introuvable.")
        if cv.extraction_status == TrainerCVExtractionStatus.VALIDATED.value:
            raise ApiError(409, "CV_ALREADY_VALIDATED", "Ce CV est déjà validé.")
        started = time.perf_counter()
        path = self.storage.get_path(cv.storage_filename)
        if not self.storage.exists(cv.storage_filename):
            return self._review(cv, "FILE_INVALID", "Le fichier du CV est introuvable.", started)

        raw_text = cv.raw_text
        if not raw_text:
            try:
                raw_text = self.text_extractor.extract(path, cv.mime_type).text
                self._save_state(cv, TrainerCVExtractionStatus.TEXT_EXTRACTED, raw_text)
            except ApiError as exc:
                if exc.code != "TEXT_EXTRACTION_EMPTY":
                    return self._failed(cv, exc, started)
                self._save_state(cv, TrainerCVExtractionStatus.OCR_REQUIRED)
                try:
                    raw_text = self.ocr_extractor.extract(path)
                    if not raw_text.strip():
                        raise ApiError(422, "OCR_FAILED", "L’OCR n’a extrait aucun texte.")
                    self._save_state(cv, TrainerCVExtractionStatus.OCR_COMPLETED, raw_text)
                except ApiError as ocr_error:
                    return self._review(cv, ocr_error.code, ocr_error.message, started)
            except Exception:
                return self._failed(
                    cv,
                    ApiError(500, "TEXT_EXTRACTION_EMPTY", "L’extraction du texte a échoué."),
                    started,
                )

        labeled_identity = extract_labeled_identity(raw_text)
        if labeled_identity.full_name and (
            labeled_identity.email
            or labeled_identity.phone
            or labeled_identity.mobile_phone
        ):
            cv.parsed_json = labeled_identity.model_dump(mode="json")
            cv.extraction_model = "extraction-déterministe"
            self._save_state(cv, TrainerCVExtractionStatus.AI_ANALYSIS_COMPLETED, raw_text)
            return self._review(cv, None, None, started, raw_text)

        self._save_state(cv, TrainerCVExtractionStatus.AI_ANALYSIS_PENDING, raw_text)
        try:
            parsed = TrainerCVExtractor(self.llm_client).extract(raw_text)
        except ApiError as exc:
            return self._review(cv, exc.code, exc.message, started, raw_text)
        except Exception:
            return self._review(
                cv,
                "LLM_INVALID_RESPONSE",
                "L’analyse automatique a retourné une réponse inexploitable.",
                started,
                raw_text,
            )
        cv.parsed_json = parsed.model_dump(mode="json")
        cv.extraction_model = self.llm_client.model_name
        self._save_state(cv, TrainerCVExtractionStatus.AI_ANALYSIS_COMPLETED, raw_text)
        return self._review(cv, None, None, started, raw_text)

    def _save_state(
        self, cv: TrainerCV, status: TrainerCVExtractionStatus, raw_text: str | None = None
    ) -> None:
        cv.extraction_status = status.value
        if raw_text is not None:
            cv.raw_text = raw_text
        self.session.commit()
        self.session.refresh(cv)

    def _review(
        self,
        cv: TrainerCV,
        code: str | None,
        message: str | None,
        started: float,
        raw_text: str | None = None,
    ) -> TrainerCV:
        cv.raw_text = raw_text or cv.raw_text
        cv.extraction_status = TrainerCVExtractionStatus.REVIEW_REQUIRED.value
        cv.extraction_error_code = code
        cv.extraction_error = message
        cv.extraction_duration_ms = int((time.perf_counter() - started) * 1000)
        cv.extraction_model = cv.extraction_model or self.llm_client.model_name
        self.session.commit()
        self.session.refresh(cv)
        return cv

    def _failed(self, cv: TrainerCV, error: ApiError, started: float) -> TrainerCV:
        cv.extraction_status = TrainerCVExtractionStatus.FAILED.value
        cv.extraction_error_code = error.code
        cv.extraction_error = error.message
        cv.extraction_duration_ms = int((time.perf_counter() - started) * 1000)
        self.session.commit()
        self.session.refresh(cv)
        return cv
