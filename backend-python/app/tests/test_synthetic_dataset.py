from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from app.synthetic_dataset.generator import (
    GenerationStats,
    OllamaProgramClient,
    build_input,
    build_specs,
    generate_dataset,
    save_datasets,
    split_duration,
    write_quality_report,
)
from app.synthetic_dataset.pdf_preview import create_program_pdf
from app.synthetic_dataset.review import build_review_queue, family_analysis
from app.synthetic_dataset.schemas import (
    ProgramMetadata,
    ProgramOutput,
    SyntheticProgramExample,
)
from app.synthetic_dataset.validation import DuplicateRegistry, load_jsonl, validate_collection


def valid_output(input_data) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    durations = split_duration(input_data.total_duration_minutes, input_data.planned_days_count)
    return {
        "title": f"Maîtriser {input_data.theme}",
        "general_objective": (
            "Appliquer une démarche structurée dans des situations professionnelles."
        ),
        "pedagogical_objectives": [
            "Expliquer les concepts essentiels du domaine.",
            "Mettre en œuvre une méthode adaptée au contexte métier.",
        ],
        "target_audience": input_data.target_audience,
        "prerequisites": ["Connaître son environnement professionnel"],
        "teaching_methods": ["Étude de cas", "Exercice guidé"],
        "pedagogical_resources": ["Support synthétique", "Fiche outil"],
        "evaluation_method": "Quiz initial, observation des exercices et étude de cas finale.",
        "days": [
            {
                "day_number": number,
                "title": f"Progression {number}",
                "objective": f"Développer la compétence professionnelle de niveau {number}.",
                "modules": [
                    {
                        "title": f"Module opérationnel {number}",
                        "description": (
                            "Séquence synthétique combinant apports et application au poste."
                        ),
                        "concepts": ["repères", "méthode", "mise en application"],
                        "duration_minutes": duration,
                        "module_type": "THEORY" if number % 2 else "PRACTICE",
                        "pedagogical_methods": ["analyse guidée"],
                        "pedagogical_resources": ["fiche pratique"],
                        "pedagogical_objective": (
                            "Réaliser une application cohérente dans un cas synthétique."
                        ),
                    }
                ],
            }
            for number, duration in enumerate(durations, 1)
        ],
    }


def valid_example(identifier: str = "program_0001") -> SyntheticProgramExample:
    spec = build_specs(1)[0]
    input_data = build_input(spec, 0, __import__("random").Random(1))
    return SyntheticProgramExample(
        id=identifier,
        generation_family_id="theme_ressources_humaines_001",
        input=input_data,
        output=ProgramOutput.model_validate(valid_output(input_data)),
        metadata=ProgramMetadata(
            source="synthetic",
            style=spec.style,
            difficulty=spec.level,
            domain=spec.theme,
            validated_by_rules=True,
        ),
    )


def test_valid_schema_and_collection() -> None:
    example = valid_example()
    assert validate_collection([example])["valid_examples"] == 1


def test_invalid_schema_forbids_extra_field() -> None:
    payload = valid_example().model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        SyntheticProgramExample.model_validate(payload)


def test_incorrect_duration_is_rejected() -> None:
    payload = valid_example().model_dump(mode="json")
    payload["output"]["days"][0]["modules"][0]["duration_minutes"] += 1
    with pytest.raises(ValidationError, match="durée totale"):
        SyntheticProgramExample.model_validate(payload)


@pytest.mark.parametrize("mutation", ["empty_day", "empty_module", "invalid_type"])
def test_invalid_day_module_and_type(mutation: str) -> None:
    payload = valid_example().model_dump(mode="json")
    module = payload["output"]["days"][0]["modules"][0]
    if mutation == "empty_day":
        payload["output"]["days"] = []
    elif mutation == "empty_module":
        payload["output"]["days"][0]["modules"] = []
    else:
        module["module_type"] = "LECTURE"
    with pytest.raises(ValidationError):
        SyntheticProgramExample.model_validate(payload)


def test_exact_and_quasi_duplicates() -> None:
    first = valid_example("program_0001")
    duplicate = first.model_copy(update={"id": "program_0002"})
    registry = DuplicateRegistry(quasi_threshold=0.80)
    registry.add(first)
    exact, quasi = registry.inspect(duplicate)
    assert exact is True
    assert quasi and quasi[0][0] == first.id


def test_review_queue_is_pending_and_family_is_shared() -> None:
    first = valid_example("program_0001")
    second = valid_example("program_0002")
    analyses = family_analysis([first, second])
    queue = build_review_queue([first, second], analyses)
    assert {item.review_status for item in queue} == {"PENDING"}
    assert len({item.generation_family_id for item in queue}) == 1
    assert all(0 <= item.scores.global_score <= 10 for item in queue)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls = 0

    def generate(self, input_data, style, correction=None):  # type: ignore[no-untyped-def]
        del style, correction
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        if response == "valid":
            return valid_output(input_data)
        if response == "bad-duration":
            output = valid_output(input_data)
            output["days"][0]["modules"][0]["duration_minutes"] += 15
            return output
        return response


def test_regeneration_and_jsonl_save(tmp_path: Path) -> None:
    output = tmp_path / "programs.jsonl"
    examples, stats, _ = generate_dataset(
        count=1,
        output=output,
        max_retries=2,
        client=FakeClient([RuntimeError("LLM_INVALID_JSON"), "valid"]),
    )
    assert len(examples) == 1
    assert stats.regenerations == 1
    assert output.exists() and output.with_suffix(".json").exists()
    assert load_jsonl(output)[0].id == "program_0001"


@pytest.mark.parametrize("error", [RuntimeError("LLM_UNAVAILABLE"), RuntimeError("LLM_TIMEOUT")])
def test_ollama_failure_and_timeout_are_rejected(tmp_path: Path, error: RuntimeError) -> None:
    with pytest.raises(RuntimeError, match="Impossible de générer"):
        generate_dataset(
            count=1,
            output=tmp_path / "failed.jsonl",
            max_retries=0,
            client=FakeClient([error]),
        )


def test_invalid_json_response(monkeypatch: pytest.MonkeyPatch) -> None:
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"message": {"content": "not-json"}}).encode()

    monkeypatch.setattr(
        "app.synthetic_dataset.generator.urlopen", lambda *args, **kwargs: Response()
    )
    spec = build_specs(1)[0]
    input_data = build_input(spec, 0, __import__("random").Random(1))
    with pytest.raises(RuntimeError, match="LLM_INVALID_JSON"):
        OllamaProgramClient().generate(input_data, spec.style)


def test_save_report_and_synthetic_pdf(tmp_path: Path) -> None:
    example = valid_example()
    jsonl = tmp_path / "dataset.jsonl"
    save_datasets([example], jsonl)
    report = tmp_path / "report.md"
    write_quality_report([example], GenerationStats(requested=1, generated=1), report)
    pdf = create_program_pdf(example, tmp_path / "preview.pdf")
    assert "Exemples valides" in report.read_text(encoding="utf-8")
    assert pdf.exists() and pdf.stat().st_size > 1_000
