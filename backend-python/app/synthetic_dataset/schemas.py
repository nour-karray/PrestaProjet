from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ModuleType(StrEnum):
    THEORY = "THEORY"
    PRACTICE = "PRACTICE"


class PedagogicalStyle(StrEnum):
    ACADEMIC = "academic"
    PRACTICAL = "practical"
    BUSINESS = "business"
    CERTIFICATION = "certification"
    INTENSIVE_WORKSHOP = "intensive_workshop"
    BLENDED_LEARNING = "blended_learning"
    BEGINNER = "beginner"
    ADVANCED = "advanced"


class DifficultyLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class DeliveryMode(StrEnum):
    IN_PERSON = "in_person"
    REMOTE = "remote"
    HYBRID = "hybrid"


class SyntheticTrainerProfile(StrictModel):
    specialties: list[str] = Field(min_length=1, max_length=8)
    domains: list[str] = Field(min_length=1, max_length=8)
    years_of_experience: int = Field(ge=1, le=40)
    certifications: list[str] = Field(default_factory=list, max_length=8)


class SyntheticProgramInput(StrictModel):
    theme: str = Field(min_length=2, max_length=160)
    client_need: str = Field(min_length=10, max_length=800)
    sector: str = Field(min_length=2, max_length=120)
    target_audience: str = Field(min_length=2, max_length=300)
    level: DifficultyLevel
    participant_count: int = Field(ge=1, le=100)
    total_duration_minutes: int = Field(gt=0, le=3_000)
    planned_days_count: int = Field(ge=1, le=10)
    delivery_mode: DeliveryMode
    location: str = Field(min_length=2, max_length=150)
    constraints: list[str] = Field(default_factory=list, max_length=10)
    trainer_profile: SyntheticTrainerProfile


class ProgramModule(StrictModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = Field(min_length=10, max_length=800)
    concepts: list[str] = Field(min_length=1, max_length=12)
    duration_minutes: int = Field(gt=0, le=600)
    module_type: ModuleType
    pedagogical_methods: list[str] = Field(min_length=1, max_length=8)
    pedagogical_resources: list[str] = Field(min_length=1, max_length=8)
    pedagogical_objective: str = Field(min_length=8, max_length=500)
    activities: list[str] = Field(default_factory=list, max_length=8)


class ProgramDay(StrictModel):
    day_number: int = Field(ge=1, le=10)
    title: str = Field(min_length=2, max_length=180)
    objective: str = Field(min_length=8, max_length=500)
    modules: list[ProgramModule] = Field(min_length=1, max_length=12)
    pedagogical_function: str | None = Field(default=None, min_length=3, max_length=180)


class ProgramOutput(StrictModel):
    title: str = Field(min_length=2, max_length=200)
    general_objective: str = Field(min_length=10, max_length=1_000)
    pedagogical_objectives: list[str] = Field(min_length=2, max_length=12)
    target_audience: str = Field(min_length=2, max_length=300)
    prerequisites: list[str] = Field(min_length=1, max_length=10)
    teaching_methods: list[str] = Field(min_length=1, max_length=10)
    pedagogical_resources: list[str] = Field(min_length=1, max_length=10)
    evaluation_method: str = Field(min_length=5, max_length=800)
    days: list[ProgramDay] = Field(min_length=1, max_length=10)
    final_deliverable: str | None = Field(default=None, min_length=3, max_length=400)


class CleaningMetadata(StrictModel):
    modified: bool
    issues_detected: list[str] = Field(default_factory=list)
    changes_summary: list[str] = Field(default_factory=list)


class ProgramMetadata(StrictModel):
    source: str = Field(pattern="^synthetic$")
    style: PedagogicalStyle
    difficulty: DifficultyLevel
    domain: str = Field(min_length=2, max_length=120)
    validated_by_rules: bool
    diversity_revision: int | None = Field(default=None, ge=1)
    previous_version: str | None = Field(default=None, max_length=80)
    generation_method: str | None = Field(default=None, max_length=120)
    qwen_attempt_count: int | None = Field(default=None, ge=1, le=4)
    regenerated_at: datetime | None = None
    cleaning: CleaningMetadata | None = None


class SyntheticProgramExample(StrictModel):
    id: str = Field(pattern=r"^program_\d{4}$")
    generation_family_id: str = Field(pattern=r"^theme_[a-z0-9_]+_\d{3}$")
    input: SyntheticProgramInput
    output: ProgramOutput
    metadata: ProgramMetadata

    @model_validator(mode="after")
    def validate_program_coherence(self) -> SyntheticProgramExample:
        if len(self.output.days) != self.input.planned_days_count:
            raise ValueError("Le nombre de journées ne correspond pas à l’entrée.")
        numbers = [day.day_number for day in self.output.days]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError("Les journées doivent être numérotées et ordonnées sans doublon.")
        duration = sum(
            module.duration_minutes for day in self.output.days for module in day.modules
        )
        if duration != self.input.total_duration_minutes:
            raise ValueError("La somme des modules ne correspond pas à la durée totale.")
        if self.output.target_audience.casefold() != self.input.target_audience.casefold():
            raise ValueError("Le public cible de sortie doit correspondre à l’entrée.")
        if not self.metadata.validated_by_rules:
            raise ValueError("L’exemple doit être validé par les règles.")
        return self
