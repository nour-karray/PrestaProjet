from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models.training_case import ActivityLog, TrainingCase, TrainingCaseStatus
from app.models.training_program import (
    ProgramItemType,
    TrainingProgram,
    TrainingProgramDay,
    TrainingProgramItem,
    TrainingProgramItemMethod,
)
from app.repositories.training_case import ActivityRepository, TrainingCaseRepository
from app.repositories.training_need import TrainingNeedRepository
from app.repositories.training_program import TrainingProgramRepository
from app.schemas.training_program import (
    TrainingProgramCreate,
    TrainingProgramDayCreate,
    TrainingProgramDayUpdate,
    TrainingProgramItemCreate,
    TrainingProgramItemUpdate,
    TrainingProgramResponse,
    TrainingProgramUpdate,
)


class TrainingProgramService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.cases = TrainingCaseRepository(session)
        self.needs = TrainingNeedRepository(session)
        self.programs = TrainingProgramRepository(session)
        self.activities = ActivityRepository(session)

    def get(self, case_id: UUID) -> TrainingProgramResponse:
        self._get_case(case_id)
        program = self._get_program(case_id)
        return self._response(program)

    def create(
        self,
        case_id: UUID,
        payload: TrainingProgramCreate,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case = self._get_case_for_change(case_id)
        self.ensure_creation_allowed(training_case)
        if self.programs.get_by_case(case_id) is not None:
            raise ApiError(
                409,
                "TRAINING_PROGRAM_ALREADY_EXISTS",
                "Un programme existe déjà pour ce dossier.",
            )
        program = TrainingProgram(
            training_case_id=case_id,
            title=payload.title or training_case.theme,
            general_objectives=payload.general_objectives,
            evaluation_method=payload.evaluation_method,
        )
        try:
            self.programs.add(program)
            training_case.status = TrainingCaseStatus.PROGRAMME_EN_PREPARATION.value
            self._log(administrator_id, training_case, program, "TrainingProgramCreated")
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ApiError(
                409,
                "TRAINING_PROGRAM_ALREADY_EXISTS",
                "Un programme existe déjà pour ce dossier.",
            ) from exc
        return self.get(case_id)

    def update(
        self,
        case_id: UUID,
        payload: TrainingProgramUpdate,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(program, field, value)
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramUpdated",
            {"fields": sorted(changes)},
        )
        self.session.commit()
        self.session.expire_all()
        return self.get(case_id)

    def add_day(
        self,
        case_id: UUID,
        payload: TrainingProgramDayCreate,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        position = len(program.days) + 1
        day = TrainingProgramDay(
            program=program,
            position=position,
            title=payload.title or f"Journée {position}",
        )
        self.session.add(day)
        self.session.flush()
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramDayAdded",
            {"day_id": str(day.id), "position": position},
        )
        self.session.commit()
        self.session.expire_all()
        return self.get(case_id)

    def update_day(
        self,
        case_id: UUID,
        day_id: UUID,
        payload: TrainingProgramDayUpdate,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        day = self._get_day(program.id, day_id)
        day.title = payload.title
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramDayUpdated",
            {"day_id": str(day.id)},
        )
        self.session.commit()
        return self.get(case_id)

    def remove_day(
        self, case_id: UUID, day_id: UUID, administrator_id: UUID
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        day = self._get_day(program.id, day_id)
        position = day.position
        self.session.delete(day)
        self.session.flush()
        self._normalize_days(program.id)
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramDayRemoved",
            {"day_id": str(day_id), "position": position},
        )
        self.session.commit()
        self.session.expire_all()
        return self.get(case_id)

    def move_day(
        self,
        case_id: UUID,
        day_id: UUID,
        direction: int,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        day = self._get_day(program.id, day_id)
        target_position = day.position + direction
        target = next((item for item in program.days if item.position == target_position), None)
        if target is None:
            return self._response(program)
        previous = day.position
        day.position = max(item.position for item in program.days) + 1
        self.session.flush()
        target.position = previous
        self.session.flush()
        day.position = target_position
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramDayMoved",
            {
                "day_id": str(day.id),
                "previous_position": previous,
                "new_position": target_position,
            },
        )
        self.session.commit()
        return self.get(case_id)

    def add_item(
        self,
        case_id: UUID,
        day_id: UUID,
        payload: TrainingProgramItemCreate,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        day = self._get_day(program.id, day_id)
        parent = self._validate_parent(day, payload)
        siblings = [item for item in day.items if item.parent_id == (parent.id if parent else None)]
        item = TrainingProgramItem(
            day=day,
            parent=parent,
            item_type=payload.item_type.value,
            title=payload.title,
            content=payload.content,
            theory_minutes=payload.theory_minutes,
            practice_minutes=payload.practice_minutes,
            position=len(siblings) + 1,
        )
        self._set_methods(item, payload.methods)
        self.session.add(item)
        self.session.flush()
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramItemAdded",
            {"day_id": str(day.id), "item_id": str(item.id), "type": item.item_type},
        )
        self.session.commit()
        return self.get(case_id)

    def update_item(
        self,
        case_id: UUID,
        item_id: UUID,
        payload: TrainingProgramItemUpdate,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        item = self._get_item(program.id, item_id)
        changes = payload.model_dump(exclude_unset=True)
        methods = changes.pop("methods", None)
        theory = changes.get("theory_minutes", item.theory_minutes)
        practice = changes.get("practice_minutes", item.practice_minutes)
        if item.children and (theory or practice):
            raise ApiError(
                400,
                "MODULE_WITH_CHILDREN_HAS_DIRECT_DURATION",
                "Un module contenant des sous-modules ne peut pas porter de durée directe.",
            )
        for field, value in changes.items():
            setattr(item, field, value)
        if methods is not None:
            self._set_methods(item, methods)
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramItemUpdated",
            {"item_id": str(item.id), "fields": sorted(payload.model_fields_set)},
        )
        self.session.commit()
        return self.get(case_id)

    def remove_item(
        self, case_id: UUID, item_id: UUID, administrator_id: UUID
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        item = self._get_item(program.id, item_id)
        day_id = item.training_program_day_id
        parent_id = item.parent_id
        position = item.position
        self.session.delete(item)
        self.session.flush()
        self._normalize_items(day_id, parent_id)
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramItemRemoved",
            {"item_id": str(item_id), "position": position},
        )
        self.session.commit()
        self.session.expire_all()
        return self.get(case_id)

    def move_item(
        self,
        case_id: UUID,
        item_id: UUID,
        direction: int,
        administrator_id: UUID,
    ) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        item = self._get_item(program.id, item_id)
        day = self._get_day(program.id, item.training_program_day_id)
        siblings = [sibling for sibling in day.items if sibling.parent_id == item.parent_id]
        target_position = item.position + direction
        target = next(
            (sibling for sibling in siblings if sibling.position == target_position),
            None,
        )
        if target is None:
            return self._response(program)
        previous = item.position
        item.position = max(sibling.position for sibling in siblings) + 1
        self.session.flush()
        target.position = previous
        self.session.flush()
        item.position = target_position
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramItemMoved",
            {
                "item_id": str(item.id),
                "previous_position": previous,
                "new_position": target_position,
            },
        )
        self.session.commit()
        return self.get(case_id)

    def submit(self, case_id: UUID, administrator_id: UUID) -> TrainingProgramResponse:
        training_case, program = self._editable(case_id)
        self._validate_complete(program)
        expected = self._expected_minutes(case_id)
        current = self._response(program).total_minutes
        if current != expected:
            raise ApiError(
                400,
                "PROGRAM_DURATION_MISMATCH",
                "La durée du programme ne correspond pas au besoin validé.",
                {"expected_minutes": expected, "actual_minutes": current},
            )
        program.is_submitted = True
        program.submitted_at = datetime.now(UTC)
        program.return_reason = None
        training_case.status = TrainingCaseStatus.PROGRAMME_A_VALIDER.value
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramSubmitted",
            {"new_status": training_case.status},
        )
        self.session.commit()
        return self.get(case_id)

    def return_to_preparation(
        self, case_id: UUID, reason: str, administrator_id: UUID
    ) -> TrainingProgramResponse:
        training_case = self._get_case_for_change(case_id)
        program = self._get_program(case_id, for_update=True)
        if not reason.strip():
            raise ApiError(400, "RETURN_REASON_REQUIRED", "Le motif du retour est obligatoire.")
        if training_case.status != TrainingCaseStatus.PROGRAMME_A_VALIDER.value:
            raise ApiError(
                409,
                "INVALID_TRAINING_CASE_STATUS",
                "Le programme n’est pas en attente de validation.",
            )
        if program.is_validated:
            raise ApiError(
                409,
                "TRAINING_PROGRAM_ALREADY_VALIDATED",
                "Le programme est déjà validé.",
            )
        program.is_submitted = False
        program.submitted_at = None
        program.returned_at = datetime.now(UTC)
        program.return_reason = reason.strip()
        training_case.status = TrainingCaseStatus.PROGRAMME_EN_PREPARATION.value
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramReturned",
            {"reason_provided": True, "new_status": training_case.status},
        )
        self.session.commit()
        return self.get(case_id)

    def validate(self, case_id: UUID, administrator_id: UUID) -> TrainingProgramResponse:
        training_case = self._get_case_for_change(case_id)
        program = self._get_program(case_id, for_update=True)
        if program.is_validated:
            raise ApiError(
                409,
                "TRAINING_PROGRAM_ALREADY_VALIDATED",
                "Le programme est déjà validé.",
            )
        if (
            training_case.status != TrainingCaseStatus.PROGRAMME_A_VALIDER.value
            or not program.is_submitted
        ):
            raise ApiError(
                409,
                "INVALID_TRAINING_CASE_STATUS",
                "Le programme n’est pas en attente de validation.",
            )
        self._validate_complete(program)
        expected = self._expected_minutes(case_id)
        current = self._response(program).total_minutes
        if current != expected:
            raise ApiError(
                400,
                "PROGRAM_DURATION_MISMATCH",
                "La durée du programme ne correspond plus au besoin validé.",
                {"expected_minutes": expected, "actual_minutes": current},
            )
        program.is_validated = True
        program.validated_at = datetime.now(UTC)
        training_case.status = TrainingCaseStatus.PROGRAMME_VALIDE.value
        self._log(
            administrator_id,
            training_case,
            program,
            "TrainingProgramValidated",
            {"new_status": training_case.status},
        )
        self.session.commit()
        return self.get(case_id)

    def _editable(self, case_id: UUID) -> tuple[TrainingCase, TrainingProgram]:
        training_case = self._get_case_for_change(case_id)
        program = self._get_program(case_id, for_update=True)
        if (
            training_case.status != TrainingCaseStatus.PROGRAMME_EN_PREPARATION.value
            or program.is_submitted
            or program.is_validated
        ):
            raise ApiError(
                409,
                "TRAINING_PROGRAM_NOT_EDITABLE",
                "Le programme n’est pas modifiable dans son état actuel.",
            )
        return training_case, program

    def ensure_creation_allowed(self, training_case: TrainingCase) -> None:
        if training_case.status not in {
            TrainingCaseStatus.BESOIN_COMPLETE.value,
            TrainingCaseStatus.PROGRAMME_EN_PREPARATION.value,
        }:
            raise ApiError(
                409,
                "INVALID_TRAINING_CASE_STATUS",
                "Le besoin doit être complété avant de créer le programme.",
            )
        if training_case.trainer_id is None:
            raise ApiError(409, "TRAINER_REQUIRED", "Un formateur doit être affecté.")
        need = self.needs.get_by_case(training_case.id)
        if need is None:
            raise ApiError(404, "TRAINING_NEED_NOT_FOUND", "Le besoin client est introuvable.")
        if not need.is_validated:
            raise ApiError(409, "TRAINING_NEED_NOT_VALIDATED", "Le besoin client doit être validé.")
        required = (
            need.target_audience,
            need.level,
            need.location,
            need.participant_count,
            need.delivery_mode,
            need.duration_hours,
            need.planned_days_count,
            need.objectives,
            need.desired_start_date,
            need.desired_end_date,
        )
        if any(value is None or value == "" for value in required):
            raise ApiError(
                409,
                "TRAINING_NEED_INCOMPLETE",
                "Tous les champs obligatoires du besoin doivent être renseignés.",
            )

    def _validate_parent(
        self, day: TrainingProgramDay, payload: TrainingProgramItemCreate
    ) -> TrainingProgramItem | None:
        if payload.item_type == ProgramItemType.MODULE:
            if payload.parent_id is not None:
                raise ApiError(400, "INVALID_PROGRAM_ITEM_PARENT", "Un module n’a pas de parent.")
            return None
        if payload.parent_id is None:
            raise ApiError(
                400, "INVALID_PROGRAM_ITEM_PARENT", "Un sous-module exige un module parent."
            )
        parent = next((item for item in day.items if item.id == payload.parent_id), None)
        if parent is None:
            raise ApiError(
                400,
                "INVALID_PROGRAM_ITEM_PARENT",
                "Le parent doit appartenir à la même journée.",
            )
        if parent.item_type != ProgramItemType.MODULE.value:
            raise ApiError(
                400,
                "INVALID_PROGRAM_ITEM_DEPTH",
                "Un sous-module ne peut pas contenir d’autre élément.",
            )
        if parent.theory_minutes or parent.practice_minutes:
            raise ApiError(
                400,
                "MODULE_WITH_CHILDREN_HAS_DIRECT_DURATION",
                "Retirez les durées directes du module avant d’ajouter un sous-module.",
            )
        return parent

    def _validate_complete(self, program: TrainingProgram) -> None:
        if not program.title.strip() or not (program.general_objectives or "").strip():
            self._incomplete()
        if not program.days:
            self._incomplete()
        for day in program.days:
            modules = [item for item in day.items if item.parent_id is None]
            if not modules:
                self._incomplete()
            for module in modules:
                children = [item for item in day.items if item.parent_id == module.id]
                if children and (module.theory_minutes or module.practice_minutes):
                    raise ApiError(
                        400,
                        "MODULE_WITH_CHILDREN_HAS_DIRECT_DURATION",
                        "Un module avec sous-modules ne peut pas porter de durée directe.",
                    )
                terminals = children or [module]
                for item in terminals:
                    if (
                        not item.title.strip()
                        or not (item.content or "").strip()
                        or not item.method_links
                        or item.theory_minutes + item.practice_minutes <= 0
                    ):
                        self._incomplete()

    @staticmethod
    def _incomplete() -> None:
        raise ApiError(
            400,
            "TRAINING_PROGRAM_INCOMPLETE",
            "Le programme ne respecte pas toutes les règles de complétude.",
        )

    def _response(self, program: TrainingProgram) -> TrainingProgramResponse:
        return TrainingProgramResponse.from_model(
            program, self._expected_minutes(program.training_case_id)
        )

    def _expected_minutes(self, case_id: UUID) -> int:
        need = self.needs.get_by_case(case_id)
        if need is None:
            raise ApiError(404, "TRAINING_NEED_NOT_FOUND", "Le besoin client est introuvable.")
        if not need.is_validated:
            raise ApiError(409, "TRAINING_NEED_NOT_VALIDATED", "Le besoin client doit être validé.")
        if need.duration_hours is None:
            raise ApiError(400, "TRAINING_PROGRAM_INCOMPLETE", "La durée du besoin est absente.")
        return int(
            (Decimal(need.duration_hours) * Decimal(60)).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )

    def _get_case(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        return training_case

    def _get_case_for_change(self, case_id: UUID) -> TrainingCase:
        training_case = self.cases.get_for_update(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        if training_case.is_archived:
            raise ApiError(409, "ARCHIVED_TRAINING_CASE", "Le dossier est archivé.")
        if training_case.status == TrainingCaseStatus.ANNULE.value:
            raise ApiError(409, "CANCELLED_TRAINING_CASE", "Le dossier est annulé.")
        return training_case

    def _get_program(self, case_id: UUID, *, for_update: bool = False) -> TrainingProgram:
        program = self.programs.get_by_case(case_id, for_update=for_update)
        if program is None:
            raise ApiError(404, "TRAINING_PROGRAM_NOT_FOUND", "Le programme est introuvable.")
        return program

    def _get_day(self, program_id: UUID, day_id: UUID) -> TrainingProgramDay:
        day = self.programs.get_day(program_id, day_id, for_update=True)
        if day is None:
            raise ApiError(404, "TRAINING_PROGRAM_DAY_NOT_FOUND", "La journée est introuvable.")
        return day

    def _get_item(self, program_id: UUID, item_id: UUID) -> TrainingProgramItem:
        item = self.programs.get_item(program_id, item_id, for_update=True)
        if item is None:
            raise ApiError(404, "TRAINING_PROGRAM_ITEM_NOT_FOUND", "L’élément est introuvable.")
        return item

    def _normalize_days(self, program_id: UUID) -> None:
        days = list(
            self.session.scalars(
                select(TrainingProgramDay)
                .where(TrainingProgramDay.training_program_id == program_id)
                .order_by(TrainingProgramDay.position)
            )
        )
        offset = max((day.position for day in days), default=0) + len(days)
        for index, day in enumerate(days, 1):
            day.position = offset + index
        self.session.flush()
        for index, day in enumerate(days, 1):
            day.position = index

    def _normalize_items(self, day_id: UUID, parent_id: UUID | None) -> None:
        parent_filter = (
            TrainingProgramItem.parent_id.is_(None)
            if parent_id is None
            else TrainingProgramItem.parent_id == parent_id
        )
        siblings = list(
            self.session.scalars(
                select(TrainingProgramItem)
                .where(
                    TrainingProgramItem.training_program_day_id == day_id,
                    parent_filter,
                )
                .order_by(TrainingProgramItem.position)
            )
        )
        offset = max((item.position for item in siblings), default=0) + len(siblings)
        for index, item in enumerate(siblings, 1):
            item.position = offset + index
        self.session.flush()
        for index, item in enumerate(siblings, 1):
            item.position = index

    @staticmethod
    def _set_methods(item: TrainingProgramItem, methods) -> None:
        item.method_links.clear()
        item.method_links.extend(
            TrainingProgramItemMethod(method=method.value) for method in methods
        )

    def _log(
        self,
        administrator_id: UUID,
        training_case: TrainingCase,
        program: TrainingProgram,
        action: str,
        extra: dict | None = None,
    ) -> None:
        self.activities.add(
            ActivityLog(
                administrator_id=administrator_id,
                training_case_id=training_case.id,
                action=action,
                entity_type="training_program",
                entity_id=program.id,
                details={
                    "training_case_id": str(training_case.id),
                    "training_program_id": str(program.id),
                    **(extra or {}),
                },
            )
        )
