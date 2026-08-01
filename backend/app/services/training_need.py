from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.training_case import ActivityLog, TrainingCaseStatus
from app.models.training_need import TrainingNeed
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.repositories.training_need import TrainingNeedRepository
from app.schemas.training_need import TrainingNeedCreate, TrainingNeedUpdate


class TrainingNeedService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.needs = TrainingNeedRepository(session)
        self.cases = TrainingCaseRepository(session)
        self.activities = ActivityRepository(session)

    def get(self, case_id: UUID) -> TrainingNeed:
        self._get_case(case_id)
        need = self.needs.get_by_case(case_id)
        if need is None:
            raise ApiError(404, "TRAINING_NEED_NOT_FOUND", "Le besoin client est introuvable.")
        return need

    def create(
        self,
        case_id: UUID,
        payload: TrainingNeedCreate,
        administrator_id: UUID,
    ) -> TrainingNeed:
        training_case = self._get_case_for_change(case_id)
        self._ensure_case_allows_need(training_case)
        if self.needs.get_by_case(case_id) is not None:
            raise ApiError(
                409,
                "TRAINING_NEED_ALREADY_EXISTS",
                "Un besoin client existe déjà pour ce dossier.",
            )
        self._validate_period(payload.desired_start_date, payload.desired_end_date)
        need = TrainingNeed(training_case_id=case_id, **payload.model_dump(mode="python"))
        try:
            self.needs.add(need)
            previous_status = training_case.status
            if previous_status in {
                TrainingCaseStatus.DEMANDE_RECUE.value,
                TrainingCaseStatus.FORMATEUR_ACCEPTE.value,
            }:
                training_case.status = TrainingCaseStatus.BESOIN_A_COMPLETER.value
            self._log(
                administrator_id,
                case_id,
                need.id,
                "TrainingNeedCreated",
                previous_status,
                training_case.status,
            )
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ApiError(
                409,
                "TRAINING_NEED_ALREADY_EXISTS",
                "Un besoin client existe déjà pour ce dossier.",
            ) from exc
        self.session.refresh(need)
        return need

    def update(
        self,
        case_id: UUID,
        payload: TrainingNeedUpdate,
        administrator_id: UUID,
    ) -> TrainingNeed:
        training_case = self._get_case_for_change(case_id)
        need = self.needs.get_by_case(case_id, for_update=True)
        if need is None:
            raise ApiError(404, "TRAINING_NEED_NOT_FOUND", "Le besoin client est introuvable.")
        if need.is_validated:
            raise ApiError(
                409,
                "TRAINING_NEED_ALREADY_VALIDATED",
                "Un besoin validé ne peut plus être modifié.",
            )
        self._ensure_case_allows_need(training_case)
        changes = payload.model_dump(exclude_unset=True, mode="python")
        start = changes.get("desired_start_date", need.desired_start_date)
        end = changes.get("desired_end_date", need.desired_end_date)
        self._validate_period(start, end)
        for field, value in changes.items():
            setattr(need, field, value)
        self._log(
            administrator_id,
            case_id,
            need.id,
            "TrainingNeedUpdated",
            training_case.status,
            training_case.status,
            {"fields": sorted(changes)},
        )
        self.session.commit()
        self.session.refresh(need)
        return need

    def validate(self, case_id: UUID, administrator_id: UUID) -> TrainingNeed:
        training_case = self._get_case_for_change(case_id)
        need = self.needs.get_by_case(case_id, for_update=True)
        if need is None:
            raise ApiError(404, "TRAINING_NEED_NOT_FOUND", "Le besoin client est introuvable.")
        if need.is_validated:
            raise ApiError(
                409,
                "TRAINING_NEED_ALREADY_VALIDATED",
                "Ce besoin client est déjà validé.",
            )
        if training_case.status != TrainingCaseStatus.BESOIN_A_COMPLETER.value:
            raise ApiError(
                409,
                "INVALID_TRAINING_CASE_STATUS",
                "Le dossier n’est pas à l’étape de validation du besoin.",
            )
        self._validate_complete(need)
        previous_status = training_case.status
        need.is_validated = True
        need.validated_at = datetime.now(UTC)
        training_case.status = TrainingCaseStatus.BESOIN_COMPLETE.value
        self._log(
            administrator_id,
            case_id,
            need.id,
            "TrainingNeedValidated",
            previous_status,
            training_case.status,
        )
        self.session.commit()
        self.session.refresh(need)
        return need

    def _get_case(self, case_id: UUID):
        training_case = self.cases.get(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        return training_case

    def _get_case_for_change(self, case_id: UUID):
        training_case = self.cases.get_for_update(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        if training_case.is_archived:
            raise ApiError(
                409, "ARCHIVED_TRAINING_CASE", "Un dossier archivé ne peut pas être modifié."
            )
        if training_case.status == TrainingCaseStatus.ANNULE.value:
            raise ApiError(
                409, "CANCELLED_TRAINING_CASE", "Un dossier annulé ne peut pas être modifié."
            )
        return training_case

    @staticmethod
    def _ensure_case_allows_need(training_case) -> None:
        if False and training_case.trainer_id is None:
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté au dossier.")
        if training_case.status not in {
            TrainingCaseStatus.DEMANDE_RECUE.value,
            TrainingCaseStatus.FORMATEUR_ACCEPTE.value,
            TrainingCaseStatus.BESOIN_A_COMPLETER.value,
        }:
            raise ApiError(
                409,
                "INVALID_TRAINING_CASE_STATUS",
                "Le besoin client n’est pas accessible à cette étape du dossier.",
            )

    @staticmethod
    def _validate_period(start, end) -> None:
        if start and end and end < start:
            raise ApiError(
                400,
                "INVALID_TRAINING_NEED_PERIOD",
                "La date de fin doit être postérieure ou égale à la date de début.",
            )

    def _validate_complete(self, need: TrainingNeed) -> None:
        required = (
            need.target_audience,
            need.location,
            need.participant_count,
            need.delivery_mode,
            need.duration_hours,
            need.objectives,
            need.desired_start_date,
            need.desired_end_date,
        )
        if any(value is None or value == "" for value in required):
            raise ApiError(
                400,
                "TRAINING_NEED_INCOMPLETE",
                "Tous les champs obligatoires du besoin doivent être renseignés.",
            )
        self._validate_period(need.desired_start_date, need.desired_end_date)

    def _log(
        self,
        administrator_id: UUID,
        case_id: UUID,
        need_id: UUID,
        action: str,
        previous_status: str,
        next_status: str,
        extra: dict | None = None,
    ) -> None:
        details = {
            "training_case_id": str(case_id),
            "training_need_id": str(need_id),
            "previous_status": previous_status,
            "new_status": next_status,
            **(extra or {}),
        }
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                training_case_id=case_id,
                action=action,
                entity_type="training_need",
                entity_id=need_id,
                details=details,
            )
        )
