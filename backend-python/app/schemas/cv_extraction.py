from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.company import clean_optional_text, validate_local_email


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        def normalize(item: object) -> object:
            if isinstance(item, str):
                cleaned = " ".join(item.split())
                return cleaned or None
            if isinstance(item, list):
                return [normalize(child) for child in item]
            if isinstance(item, dict):
                return {key: normalize(child) for key, child in item.items()}
            return item

        return normalize(value)


class TrainerExperience(StrictSchema):
    job_title: str | None = Field(default=None, max_length=250)
    company: str | None = Field(default=None, max_length=250)
    location: str | None = Field(default=None, max_length=250)
    start_date: str | None = Field(default=None, max_length=100)
    end_date: str | None = Field(default=None, max_length=100)
    is_current: bool = False
    description: str | None = Field(default=None, max_length=2000)


class TrainerEducation(StrictSchema):
    degree: str | None = Field(default=None, max_length=250)
    field_of_study: str | None = Field(default=None, max_length=250)
    institution: str | None = Field(default=None, max_length=250)
    location: str | None = Field(default=None, max_length=250)
    start_date: str | None = Field(default=None, max_length=100)
    end_date: str | None = Field(default=None, max_length=100)


class TrainerCertification(StrictSchema):
    name: str | None = Field(default=None, max_length=250)
    issuer: str | None = Field(default=None, max_length=250)
    issue_date: str | None = Field(default=None, max_length=100)
    expiration_date: str | None = Field(default=None, max_length=100)


class TrainerLanguage(StrictSchema):
    name: str = Field(min_length=1, max_length=100)
    level: str | None = Field(default=None, max_length=100)


class TrainerCVExtractionResult(StrictSchema):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    full_name: str | None = Field(default=None, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=100)
    mobile_phone: str | None = Field(default=None, max_length=100)
    birth_date: str | None = Field(default=None, max_length=50)
    birth_place: str | None = Field(default=None, max_length=150)
    address: str | None = Field(default=None, max_length=300)
    company: str | None = Field(default=None, max_length=250)
    employer_address: str | None = Field(default=None, max_length=300)
    job_title: str | None = Field(default=None, max_length=250)
    years_experience: float | None = Field(default=None, ge=0, le=100)
    city: str | None = Field(default=None, max_length=150)
    country: str | None = Field(default=None, max_length=150)
    linkedin_url: str | None = Field(default=None, max_length=500)
    website: str | None = Field(default=None, max_length=500)
    summary: str | None = Field(default=None, max_length=3000)
    skills: list[str] = Field(default_factory=list, max_length=200)
    languages: list[TrainerLanguage] = Field(default_factory=list, max_length=50)
    certifications: list[TrainerCertification] = Field(default_factory=list, max_length=100)
    education: list[TrainerEducation] = Field(default_factory=list, max_length=100)
    experiences: list[TrainerExperience] = Field(default_factory=list, max_length=100)
    confidence: dict[str, float] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list, max_length=100)

    @field_validator(
        "first_name",
        "last_name",
        "full_name",
        "phone",
        "mobile_phone",
        "birth_date",
        "birth_place",
        "address",
        "company",
        "employer_address",
        "job_title",
        "city",
        "country",
        "linkedin_url",
        "website",
        "summary",
        mode="before",
    )
    @classmethod
    def clean_text(cls, value: object) -> object:
        return clean_optional_text(value) if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: object) -> object:
        return validate_local_email(value) if isinstance(value, str | type(None)) else value

    @field_validator("skills", "warnings", mode="before")
    @classmethod
    def clean_unique_strings(cls, values: list[object]) -> list[str]:
        result: list[str] = []
        for value in values:
            if not isinstance(value, str):
                continue
            cleaned = " ".join(value.split())
            if cleaned and cleaned not in result:
                result.append(cleaned[:500])
        return result

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, values: dict[str, float]) -> dict[str, float]:
        if any(value < 0 or value > 1 for value in values.values()):
            raise ValueError("Les scores de confiance doivent être compris entre 0 et 1.")
        return values

    @field_validator("experiences")
    @classmethod
    def unique_experiences(cls, values: list[TrainerExperience]) -> list[TrainerExperience]:
        result: list[TrainerExperience] = []
        seen: set[str] = set()
        for value in values:
            key = value.model_dump_json()
            if key not in seen:
                seen.add(key)
                result.append(value)
        return result
