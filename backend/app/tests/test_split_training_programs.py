from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from app.schemas.program_document import TrainingProgramOutput

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "split_training_programs.py"
SPEC = importlib.util.spec_from_file_location("split_training_programs", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def load_final() -> list[dict]:  # type: ignore[type-arg]
    lines = (
        (ROOT / "data" / "training_programs_final.jsonl").read_text(encoding="utf-8").splitlines()
    )
    return [json.loads(line) for line in lines if line.strip()]


def signature(splits) -> dict[str, list[str]]:  # type: ignore[no-untyped-def]
    return {name: [item["id"] for item in values] for name, values in splits.items()}


def test_split_is_reproducible_and_complete() -> None:
    items = load_final()
    first = MODULE.split_programs(items, 42)
    second = MODULE.split_programs(items, 42)
    assert signature(first) == signature(second)
    assert {name: len(values) for name, values in first.items()} == {
        "train": 84,
        "validation": 20,
        "test": 16,
    }
    ids = [item["id"] for values in first.values() for item in values]
    assert len(ids) == 120
    assert len(ids) == len(set(ids))
    assert set(ids) == {item["id"] for item in items}


def test_no_id_or_family_leak() -> None:
    splits = MODULE.split_programs(load_final(), 42)
    id_sets = {name: {item["id"] for item in values} for name, values in splits.items()}
    assert not (id_sets["train"] & id_sets["validation"])
    assert not (id_sets["train"] & id_sets["test"])
    assert not (id_sets["validation"] & id_sets["test"])
    family_location: dict[str, set[str]] = {}
    for name, values in splits.items():
        for item in values:
            family_location.setdefault(item["generation_family_id"], set()).add(name)
    assert all(len(locations) == 1 for locations in family_location.values())


def test_every_split_is_pydantic_valid() -> None:
    splits = MODULE.split_programs(load_final(), 42)
    for values in splits.values():
        for item in values:
            program = TrainingProgramOutput.model_validate(item["output"])
            assert program.total_duration_minutes == item["input"]["total_duration_minutes"]
            assert len(program.days) == item["input"]["planned_days_count"]


def test_final_file_is_not_modified_by_split() -> None:
    path = ROOT / "data" / "training_programs_final.jsonl"
    before = hashlib.sha256(path.read_bytes()).digest()
    MODULE.split_programs(load_final(), 42)
    after = hashlib.sha256(path.read_bytes()).digest()
    assert before == after


def test_seed_42_serialization_is_reproducible() -> None:
    first = MODULE.split_programs(load_final(), 42)
    second = MODULE.split_programs(load_final(), 42)
    for name in MODULE.SPLIT_NAMES:
        first_bytes = "".join(
            json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
            for item in first[name]
        ).encode()
        second_bytes = "".join(
            json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
            for item in second[name]
        ).encode()
        assert hashlib.sha256(first_bytes).digest() == hashlib.sha256(second_bytes).digest()
