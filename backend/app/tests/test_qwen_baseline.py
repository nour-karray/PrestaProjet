from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from app.synthetic_dataset.baseline import (
    BaselineGenerationConfig,
    build_prompt,
    deterministic_metrics,
    generate_case,
    parse_json_response,
)
from app.synthetic_dataset.schemas import ProgramOutput

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "evaluate_qwen_baseline.py"
SPEC = importlib.util.spec_from_file_location("evaluate_qwen_baseline", SCRIPT)
assert SPEC and SPEC.loader
SCRIPT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCRIPT_MODULE)


def baseline_case() -> dict:  # type: ignore[type-arg]
    return SCRIPT_MODULE.load_cases(ROOT / "data" / "final" / "test.jsonl")[0]


class FakeClient:
    model = "fake-qwen"

    def __init__(self, response: str | None = None, error: str | None = None) -> None:
        self.response = response
        self.error = error

    def health(self) -> None:
        return None

    def generate(self, prompt: str, config: BaselineGenerationConfig) -> str:
        if self.error:
            raise RuntimeError(self.error)
        assert self.response is not None
        return self.response


def test_prompt_contains_only_input_and_schema() -> None:
    case = baseline_case()
    prompt = build_prompt(case["input"])
    assert case["input"]["client_need"] in prompt
    assert case["output"]["general_objective"] not in prompt
    assert "cleaning" not in prompt
    assert "generation_family_id" not in prompt


def test_json_parsing_and_pydantic_validation() -> None:
    case = baseline_case()
    raw = json.dumps(case["output"], ensure_ascii=False)
    parsed = parse_json_response(f"```json\n{raw}\n```")
    assert ProgramOutput.model_validate(parsed)
    metrics = deterministic_metrics(case["input"], parsed)
    assert metrics["json_parsable"]
    assert metrics["pydantic_valid"]
    assert metrics["automatic_validation_pass"]


def test_invalid_model_response_is_a_parse_error() -> None:
    record = generate_case(
        FakeClient(response="pas du json"),
        baseline_case(),
        BaselineGenerationConfig(max_attempts=1),
    )
    assert record["generation_status"] == "PARSE_ERROR"
    assert not record["automatic_metrics"]["json_parsable"]


def test_model_error_is_recorded() -> None:
    record = generate_case(
        FakeClient(error="MODEL_UNAVAILABLE"),
        baseline_case(),
        BaselineGenerationConfig(max_attempts=1),
    )
    assert record["generation_status"] == "MODEL_ERROR"
    assert record["error"] == "MODEL_UNAVAILABLE"


def test_resume_reads_existing_records(tmp_path: Path) -> None:
    path = tmp_path / "generations.jsonl"
    records = [{"program_id": "program_0001"}, {"program_id": "program_0002"}]
    path.write_text("".join(json.dumps(item) + "\n" for item in records), encoding="utf-8")
    assert SCRIPT_MODULE.load_existing(path) == records


def test_test_dataset_is_not_modified_by_helpers() -> None:
    path = ROOT / "data" / "final" / "test.jsonl"
    before = hashlib.sha256(path.read_bytes()).digest()
    case = baseline_case()
    build_prompt(case["input"])
    deterministic_metrics(case["input"], case["output"])
    assert hashlib.sha256(path.read_bytes()).digest() == before
