from __future__ import annotations

import json
from pathlib import Path

from app.schemas.program_document import TrainingProgramOutput

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data/training_programs_final_v3.jsonl"
SPLIT_DIR = ROOT / "data/final_v3"
NAMES = ("train", "validation", "test")


def source_lines() -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for line in SOURCE.read_bytes().splitlines(keepends=True):
        row = json.loads(line.decode("utf-8"))
        result[row["id"]] = line
    return result


def split_rows() -> dict[str, list[dict]]:
    return {
        name: [
            json.loads(line)
            for line in (SPLIT_DIR / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
            if line
        ]
        for name in NAMES
    }


def test_dataset_split_sizes_and_ids() -> None:
    splits = split_rows()
    assert {name: len(rows) for name, rows in splits.items()} == {
        "train": 84,
        "validation": 20,
        "test": 16,
    }
    ids = [row["id"] for rows in splits.values() for row in rows]
    assert len(ids) == len(set(ids)) == 120
    assert set(ids) == set(source_lines())


def test_dataset_has_no_id_overlap_or_family_leak() -> None:
    splits = split_rows()
    id_sets = {name: {row["id"] for row in rows} for name, rows in splits.items()}
    assert not (id_sets["train"] & id_sets["validation"])
    assert not (id_sets["train"] & id_sets["test"])
    assert not (id_sets["validation"] & id_sets["test"])
    locations: dict[str, set[str]] = {}
    for name, rows in splits.items():
        for row in rows:
            locations.setdefault(row["generation_family_id"], set()).add(name)
    assert len(locations) == 30
    assert all(len(names) == 1 for names in locations.values())


def test_split_lines_are_byte_identical_to_source() -> None:
    expected = source_lines()
    for name in NAMES:
        for line in (SPLIT_DIR / f"{name}.jsonl").read_bytes().splitlines(keepends=True):
            row = json.loads(line.decode("utf-8"))
            assert line == expected[row["id"]]


def test_split_programs_are_pydantic_valid() -> None:
    for rows in split_rows().values():
        for row in rows:
            TrainingProgramOutput.model_validate(row["output"])
