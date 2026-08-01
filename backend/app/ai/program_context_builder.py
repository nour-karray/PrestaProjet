from decimal import ROUND_HALF_UP, Decimal

from app.models.training_program import PedagogicalMethod


def build_program_context(training_case, need) -> dict:
    total_minutes = int(
        (Decimal(need.duration_hours) * Decimal(60)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )
    return {
        "theme": training_case.theme,
        "target_audience": need.target_audience,
        "objectives": need.objectives,
        "total_minutes": total_minutes,
        "delivery_mode": need.delivery_mode,
        "constraints": need.constraints,
        "location": need.location,
        "participant_count": need.participant_count,
        "allowed_methods": [method.value for method in PedagogicalMethod],
        "structure": "jours > modules > sous-modules (deux niveaux maximum)",
    }
