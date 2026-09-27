from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.synthetic_dataset.schemas import ProgramMetadata, ProgramOutput, SyntheticProgramExample


class ReviewScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    need_alignment: float = Field(ge=0, le=10)
    pedagogical_coherence: float = Field(ge=0, le=10)
    content_quality: float = Field(ge=0, le=10)
    duration_realism: float = Field(ge=0, le=10)
    level_adaptation: float = Field(ge=0, le=10)
    trainer_alignment: float = Field(ge=0, le=10)
    originality: float = Field(ge=0, le=10)
    global_score: float = Field(ge=0, le=10)


class ReviewEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    generation_family_id: str
    input: dict[str, Any]
    output: ProgramOutput
    metadata: ProgramMetadata
    review_status: Literal[
        "PENDING", "ACCEPTED", "ACCEPTED_WITH_CHANGES", "REJECTED"
    ] = "PENDING"
    scores: ReviewScores
    review_notes: str = ""
    corrected_output: ProgramOutput | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None


def make_family_id(theme: str, sequence: int = 1) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", theme.casefold()).strip("_")
    return f"theme_{slug}_{sequence:03d}"


def migrate_family_ids(raw_items: list[dict[str, Any]]) -> list[SyntheticProgramExample]:
    examples: list[SyntheticProgramExample] = []
    for raw in raw_items:
        item = dict(raw)
        item["generation_family_id"] = item.get("generation_family_id") or make_family_id(
            item["input"]["theme"]
        )
        examples.append(SyntheticProgramExample.model_validate(item))
    return examples


def save_examples(examples: list[SyntheticProgramExample], jsonl_path: Path) -> None:
    jsonl_path.write_text(
        "".join(example.model_dump_json() + "\n" for example in examples),
        encoding="utf-8",
    )
    jsonl_path.with_suffix(".json").write_text(
        json.dumps(
            [example.model_dump(mode="json") for example in examples],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def content_signature(example: SyntheticProgramExample) -> str:
    values = [
        example.output.title,
        example.output.general_objective,
        *example.output.pedagogical_objectives,
        example.output.evaluation_method,
    ]
    for day in example.output.days:
        values.extend([day.title, day.objective])
        for module in day.modules:
            values.extend([module.title, module.description, *module.concepts])
    return " ".join(values).casefold()


def exact_fingerprint(example: SyntheticProgramExample) -> str:
    canonical = json.dumps(
        example.model_dump(mode="json", exclude={"id"}),
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def family_analysis(examples: list[SyntheticProgramExample]) -> list[dict[str, Any]]:
    families: dict[str, list[SyntheticProgramExample]] = defaultdict(list)
    for example in examples:
        families[example.generation_family_id].append(example)
    results: list[dict[str, Any]] = []
    for family_id, members in sorted(families.items()):
        comparisons: list[float] = []
        for left_index, left in enumerate(members):
            for right in members[left_index + 1 :]:
                comparisons.append(
                    SequenceMatcher(None, content_signature(left), content_signature(right)).ratio()
                )
        average = sum(comparisons) / len(comparisons) if comparisons else 1.0
        maximum = max(comparisons, default=1.0)
        results.append(
            {
                "generation_family_id": family_id,
                "theme": members[0].input.theme,
                "count": len(members),
                "titles": len({item.output.title for item in members}),
                "objectives": len({item.output.general_objective for item in members}),
                "day_structures": len(
                    {
                        tuple(day.title for day in item.output.days)
                        for item in members
                    }
                ),
                "module_structures": len(
                    {
                        tuple(module.title for day in item.output.days for module in day.modules)
                        for item in members
                    }
                ),
                "durations": sorted({item.input.total_duration_minutes for item in members}),
                "styles": sorted({item.metadata.style.value for item in members}),
                "evaluations": len({item.output.evaluation_method for item in members}),
                "average_content_similarity": round(average, 4),
                "max_content_similarity": round(maximum, 4),
                "too_close": average >= 0.82 or maximum >= 0.92,
            }
        )
    return results


def automatic_scores(
    example: SyntheticProgramExample, family: dict[str, Any]
) -> ReviewScores:
    duration_ok = sum(
        module.duration_minutes
        for day in example.output.days
        for module in day.modules
    ) == example.input.total_duration_minutes
    raw = {
        "need_alignment": 8.0,
        "pedagogical_coherence": 8.0,
        "content_quality": 7.0,
        "duration_realism": 9.0 if duration_ok else 0.0,
        "level_adaptation": 7.0,
        "trainer_alignment": 8.0,
        "originality": 4.0 if family["too_close"] else 7.0,
    }
    raw["global_score"] = round(sum(raw.values()) / len(raw), 2)
    return ReviewScores.model_validate(raw)


def build_review_queue(
    examples: list[SyntheticProgramExample], analyses: list[dict[str, Any]]
) -> list[ReviewEntry]:
    by_family = {item["generation_family_id"]: item for item in analyses}
    return [
        ReviewEntry(
            id=example.id,
            generation_family_id=example.generation_family_id,
            input=example.input.model_dump(mode="json"),
            output=example.output,
            metadata=example.metadata,
            scores=automatic_scores(example, by_family[example.generation_family_id]),
        )
        for example in examples
    ]
