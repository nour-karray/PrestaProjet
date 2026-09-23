from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class TrainingLevel(StrEnum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class TrainerProfile(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    specialties: list[str] = Field(min_length=1, max_length=8)
    years_of_experience: int = Field(ge=0, le=60)


class TrainingProgramInput(StrictModel):
    training_name: str = Field(min_length=2, max_length=200)
    client_need: str = Field(min_length=5, max_length=1_000)
    target_audience: str = Field(min_length=2, max_length=400)
    level: TrainingLevel
    total_duration_minutes: int = Field(gt=0, le=3_000)
    planned_days_count: int = Field(ge=1, le=10)
    delivery_mode: str = Field(min_length=2, max_length=100)
    location: str = Field(min_length=2, max_length=160)
    trainer_profile: TrainerProfile


class ProgramContent(StrictModel):
    title: str = Field(min_length=2, max_length=200)
    concepts: list[str] = Field(min_length=1, max_length=15)


class ProgramTrainer(StrictModel):
    name: str = Field(min_length=2, max_length=160)
    hours: float = Field(gt=0, le=500)


class TrainingProgramDay(StrictModel):
    day_number: int = Field(ge=1, le=10)
    title: str = Field(min_length=2, max_length=200)
    contents: list[ProgramContent] = Field(min_length=1, max_length=8)
    methods_and_resources: list[str] = Field(min_length=1, max_length=12)
    theory_minutes: int = Field(ge=0, le=840)
    practice_minutes: int = Field(ge=0, le=840)

    @model_validator(mode="after")
    def duration_is_positive(self) -> TrainingProgramDay:
        if self.theory_minutes + self.practice_minutes <= 0:
            raise ValueError("Une journée doit avoir une durée positive.")
        return self


class TrainingProgramOutput(StrictModel):
    theme: str = Field(min_length=2, max_length=200)
    target_audience: str = Field(min_length=2, max_length=400)
    training_objectives: list[str] = Field(min_length=1, max_length=12)
    pedagogical_objectives: list[str] = Field(min_length=1, max_length=15)
    trainer: ProgramTrainer
    days: list[TrainingProgramDay] = Field(min_length=1, max_length=10)
    total_duration_minutes: int = Field(gt=0, le=3_000)
    evaluation_method: str = Field(min_length=5, max_length=800)

    @model_validator(mode="after")
    def validate_internal_totals(self) -> TrainingProgramOutput:
        numbers = [day.day_number for day in self.days]
        if numbers != list(range(1, len(self.days) + 1)):
            raise ValueError("Les journées doivent être ordonnées et numérotées sans rupture.")
        total = sum(day.theory_minutes + day.practice_minutes for day in self.days)
        if total != self.total_duration_minutes:
            raise ValueError("La somme des journées ne correspond pas à la durée totale.")
        if abs(self.trainer.hours * 60 - self.total_duration_minutes) > 0.01:
            raise ValueError("Les heures du formateur ne correspondent pas à la durée totale.")
        return self

    def validate_against(self, source: TrainingProgramInput) -> None:
        if len(self.days) != source.planned_days_count:
            raise ValueError("Le nombre de journées ne correspond pas au besoin.")
        if self.total_duration_minutes != source.total_duration_minutes:
            raise ValueError("La durée totale ne correspond pas au besoin.")
        if self.target_audience.casefold() != source.target_audience.casefold():
            raise ValueError("Le public cible ne correspond pas au besoin.")
        if self.trainer.name.casefold() != source.trainer_profile.name.casefold():
            raise ValueError("Le formateur ne correspond pas au profil sélectionné.")
