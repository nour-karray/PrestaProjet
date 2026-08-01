from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.company import Company
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.repositories.company import ContactRepository
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.schemas.training_case import TrainingCaseCreate, TrainingCaseUpdate

ALLOWED_TRANSITIONS = {
    TrainingCaseStatus.BROUILLON: {TrainingCaseStatus.DEMANDE_RECUE},
    TrainingCaseStatus.DEMANDE_RECUE: {
        TrainingCaseStatus.BESOIN_A_COMPLETER,
        TrainingCaseStatus.RECHERCHE_FORMATEUR,
    },
    TrainingCaseStatus.BESOIN_COMPLETE: {TrainingCaseStatus.RECHERCHE_FORMATEUR},
    TrainingCaseStatus.RECHERCHE_FORMATEUR: {TrainingCaseStatus.FORMATEUR_PROPOSE},
    TrainingCaseStatus.FORMATEUR_PROPOSE: {TrainingCaseStatus.FORMATEUR_ACCEPTE},
    TrainingCaseStatus.FORMATEUR_ACCEPTE: {
        TrainingCaseStatus.BESOIN_A_COMPLETER,
        TrainingCaseStatus.PROGRAMME_EN_PREPARATION,
    },
}
CANCELLABLE_STATUSES = {
    TrainingCaseStatus.BROUILLON,
    TrainingCaseStatus.DEMANDE_RECUE,
    TrainingCaseStatus.RECHERCHE_FORMATEUR,
}


class TrainingCaseService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.cases = TrainingCaseRepository(session)
        self.activities = ActivityRepository(session)

    def get(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        return training_case

    def create(
        self,
        payload: TrainingCaseCreate,
        administrator_id: UUID,
        *,
        created_at: datetime | None = None,
    ) -> TrainingCase:
        self._validate_company_and_contact(
            payload.company_id, payload.primary_contact_id, require_active=True
        )
        now = created_at or datetime.now(UTC)
        training_case = TrainingCase(
            reference=self.cases.next_reference(now.year),
            created_by=administrator_id,
            created_at=now,
            **payload.model_dump(),
        )
        self.cases.add(training_case)
        self._log(training_case, administrator_id, "CREATION", {})
        self.session.commit()
        return self.get(training_case.id)

    def update(
        self,
        case_id: UUID,
        payload: TrainingCaseUpdate,
        administrator_id: UUID,
    ) -> TrainingCase:
        training_case = self.get(case_id)
        self._ensure_editable(training_case)
        changes = payload.model_dump(exclude_unset=True)
        company_id = changes.get("company_id", training_case.company_id)
        contact_id = changes.get("primary_contact_id", training_case.primary_contact_id)
        self._validate_company_and_contact(company_id, contact_id, require_active=True)
        start = changes.get("desired_start_date", training_case.desired_start_date)
        end = changes.get("desired_end_date", training_case.desired_end_date)
        if start and end and end < start:
            raise ApiError(
                422,
                "INVALID_DATE_RANGE",
                "La date de fin ne peut pas précéder la date de début.",
            )
        for field, value in changes.items():
            setattr(training_case, field, value)
        self._log(training_case, administrator_id, "MODIFICATION", {"fields": list(changes)})
        self.session.commit()
        return self.get(case_id)

    def change_status(
        self,
        case_id: UUID,
        target: TrainingCaseStatus,
        administrator_id: UUID,
    ) -> TrainingCase:
        training_case = self.get(case_id)
        current = TrainingCaseStatus(training_case.status)
        if (
            target
            in {
                TrainingCaseStatus.FORMATEUR_PROPOSE,
                TrainingCaseStatus.FORMATEUR_ACCEPTE,
            }
            and training_case.trainer_id is None
        ):
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté au dossier.")
        if target not in ALLOWED_TRANSITIONS.get(current, set()):
            raise ApiError(
                409,
                "INVALID_STATUS_TRANSITION",
                f"Transition de {current.value} vers {target.value} non autorisée.",
            )
        action = {
            TrainingCaseStatus.FORMATEUR_PROPOSE: "TrainerProposed",
            TrainingCaseStatus.FORMATEUR_ACCEPTE: "TrainerAccepted",
        }.get(target, "CHANGEMENT_STATUT")
        self._set_status(training_case, target, administrator_id, action)
        return self.get(case_id)

    def cancel(self, case_id: UUID, administrator_id: UUID) -> TrainingCase:
        training_case = self.get(case_id)
        current = TrainingCaseStatus(training_case.status)
        if current not in CANCELLABLE_STATUSES:
            raise ApiError(409, "CASE_NOT_CANCELLABLE", "Ce dossier ne peut pas être annulé.")
        self._set_status(training_case, TrainingCaseStatus.ANNULE, administrator_id, "ANNULATION")
        return self.get(case_id)

    def close(self, case_id: UUID, administrator_id: UUID) -> TrainingCase:
        training_case = self.get(case_id)
        if training_case.status != TrainingCaseStatus.DOCUMENTS_GENERES.value:
            raise ApiError(409, "CASE_NOT_CLOSABLE", "Ce dossier ne peut pas être clôturé.")
        training_case.closed_at = datetime.now(UTC)
        self._set_status(training_case, TrainingCaseStatus.TERMINE, administrator_id, "CLOTURE")
        return self.get(case_id)

    def archive(self, case_id: UUID, administrator_id: UUID) -> TrainingCase:
        training_case = self.get(case_id)
        if TrainingCaseStatus(training_case.status) not in {
            TrainingCaseStatus.TERMINE,
            TrainingCaseStatus.ANNULE,
        }:
            raise ApiError(
                409, "CASE_NOT_ARCHIVABLE", "Seul un dossier terminé ou annulé peut être archivé."
            )
        training_case.status = TrainingCaseStatus.ARCHIVE.value
        training_case.is_archived = True
        self._log(training_case, administrator_id, "ARCHIVAGE", {})
        self.session.commit()
        return self.get(case_id)

    def _set_status(
        self,
        training_case: TrainingCase,
        target: TrainingCaseStatus,
        administrator_id: UUID,
        action: str,
    ) -> None:
        previous = training_case.status
        training_case.status = target.value
        self._log(
            training_case,
            administrator_id,
            action,
            {"previous_status": previous, "new_status": target.value},
        )
        self.session.commit()

    def _validate_company_and_contact(
        self, company_id: UUID, contact_id: UUID | None, *, require_active: bool
    ) -> None:
        company = self.session.get(Company, company_id)
        if company is None:
            raise ApiError(404, "COMPANY_NOT_FOUND", "L’entreprise est introuvable.")
        if require_active and company.is_archived:
            raise ApiError(
                409,
                "COMPANY_ARCHIVED",
                "Une entreprise archivée ne peut pas être associée à un nouveau dossier.",
            )
        if contact_id is None:
            return
        contact = ContactRepository(self.session).get(contact_id)
        if contact is None:
            raise ApiError(404, "CONTACT_NOT_FOUND", "Le contact est introuvable.")
        if contact.company_id != company_id:
            raise ApiError(
                409,
                "CONTACT_COMPANY_MISMATCH",
                "Le contact n’appartient pas à l’entreprise sélectionnée.",
            )

    @staticmethod
    def _ensure_editable(training_case: TrainingCase) -> None:
        if training_case.is_archived:
            raise ApiError(409, "CASE_ARCHIVED", "Un dossier archivé ne peut plus être modifié.")

    def _log(
        self,
        training_case: TrainingCase,
        administrator_id: UUID,
        action: str,
        details: dict,
    ) -> None:
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                training_case_id=training_case.id,
                action=action,
                entity_type="training_case",
                entity_id=training_case.id,
                details=details,
            )
        )
