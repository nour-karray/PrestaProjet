from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.local_llm import LocalLLMClient, OllamaLocalLLMClient
from app.ai.program_context_builder import build_program_context
from app.ai.program_generation_schemas import ProgramDraftSchema
from app.ai.program_prompt_builder import build_program_prompt
from app.core.config import settings
from app.core.errors import ApiError
from app.models.training_case import ActivityLog, TrainingCaseStatus
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
from app.schemas.training_program import TrainingProgramResponse
from app.services.training_program import TrainingProgramService


class ProgramGenerationService:
    def __init__(self, session: Session, llm: LocalLLMClient | None = None) -> None:
        self.session = session
        self.cases = TrainingCaseRepository(session)
        self.needs = TrainingNeedRepository(session)
        self.programs = TrainingProgramRepository(session)
        self.activities = ActivityRepository(session)
        self.program_service = TrainingProgramService(session)
        self.llm = llm or OllamaLocalLLMClient(settings.program_generation_timeout_seconds)

    def generate(self, case_id: UUID, administrator_id: UUID) -> TrainingProgramResponse:
        training_case = self.cases.get_for_update(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        self.program_service.ensure_creation_allowed(training_case)
        if self.programs.get_by_case(case_id) is not None:
            raise ApiError(409, "TRAINING_PROGRAM_ALREADY_EXISTS", "Un programme existe déjà.")
        need = self.needs.get_by_case(case_id)
        context = build_program_context(training_case, need)
        try:
            raw = self.llm.generate_structured(build_program_prompt(context), ProgramDraftSchema)
            draft = ProgramDraftSchema.model_validate(raw)
        except ApiError as exc:
            if exc.status_code != 502:
                raise
            raise ApiError(
                502,
                "PROGRAM_GENERATION_INVALID_RESPONSE",
                "Ollama n’a pas produit un programme valide. Aucun brouillon n’a été créé.",
            ) from exc
        except ValidationError as exc:
            raise ApiError(
                502,
                "PROGRAM_GENERATION_INVALID_RESPONSE",
                "Ollama n’a pas produit un programme valide. Aucun brouillon n’a été créé.",
            ) from exc
        if draft.total_minutes != context["total_minutes"]:
            raise ApiError(
                422,
                "PROGRAM_DURATION_MISMATCH",
                "La durée proposée par Ollama ne correspond pas au besoin validé.",
                {
                    "expected_minutes": context["total_minutes"],
                    "actual_minutes": draft.total_minutes,
                },
            )
        try:
            program = self._persist(training_case, draft)
            training_case.status = TrainingCaseStatus.PROGRAMME_EN_PREPARATION.value
            module_count = sum(len(day.modules) for day in draft.days)
            self.activities.add(
                ActivityLog(
                    administrator_id=administrator_id,
                    training_case_id=case_id,
                    action="TrainingProgramDraftGenerated",
                    entity_type="TrainingProgram",
                    entity_id=program.id,
                    details={
                        "model": self.llm.model_name,
                        "day_count": len(draft.days),
                        "module_count": module_count,
                        "duration_minutes": draft.total_minutes,
                    },
                )
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return self.program_service.get(case_id)

    def _persist(self, training_case, draft: ProgramDraftSchema) -> TrainingProgram:
        program = TrainingProgram(
            training_case_id=training_case.id,
            title=draft.title,
            general_objectives=draft.general_objectives,
            prerequisites=draft.prerequisites or "Aucun prérequis particulier.",
            evaluation_method=draft.evaluation_method,
        )
        self.session.add(program)
        for day_data in sorted(draft.days, key=lambda item: item.position):
            day = TrainingProgramDay(title=day_data.title, position=day_data.position)
            program.days.append(day)
            for module_data in sorted(day_data.modules, key=lambda item: item.position):
                module = TrainingProgramItem(
                    item_type=ProgramItemType.MODULE.value,
                    title=module_data.title,
                    content=module_data.content,
                    theory_minutes=module_data.theory_minutes,
                    practice_minutes=module_data.practice_minutes,
                    position=module_data.position,
                )
                module.method_links = [
                    TrainingProgramItemMethod(method=method.value) for method in module_data.methods
                ]
                day.items.append(module)
                for child_data in sorted(module_data.submodules, key=lambda item: item.position):
                    child = TrainingProgramItem(
                        item_type=ProgramItemType.SUBMODULE.value,
                        title=child_data.title,
                        content=child_data.content,
                        theory_minutes=child_data.theory_minutes,
                        practice_minutes=child_data.practice_minutes,
                        position=child_data.position,
                        method_links=[
                            TrainingProgramItemMethod(method=method.value)
                            for method in child_data.methods
                        ],
                    )
                    module.children.append(child)
                    day.items.append(child)
        self.session.flush()
        return program
