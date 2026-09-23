from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.training_program import PedagogicalMethod


class DraftBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def clean_strings(cls, value):
        return " ".join(value.split()) if isinstance(value, str) else value


class ProgramSubmoduleDraftSchema(DraftBase):
    title: str = Field(min_length=1, max_length=250)
    content: str = Field(min_length=1, max_length=4000)
    position: int = Field(ge=1)
    theory_minutes: int = Field(default=0, ge=0)
    practice_minutes: int = Field(default=0, ge=0)
    methods: list[PedagogicalMethod] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_methods(self):
        self.methods = list(dict.fromkeys(self.methods))
        return self


class ProgramModuleDraftSchema(DraftBase):
    title: str = Field(min_length=1, max_length=250)
    content: str | None = Field(default=None, max_length=4000)
    position: int = Field(ge=1)
    theory_minutes: int = Field(default=0, ge=0)
    practice_minutes: int = Field(default=0, ge=0)
    methods: list[PedagogicalMethod] = Field(default_factory=list)
    submodules: list[ProgramSubmoduleDraftSchema] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_terminal(self):
        if self.submodules:
            if self.theory_minutes or self.practice_minutes or self.methods:
                raise ValueError("Un module avec sous-modules ne porte pas de durée ni de méthode.")
            _unique_positions(self.submodules)
        elif not (self.content or "").strip() or not self.methods:
            raise ValueError("Un module terminal doit être complet.")
        self.methods = list(dict.fromkeys(self.methods))
        return self


class ProgramDayDraftSchema(DraftBase):
    title: str = Field(min_length=1, max_length=250)
    position: int = Field(ge=1)
    modules: list[ProgramModuleDraftSchema] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_positions(self):
        _unique_positions(self.modules)
        return self


class ProgramDraftSchema(DraftBase):
    title: str = Field(min_length=1, max_length=250)
    general_objectives: str = Field(min_length=1, max_length=4000)
    prerequisites: str | None = Field(default=None, max_length=2000)
    evaluation_method: str = Field(min_length=1, max_length=2000)
    days: list[ProgramDayDraftSchema] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_positions(self):
        _unique_positions(self.days)
        return self

    @property
    def total_minutes(self) -> int:
        total = 0
        for day in self.days:
            for module in day.modules:
                if module.submodules:
                    total += sum(
                        item.theory_minutes + item.practice_minutes for item in module.submodules
                    )
                else:
                    total += module.theory_minutes + module.practice_minutes
        return total


def _unique_positions(items) -> None:
    positions = [item.position for item in items]
    if len(positions) != len(set(positions)):
        raise ValueError("Les positions doivent être uniques.")
