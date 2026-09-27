from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.training_program import PedagogicalMethod, ProgramItemType, TrainingProgram


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class TrainingProgramCreate(BaseModel):
    title: str | None = Field(default=None, max_length=250)
    general_objectives: str | None = None
    prerequisites: str | None = None
    evaluation_method: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional(value) if isinstance(value, str) else value


class TrainingProgramUpdate(TrainingProgramCreate):
    pass


class TrainingProgramDayCreate(BaseModel):
    title: str | None = Field(default=None, max_length=250)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> object:
        return clean_optional(value) if isinstance(value, str) else value


class TrainingProgramDayUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=250)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return value.strip()


class TrainingProgramItemCreate(BaseModel):
    item_type: ProgramItemType
    parent_id: UUID | None = None
    title: str = Field(min_length=1, max_length=250)
    content: str | None = None
    theory_minutes: int = Field(default=0, ge=0)
    practice_minutes: int = Field(default=0, ge=0)
    methods: list[PedagogicalMethod] = Field(default_factory=list)

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("content", mode="before")
    @classmethod
    def clean_content(cls, value: object) -> object:
        return clean_optional(value) if isinstance(value, str) else value

    @field_validator("methods")
    @classmethod
    def unique_methods(cls, values: list[PedagogicalMethod]) -> list[PedagogicalMethod]:
        if len(values) != len(set(values)):
            raise ValueError("Une méthode pédagogique ne peut apparaître qu’une fois.")
        return values


class TrainingProgramItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    content: str | None = None
    theory_minutes: int | None = Field(default=None, ge=0)
    practice_minutes: int | None = Field(default=None, ge=0)
    methods: list[PedagogicalMethod] | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("content", mode="before")
    @classmethod
    def clean_content(cls, value: object) -> object:
        return clean_optional(value) if isinstance(value, str) else value

    @field_validator("methods")
    @classmethod
    def unique_methods(
        cls, values: list[PedagogicalMethod] | None
    ) -> list[PedagogicalMethod] | None:
        if values is not None and len(values) != len(set(values)):
            raise ValueError("Une méthode pédagogique ne peut apparaître qu’une fois.")
        return values


class TrainingProgramReturnRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator("reason", mode="before")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return value.strip()


class TrainingProgramItemResponse(BaseModel):
    id: UUID
    item_type: ProgramItemType
    parent_id: UUID | None
    title: str
    content: str | None
    theory_minutes: int
    practice_minutes: int
    theory_total_minutes: int
    practice_total_minutes: int
    total_minutes: int
    position: int
    methods: list[PedagogicalMethod]
    children: list["TrainingProgramItemResponse"]


class TrainingProgramDayResponse(BaseModel):
    id: UUID
    title: str
    position: int
    theory_total_minutes: int
    practice_total_minutes: int
    total_minutes: int
    items: list[TrainingProgramItemResponse]


class TrainingProgramResponse(BaseModel):
    id: UUID
    training_case_id: UUID
    title: str
    general_objectives: str | None
    prerequisites: str | None
    evaluation_method: str | None
    is_submitted: bool
    submitted_at: datetime | None
    is_validated: bool
    validated_at: datetime | None
    returned_at: datetime | None
    return_reason: str | None
    created_at: datetime
    updated_at: datetime
    expected_total_minutes: int
    theory_total_minutes: int
    practice_total_minutes: int
    total_minutes: int
    days: list[TrainingProgramDayResponse]
    pedagogical_warning: str | None = None
    pedagogical_correction_performed: bool = False

    @classmethod
    def from_model(
        cls, program: TrainingProgram, expected_total_minutes: int
    ) -> "TrainingProgramResponse":
        days = []
        for day in sorted(program.days, key=lambda value: value.position):
            roots = sorted(
                (item for item in day.items if item.parent_id is None),
                key=lambda value: value.position,
            )
            item_responses = [_item_response(item, day.items) for item in roots]
            theory = sum(item.theory_total_minutes for item in item_responses)
            practice = sum(item.practice_total_minutes for item in item_responses)
            days.append(
                TrainingProgramDayResponse(
                    id=day.id,
                    title=day.title,
                    position=day.position,
                    theory_total_minutes=theory,
                    practice_total_minutes=practice,
                    total_minutes=theory + practice,
                    items=item_responses,
                )
            )
        theory = sum(day.theory_total_minutes for day in days)
        practice = sum(day.practice_total_minutes for day in days)
        return cls(
            id=program.id,
            training_case_id=program.training_case_id,
            title=program.title,
            general_objectives=program.general_objectives,
            prerequisites=program.prerequisites,
            evaluation_method=program.evaluation_method,
            is_submitted=program.is_submitted,
            submitted_at=program.submitted_at,
            is_validated=program.is_validated,
            validated_at=program.validated_at,
            returned_at=program.returned_at,
            return_reason=program.return_reason,
            created_at=program.created_at,
            updated_at=program.updated_at,
            expected_total_minutes=expected_total_minutes,
            theory_total_minutes=theory,
            practice_total_minutes=practice,
            total_minutes=theory + practice,
            days=days,
        )


def _item_response(item, all_items) -> TrainingProgramItemResponse:
    children = sorted(
        (candidate for candidate in all_items if candidate.parent_id == item.id),
        key=lambda value: value.position,
    )
    child_responses = [_item_response(child, all_items) for child in children]
    theory = (
        sum(child.theory_total_minutes for child in child_responses)
        if child_responses
        else item.theory_minutes
    )
    practice = (
        sum(child.practice_total_minutes for child in child_responses)
        if child_responses
        else item.practice_minutes
    )
    return TrainingProgramItemResponse(
        id=item.id,
        item_type=item.item_type,
        parent_id=item.parent_id,
        title=item.title,
        content=item.content,
        theory_minutes=item.theory_minutes,
        practice_minutes=item.practice_minutes,
        theory_total_minutes=theory,
        practice_total_minutes=practice,
        total_minutes=theory + practice,
        position=item.position,
        methods=[link.method for link in item.method_links],
        children=child_responses,
    )
