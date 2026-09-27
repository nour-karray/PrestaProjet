from __future__ import annotations

import importlib.util
from pathlib import Path

from app.synthetic_dataset.review import build_review_queue, family_analysis
from app.tests.test_synthetic_dataset import valid_example

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "build_gold_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_gold_dataset", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_pending_entries_are_excluded_from_gold() -> None:
    example = valid_example()
    queue = build_review_queue([example], family_analysis([example]))
    assert MODULE.select_gold([queue[0].model_dump(mode="json")]) == []


def test_family_never_leaks_between_splits() -> None:
    examples = [valid_example(f"program_{index:04d}") for index in range(1, 5)]
    splits = MODULE.split_by_family(examples)
    containing = [name for name, values in splits.items() if values]
    assert len(containing) == 1
    assert len(splits[containing[0]]) == 4
