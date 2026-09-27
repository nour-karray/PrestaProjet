from __future__ import annotations

import pytest

from app.ai.program_duration_normalizer import (
    ProgramDayCountMismatchError,
    fix_program_durations,
    validate_normalized_program,
)
from app.ai.program_generation_schemas import ProgramDraftSchema


def make_draft(
    day_count: int,
    *,
    theory: int = 600,
    practice: int = 150,
    omit_durations: bool = False,
) -> ProgramDraftSchema:
    days = []
    for index in range(day_count):
        module = {
            "title": f"Module {index + 1}",
            "content": "Contenu pédagogique conservé.",
            "position": 1,
            "methods": ["EXPOSE"],
            "submodules": [],
        }
        if not omit_durations:
            module |= {"theory_minutes": theory, "practice_minutes": practice}
        days.append(
            {
                "title": f"Journée {index + 1}",
                "position": index + 1,
                "modules": [module],
            }
        )
    return ProgramDraftSchema.model_validate(
        {
            "title": "Programme test",
            "general_objectives": "Objectifs inchangés.",
            "prerequisites": "Aucun.",
            "evaluation_method": "Évaluation finale.",
            "days": days,
        }
    )


def test_five_days_are_normalized_to_exactly_2100_minutes() -> None:
    result = fix_program_durations(make_draft(5), total_duration_minutes=2100, planned_days_count=5)
    assert result.total_minutes == 2100
    assert [
        sum(item.theory_minutes + item.practice_minutes for item in day.modules)
        for day in result.days
    ] == [420, 420, 420, 420, 420]
    assert [
        (day.modules[0].theory_minutes, day.modules[0].practice_minutes) for day in result.days
    ] == [
        (336, 84),
    ] * 5


def test_non_divisible_duration_distributes_remainder_without_loss() -> None:
    result = fix_program_durations(make_draft(3), total_duration_minutes=1000, planned_days_count=3)
    totals = [
        sum(item.theory_minutes + item.practice_minutes for item in day.modules)
        for day in result.days
    ]
    assert totals == [334, 333, 333]
    assert sum(totals) == 1000


def test_missing_or_zero_durations_use_a_balanced_default() -> None:
    result = fix_program_durations(
        make_draft(1, omit_durations=True),
        total_duration_minutes=421,
        planned_days_count=1,
    )
    module = result.days[0].modules[0]
    assert module.theory_minutes == 210
    assert module.practice_minutes == 211


def test_day_count_mismatch_does_not_invent_days() -> None:
    draft = make_draft(1)
    with pytest.raises(ProgramDayCountMismatchError) as raised:
        fix_program_durations(draft, total_duration_minutes=2100, planned_days_count=5)
    assert raised.value.expected == 5
    assert raised.value.actual == 1
    assert len(draft.days) == 1


def test_normalization_never_creates_negative_minutes() -> None:
    result = fix_program_durations(
        make_draft(3, theory=0, practice=700),
        total_duration_minutes=1000,
        planned_days_count=3,
    )
    validate_normalized_program(result, total_duration_minutes=1000, planned_days_count=3)
    assert all(
        item.theory_minutes >= 0 and item.practice_minutes >= 0
        for day in result.days
        for item in day.modules
    )


def test_normalization_changes_only_duration_fields() -> None:
    draft = make_draft(1)
    result = fix_program_durations(draft, total_duration_minutes=420, planned_days_count=1)
    before = draft.model_dump()
    after = result.model_dump()
    before_module = before["days"][0]["modules"][0]
    after_module = after["days"][0]["modules"][0]
    before_module.pop("theory_minutes")
    before_module.pop("practice_minutes")
    after_module.pop("theory_minutes")
    after_module.pop("practice_minutes")
    assert after == before
