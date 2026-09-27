from __future__ import annotations

import json
from pathlib import Path

from app.schemas.program_document import TrainingProgramOutput

ROOT = Path(__file__).resolve().parents[3]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_curated_dataset_has_120_valid_unique_programs() -> None:
    rows = load_jsonl(ROOT / "data/training_programs_final_v3.jsonl")
    assert len(rows) == 120
    assert len({row["id"] for row in rows}) == 120
    assert len({json.dumps(row["output"], sort_keys=True) for row in rows}) == 120
    for row in rows:
        TrainingProgramOutput.model_validate(row["output"])


def test_curated_dataset_preserves_every_protected_business_field() -> None:
    before = load_jsonl(ROOT / "data/training_programs_final_v2.jsonl")
    after = load_jsonl(ROOT / "data/training_programs_final_v3.jsonl")
    for old, new in zip(before, after, strict=True):
        for key in ("id", "generation_family_id", "input", "metadata"):
            assert new[key] == old[key]
        assert new["output"]["theme"] == old["output"]["theme"]
        assert new["output"]["target_audience"] == old["output"]["target_audience"]
        assert new["output"]["trainer"] == old["output"]["trainer"]
        assert new["output"]["total_duration_minutes"] == old["output"]["total_duration_minutes"]
        assert len(new["output"]["days"]) == len(old["output"]["days"])
        for old_day, new_day in zip(old["output"]["days"], new["output"]["days"], strict=True):
            for key in ("day_number", "theory_minutes", "practice_minutes"):
                assert new_day[key] == old_day[key]


def test_curated_dataset_has_no_targeted_template_or_language_defect() -> None:
    rows = load_jsonl(ROOT / "data/training_programs_final_v3.jsonl")
    text = "\n".join(json.dumps(row["output"], ensure_ascii=False) for row in rows).casefold()
    forbidden = (
        "dans une situation professionnelle adaptée",
        "justifier la décision à partir d'indicateurs métier",
        "puis produire une décision applicable",
        "simulation stratégique",
        "revue stratégique des décisions",
        "mise en commun des acquis",
        "formalisation des recommandations",
        "vérification guidée des acquis",
        "adapté à chefs",
        "adapté à collaborateurs",
        "adapté à techniciens",
        "adapté à nouveaux",
        "au secteur secteur",
        "dans un équipe",
        "d'power bi",
        "final deliverable",
        "feedback",
        "forecast",
        "roadmap",
        "dashboards",
        "budgeting",
        "coaching",
        "nurturing",
    )
    assert not any(value in text for value in forbidden)


def test_multiday_programs_have_no_method_common_to_every_day() -> None:
    rows = load_jsonl(ROOT / "data/training_programs_final_v3.jsonl")
    for row in rows:
        days = row["output"]["days"]
        if len(days) < 2:
            continue
        method_sets = [
            {method.casefold() for method in day["methods_and_resources"]} for day in days
        ]
        assert not set.intersection(*method_sets)
