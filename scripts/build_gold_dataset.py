from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.review import ReviewEntry  # noqa: E402
from app.synthetic_dataset.schemas import SyntheticProgramExample  # noqa: E402


def select_gold(raw_entries: list[dict[str, Any]]) -> list[SyntheticProgramExample]:
    selected: list[SyntheticProgramExample] = []
    fingerprints: set[str] = set()
    for raw in raw_entries:
        entry = ReviewEntry.model_validate(raw)
        if entry.review_status not in {"ACCEPTED", "ACCEPTED_WITH_CHANGES"}:
            continue
        if entry.scores.global_score < 7:
            continue
        output = entry.output
        if entry.review_status == "ACCEPTED_WITH_CHANGES":
            if entry.corrected_output is None:
                continue
            output = entry.corrected_output
        example = SyntheticProgramExample.model_validate(
            {
                "id": entry.id,
                "generation_family_id": entry.generation_family_id,
                "input": entry.input,
                "output": output.model_dump(mode="json"),
                "metadata": entry.metadata.model_dump(mode="json"),
            }
        )
        fingerprint = hashlib.sha256(
            json.dumps(example.output.model_dump(mode="json"), sort_keys=True).encode()
        ).hexdigest()
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        selected.append(example)
    return selected


def split_by_family(
    examples: list[SyntheticProgramExample], seed: str = "synthetic-v1"
) -> dict[str, list[SyntheticProgramExample]]:
    families: dict[str, list[SyntheticProgramExample]] = defaultdict(list)
    for example in examples:
        families[example.generation_family_id].append(example)
    result: dict[str, list[SyntheticProgramExample]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    for family_id, members in sorted(families.items()):
        bucket = int(hashlib.sha256(f"{seed}:{family_id}".encode()).hexdigest()[:8], 16) % 10
        split = "train" if bucket < 8 else "validation" if bucket == 8 else "test"
        result[split].extend(members)
    return result


def write_splits(splits: dict[str, list[SyntheticProgramExample]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, examples in splits.items():
        (output_dir / f"{name}.jsonl").write_text(
            "".join(example.model_dump_json() + "\n" for example in examples),
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Construire le dataset Gold après revue humaine.")
    parser.add_argument(
        "--review-queue",
        type=Path,
        default=ROOT / "data" / "training_programs_review_queue_master.json",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "gold")
    args = parser.parse_args()
    raw_entries = json.loads(args.review_queue.read_text(encoding="utf-8"))
    selected = select_gold(raw_entries)
    splits = split_by_family(selected)
    write_splits(splits, args.output_dir)
    print(f"Exemples Gold retenus: {len(selected)}")
    for name, examples in splits.items():
        print(f"{name}: {len(examples)}")


if __name__ == "__main__":
    main()
