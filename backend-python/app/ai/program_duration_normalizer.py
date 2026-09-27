from __future__ import annotations

from app.ai.program_generation_schemas import (
    ProgramDraftSchema,
    ProgramModuleDraftSchema,
    ProgramSubmoduleDraftSchema,
)

TerminalDraft = ProgramModuleDraftSchema | ProgramSubmoduleDraftSchema


class ProgramDayCountMismatchError(ValueError):
    def __init__(self, expected: int, actual: int) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"Nombre de journées invalide : {actual} au lieu de {expected}.")


def fix_program_durations(
    program: ProgramDraftSchema,
    *,
    total_duration_minutes: int,
    planned_days_count: int,
) -> ProgramDraftSchema:
    """Normalize duration fields using the validated user need as the source of truth."""
    if total_duration_minutes <= 0:
        raise ValueError("La durée totale doit être strictement positive.")
    if planned_days_count <= 0:
        raise ValueError("Le nombre de journées doit être strictement positif.")
    if len(program.days) != planned_days_count:
        raise ProgramDayCountMismatchError(planned_days_count, len(program.days))

    normalized = program.model_copy(deep=True)
    base_duration, remainder = divmod(total_duration_minutes, planned_days_count)
    day_durations = [
        base_duration + (1 if index < remainder else 0) for index in range(planned_days_count)
    ]

    for day, target_duration in zip(normalized.days, day_durations, strict=True):
        terminals = _terminal_items(day.modules)
        allocations = _allocate_exact(
            target_duration,
            [item.theory_minutes + item.practice_minutes for item in terminals],
        )
        for item, allocated in zip(terminals, allocations, strict=True):
            original_total = item.theory_minutes + item.practice_minutes
            if original_total == 0:
                theory = allocated // 2
            else:
                theory = (allocated * item.theory_minutes + original_total // 2) // original_total
            theory = min(max(theory, 0), allocated)
            item.theory_minutes = theory
            item.practice_minutes = allocated - theory

    if normalized.total_minutes != total_duration_minutes:
        raise RuntimeError("La normalisation n'a pas produit la durée totale attendue.")
    return normalized


def validate_normalized_program(
    program: ProgramDraftSchema,
    *,
    total_duration_minutes: int,
    planned_days_count: int,
) -> None:
    if len(program.days) != planned_days_count:
        raise ProgramDayCountMismatchError(planned_days_count, len(program.days))
    if program.total_minutes != total_duration_minutes:
        raise ValueError("La somme des durées ne correspond pas au besoin validé.")
    for day in program.days:
        for item in _terminal_items(day.modules):
            if item.theory_minutes < 0 or item.practice_minutes < 0:
                raise ValueError("Une durée normalisée ne peut pas être négative.")
            if item.theory_minutes + item.practice_minutes <= 0:
                raise ValueError("Chaque élément terminal doit conserver une durée positive.")


def _terminal_items(modules: list[ProgramModuleDraftSchema]) -> list[TerminalDraft]:
    terminals: list[TerminalDraft] = []
    for module in modules:
        terminals.extend(module.submodules or [module])
    if not terminals:
        raise ValueError("Une journée doit contenir au moins un élément terminal.")
    return terminals


def _allocate_exact(total: int, weights: list[int]) -> list[int]:
    """Allocate an integer total proportionally, with at least one minute per item."""
    if total < len(weights):
        raise ValueError("La journée est trop courte pour attribuer une minute à chaque élément.")
    remaining = total - len(weights)
    positive_weight = sum(weights)
    if positive_weight == 0:
        quotient, remainder = divmod(remaining, len(weights))
        return [1 + quotient + (1 if index < remainder else 0) for index in range(len(weights))]

    raw_numerators = [remaining * weight for weight in weights]
    shares = [value // positive_weight for value in raw_numerators]
    remainder = remaining - sum(shares)
    order = sorted(
        range(len(weights)),
        key=lambda index: (-(raw_numerators[index] % positive_weight), index),
    )
    for index in order[:remainder]:
        shares[index] += 1
    return [share + 1 for share in shares]
