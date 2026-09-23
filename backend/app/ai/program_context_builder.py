from decimal import ROUND_HALF_UP, Decimal

from app.models.training_program import PedagogicalMethod


def build_program_context(training_case, need) -> dict:
    total_minutes = int(
        (Decimal(need.duration_hours) * Decimal(60)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    return {
        "theme": training_case.theme,
        "client_need": training_case.description,
        "target_audience": need.target_audience,
        "level": need.level,
        "objectives": need.objectives,
        "pedagogical_objectives": need.objectives,
        "total_minutes": total_minutes,
        "planned_days_count": need.planned_days_count,
        "delivery_mode": need.delivery_mode,
        "constraints": need.constraints,
        "location": need.location,
        "participant_count": need.participant_count,
        "trainer_profile": _trainer_profile(training_case.trainer),
        "allowed_methods": [method.value for method in PedagogicalMethod],
        "structure": "jours > modules > sous-modules (deux niveaux maximum)",
    }


def _trainer_profile(trainer) -> dict | None:
    if trainer is None:
        return None
    specialties: list[str] = []
    domains: list[str] = []
    certifications: list[str] = []
    for cv in sorted(trainer.cvs, key=lambda item: item.uploaded_at, reverse=True):
        if not isinstance(cv.parsed_json, dict):
            continue
        parsed_skills = cv.parsed_json.get("skills")
        if isinstance(parsed_skills, list):
            specialties = [
                item.strip()
                for item in parsed_skills
                if isinstance(item, str) and item.strip()
            ]
        parsed_certifications = cv.parsed_json.get("certifications")
        if isinstance(parsed_certifications, list):
            certifications = [
                item["name"].strip()
                for item in parsed_certifications
                if isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and item["name"].strip()
            ]
        parsed_experiences = cv.parsed_json.get("experiences")
        if isinstance(parsed_experiences, list):
            domains = [
                item["job_title"].strip()
                for item in parsed_experiences
                if isinstance(item, dict)
                and isinstance(item.get("job_title"), str)
                and item["job_title"].strip()
            ]
        break
    return {
        "name": trainer.full_name,
        "specialties": specialties[:20],
        "domains": domains[:20],
        "years_of_experience": trainer.years_experience,
        "certifications": certifications[:20],
    }
