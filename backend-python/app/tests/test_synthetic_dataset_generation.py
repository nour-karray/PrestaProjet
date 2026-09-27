from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from app.synthetic_dataset.v3 import (
    V3ProgramBlueprint,
    build_v3_output,
    pedagogical_violations,
    regenerate_v3,
)
from app.tests.test_synthetic_dataset import valid_example


def blueprint(example, marker: str = "A") -> dict[str, Any]:  # type: ignore[no-untyped-def]
    days = []
    total_days = example.input.planned_days_count
    day_duration = example.input.total_duration_minutes // total_days
    module_count = 3 if day_duration >= 420 else 2
    for day_index in range(total_days):
        days.append(
            {
                "title": f"{marker} cadrage métier {day_index}",
                "objective": f"Analyser le contexte professionnel avancé {marker} {day_index}",
                "pedagogical_function": "Cadrage" if day_index == 0 else "Application",
                "modules": [
                    {
                        "title": f"{marker} diagnostic {day_index}-{module_index}",
                        "description": (
                            "Approfondir une situation complexe "
                            f"{marker} {day_index}-{module_index}"
                        ),
                        "concepts": ["analyse avancée", f"audit {marker} {module_index}"],
                        "pedagogical_objective": (
                            f"Évaluer un scénario complexe {marker} {day_index}-{module_index}"
                        ),
                        "activities": [f"Audit guidé {marker} {module_index}"],
                        "module_type": "THEORY" if module_index == 0 else "PRACTICE",
                    }
                    for module_index in range(module_count)
                ],
            }
        )
    return {
        "title": f"Programme avancé {marker}",
        "general_objective": f"Piloter une démarche complexe et mesurable {marker}",
        "pedagogical_objectives": [
            f"Diagnostiquer les risques {marker}",
            f"Optimiser les décisions {marker}",
            f"Auditer les résultats {marker}",
        ],
        "prerequisites": ["Maîtriser les fondamentaux du domaine"],
        "evaluation_method": f"Audit argumenté et soutenance finale {marker}",
        "final_deliverable": f"Rapport d'audit opérationnel {marker}",
        "days": days,
    }


class FakeV3Client:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls = 0

    def generate(self, example, variant_index, forbidden_summary, correction=None):  # type: ignore[no-untyped-def]
        del variant_index, forbidden_summary, correction
        value = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(value, Exception):
            raise value
        if callable(value):
            return value(example, f"V{self.calls}")
        return value


def test_v1_program_is_flagged_for_long_single_module() -> None:
    reasons = pedagogical_violations(valid_example())
    assert "DAY_HAS_FEWER_THAN_TWO_MODULES" in reasons
    assert "SINGLE_MODULE_LONG_DAY" not in reasons  # the fixture lasts only three hours


def test_python_allocates_duration_without_creating_modules() -> None:
    example = valid_example()
    raw = blueprint(example)
    output = build_v3_output(V3ProgramBlueprint.model_validate(raw), example)
    assert len(output.days[0].modules) == len(raw["days"][0]["modules"])
    assert sum(module.duration_minutes for module in output.days[0].modules) == 180


def test_regeneration_preserves_identifiers_and_saves_progressively(tmp_path: Path) -> None:
    original = valid_example()
    output = tmp_path / "v3.jsonl"
    examples, stats, _ = regenerate_v3(
        [original], output, FakeV3Client([blueprint]), max_retries=1
    )
    assert examples[0].id == original.id
    assert examples[0].generation_family_id == original.generation_family_id
    assert examples[0].metadata.diversity_revision == 3
    assert stats.calls == 1
    assert output.exists() and output.with_suffix(".json").exists()


def test_rejection_is_retried_with_an_independent_call(tmp_path: Path) -> None:
    original = valid_example()
    invalid = blueprint(original)
    invalid["days"][0]["modules"] = invalid["days"][0]["modules"][:1]
    client = FakeV3Client([invalid, blueprint])
    examples, stats, _ = regenerate_v3(
        [original], tmp_path / "v3.jsonl", client, max_retries=2
    )
    assert len(examples) == 1
    assert client.calls == 2
    assert stats.rejected == 1


def test_ollama_unavailable_aborts_without_corrupting_source(tmp_path: Path) -> None:
    original = valid_example()
    source_snapshot = original.model_dump_json()
    with pytest.raises(RuntimeError, match="V3_ABORTED"):
        regenerate_v3(
            [original],
            tmp_path / "v3.jsonl",
            FakeV3Client([RuntimeError("LLM_UNAVAILABLE")]),
            max_retries=0,
        )
    assert original.model_dump_json() == source_snapshot
