from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from app.schemas.program_document import TrainingProgramOutput

ROOT = Path(__file__).resolve().parents[3]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_cleaned_dataset_is_valid_and_preserves_protected_fields() -> None:
    source = load_jsonl(ROOT / "data/training_programs_final.jsonl")
    cleaned = load_jsonl(ROOT / "data/training_programs_final_v2.jsonl")
    assert len(cleaned) == len(source) == 120
    assert len({row["id"] for row in cleaned}) == 120
    for before, after in zip(source, cleaned, strict=True):
        assert after["id"] == before["id"]
        assert after["generation_family_id"] == before["generation_family_id"]
        assert after["input"] == before["input"]
        assert after["metadata"] == before["metadata"]
        program = TrainingProgramOutput.model_validate(after["output"])
        assert program.total_duration_minutes == before["output"]["total_duration_minutes"]
        assert len(program.days) == len(before["output"]["days"])
        for old_day, day in zip(before["output"]["days"], after["output"]["days"], strict=True):
            assert (day["theory_minutes"], day["practice_minutes"]) == (
                old_day["theory_minutes"],
                old_day["practice_minutes"],
            )


def test_cleaned_dataset_removes_named_artificial_patterns() -> None:
    text = (ROOT / "data/training_programs_final_v2.jsonl").read_text(encoding="utf-8")
    output_text = "\n".join(
        json.dumps(row["output"], ensure_ascii=False)
        for row in load_jsonl(ROOT / "data/training_programs_final_v2.jsonl")
    ).casefold()
    assert "objectif de la journée" not in output_text
    assert "restitution critique du module" not in output_text
    assert not any(
        f'"{level}"' in output_text for level in ("beginner", "intermediate", "advanced")
    )
    assert "enjeux expert" not in output_text
    assert "pédagogie expert" not in output_text
    assert "<script" not in text.casefold()


def test_cleaner_is_reproducible_and_source_is_unchanged(tmp_path: Path) -> None:
    source = ROOT / "data/training_programs_final.jsonl"
    before = digest(source)
    first_jsonl = tmp_path / "first.jsonl"
    first_json = tmp_path / "first.json"
    second_jsonl = tmp_path / "second.jsonl"
    second_json = tmp_path / "second.json"
    script = ROOT / "scripts/clean_training_programs_final_v2.py"
    for jsonl_path, json_path in ((first_jsonl, first_json), (second_jsonl, second_json)):
        subprocess.run(
            [
                sys.executable,
                str(script),
                "--input",
                str(source),
                "--jsonl",
                str(jsonl_path),
                "--json",
                str(json_path),
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    assert first_jsonl.read_bytes() == second_jsonl.read_bytes()
    assert first_json.read_bytes() == second_json.read_bytes()
    assert digest(source) == before
