from uuid import UUID

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.local_llm import LocalLLMClient, OllamaLocalLLMClient
from app.ai.program_context_builder import build_program_context
from app.ai.program_duration_normalizer import (
    ProgramDayCountMismatchError,
    fix_program_durations,
    validate_normalized_program,
)
from app.ai.program_generation_schemas import ProgramDraftSchema
from app.ai.program_prompt_builder import build_program_correction_prompt, build_program_prompt
from app.ai.program_quality_validator import audit_program_pedagogical_quality
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
        self.llm = llm or OllamaLocalLLMClient(settings.local_llm_timeout_seconds)

    def generate(self, case_id: UUID, administrator_id: UUID) -> TrainingProgramResponse:
        training_case = self.cases.get_for_update(case_id)
        if training_case is None:
            raise ApiError(404, "TRAINING_CASE_NOT_FOUND", "Le dossier est introuvable.")
        self.program_service.ensure_creation_allowed(training_case)
        if self.programs.get_by_case(case_id) is not None:
            raise ApiError(409, "TRAINING_PROGRAM_ALREADY_EXISTS", "Un programme existe déjà.")
        need = self.needs.get_by_case(case_id)
        context = build_program_context(training_case, need)
        if context["planned_days_count"] is None:
            raise ApiError(
                400,
                "PROGRAM_PLANNED_DAYS_MISSING",
                "Le nombre de journées planifiées doit être renseigné dans le besoin client.",
            )
        try:
            raw = self.llm.generate_structured(build_program_prompt(context), ProgramDraftSchema)
            raw = _complete_missing_terminal_content(raw)
            draft = _validate_and_normalize(raw, context)
        except ProgramDayCountMismatchError as exc:
            raise ApiError(
                422,
                "PROGRAM_DAY_COUNT_MISMATCH",
                "Le nombre de journées proposé ne correspond pas au besoin validé.",
                {"expected_days": exc.expected, "actual_days": exc.actual},
            ) from exc
        except ApiError as exc:
            if exc.code not in {"LLM_INVALID_RESPONSE", "JSON_VALIDATION_FAILED"}:
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
        except ValueError as exc:
            raise ApiError(
                422,
                "PROGRAM_DURATION_NORMALIZATION_FAILED",
                "Les durées du programme ne peuvent pas être normalisées.",
                {"reason": str(exc)},
            ) from exc

        initial_quality_issues = audit_program_pedagogical_quality(draft)
        quality_issues = initial_quality_issues
        correction_performed = bool(initial_quality_issues)
        correction_succeeded = False
        correction_error: str | None = None
        if correction_performed:
            initial_draft = draft
            try:
                corrected_raw = self.llm.generate_structured(
                    build_program_correction_prompt(draft, initial_quality_issues, context),
                    ProgramDraftSchema,
                )
                corrected_raw = _complete_missing_terminal_content(corrected_raw)
                corrected_draft = ProgramDraftSchema.model_validate(corrected_raw)
                _ensure_correction_preserves_protected_values(initial_draft, corrected_draft)
                draft = _validate_and_normalize(corrected_raw, context)
                quality_issues = audit_program_pedagogical_quality(draft)
                correction_succeeded = True
            except (ApiError, ProgramDayCountMismatchError, ValidationError, ValueError) as exc:
                draft = initial_draft
                quality_issues = initial_quality_issues
                correction_error = type(exc).__name__
        try:
            program = self._persist(training_case, draft)
            training_case.status = TrainingCaseStatus.PROGRAMME_EN_PREPARATION.value
            module_count = sum(len(day.modules) for day in draft.days)
            self.activities.add(
                ActivityLog(
                    administrator_id=administrator_id,
                    training_case_id=case_id,
                    action="TrainingProgramInitialGenerated",
                    entity_type="TrainingProgram",
                    entity_id=program.id,
                    details={
                        "model": self.llm.model_name,
                        "pedagogical_quality_issues": _serialize_quality_issues(
                            initial_quality_issues
                        ),
                    },
                )
            )
            if correction_performed:
                self.activities.add(
                    ActivityLog(
                        administrator_id=administrator_id,
                        training_case_id=case_id,
                        action="TrainingProgramPedagogicalCorrectionPerformed",
                        entity_type="TrainingProgram",
                        entity_id=program.id,
                        details={
                            "model": self.llm.model_name,
                            "correction_succeeded": correction_succeeded,
                            "correction_error": correction_error,
                            "remaining_quality_issues": _serialize_quality_issues(
                                quality_issues
                            ),
                        },
                    )
                )
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
                        "pedagogical_quality_issues": _serialize_quality_issues(quality_issues),
                    },
                )
            )
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        response = self.program_service.get(case_id)
        warning = (
            "Le programme a été généré mais certains éléments méritent une vérification "
            "pédagogique."
            if quality_issues or correction_error
            else None
        )
        return response.model_copy(
            update={
                "pedagogical_warning": warning,
                "pedagogical_correction_performed": correction_performed,
            }
        )

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


def _complete_missing_terminal_content(raw: dict) -> dict:
    """Complete only content omitted by the fine-tuned legacy output shape."""
    for day in raw.get("days", []):
        if not isinstance(day, dict):
            continue
        for module in day.get("modules", []):
            if not isinstance(module, dict) or module.get("submodules"):
                continue
            content = module.get("content")
            if isinstance(content, str) and content.strip():
                continue
            title = module.get("title")
            if isinstance(title, str) and title.strip() and module.get("methods"):
                module["content"] = f"Apports, consignes et activités du module : {title.strip()}."
    return raw


def _validate_and_normalize(raw: dict, context: dict) -> ProgramDraftSchema:
    draft = ProgramDraftSchema.model_validate(raw)
    draft = fix_program_durations(
        draft,
        total_duration_minutes=context["total_minutes"],
        planned_days_count=context["planned_days_count"],
    )
    validate_normalized_program(
        draft,
        total_duration_minutes=context["total_minutes"],
        planned_days_count=context["planned_days_count"],
    )
    return draft


def _ensure_correction_preserves_protected_values(
    initial: ProgramDraftSchema,
    corrected: ProgramDraftSchema,
) -> None:
    if (
        corrected.title != initial.title
        or corrected.general_objectives != initial.general_objectives
        or corrected.prerequisites != initial.prerequisites
    ):
        raise ValueError("La correction a modifié des métadonnées protégées.")
    if [day.position for day in corrected.days] != [day.position for day in initial.days]:
        raise ValueError("La correction a modifié le nombre ou l’ordre des journées.")
    if corrected.total_minutes != initial.total_minutes:
        raise ValueError("La correction a modifié la durée totale du programme.")
    initial_day_totals = [_draft_day_total(day) for day in initial.days]
    corrected_day_totals = [_draft_day_total(day) for day in corrected.days]
    if corrected_day_totals != initial_day_totals:
        raise ValueError("La correction a modifié la durée totale d’une journée.")


def _draft_day_total(day) -> int:
    return sum(
        sum(child.theory_minutes + child.practice_minutes for child in module.submodules)
        if module.submodules
        else module.theory_minutes + module.practice_minutes
        for module in day.modules
    )


def _serialize_quality_issues(issues) -> list[dict[str, str]]:
    return [
        {"code": issue.code, "location": issue.location, "message": issue.message}
        for issue in issues
    ]
