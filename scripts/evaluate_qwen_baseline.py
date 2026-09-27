from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.baseline import (  # noqa: E402
    BaselineGenerationConfig,
    OllamaQwenClient,
    generate_case,
)
from app.synthetic_dataset.schemas import SyntheticProgramExample  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for case in cases:
        SyntheticProgramExample.model_validate(case)
    return cases


def load_existing(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def metric_summary(
    cases: list[dict[str, Any]], records: list[dict[str, Any]]
) -> dict[str, Any]:
    total_cases = len(cases)
    attempted = len(records)
    counts = Counter(record["generation_status"] for record in records)
    metric_names = list(records[0]["automatic_metrics"]) if records else []
    metric_counts = {
        name: sum(bool(record["automatic_metrics"].get(name)) for record in records)
        for name in metric_names
    }

    def rate(name: str) -> float:
        return metric_counts.get(name, 0) / attempted if attempted else 0.0

    return {
        "total_cases": total_cases,
        "attempted_cases": attempted,
        "successful_generations": counts["SUCCESS"],
        "model_errors": counts["MODEL_ERROR"],
        "parse_errors": counts["PARSE_ERROR"],
        "json_parsable_count": metric_counts.get("json_parsable", 0),
        "json_parse_rate": rate("json_parsable"),
        "pydantic_valid_count": metric_counts.get("pydantic_valid", 0),
        "pydantic_valid_rate": rate("pydantic_valid"),
        "duration_compliant_count": metric_counts.get("total_duration_correct", 0),
        "duration_compliance_rate": rate("total_duration_correct"),
        "day_count_compliant_count": metric_counts.get("day_count_correct", 0),
        "day_count_compliance_rate": rate("day_count_correct"),
        "module_structure_compliant_count": metric_counts.get(
            "module_structure_correct", 0
        ),
        "module_structure_compliance_rate": rate("module_structure_correct"),
        "automatic_validation_pass_count": metric_counts.get(
            "automatic_validation_pass", 0
        ),
        "automatic_validation_pass_rate": rate("automatic_validation_pass"),
        "metric_counts": metric_counts,
        "total_generation_time_seconds": round(
            sum(r["generation_time_seconds"] for r in records), 4
        ),
        "average_generation_time_seconds": round(
            sum(r["generation_time_seconds"] for r in records) / attempted, 4
        )
        if attempted
        else 0.0,
    }


def write_semantic_review(
    cases: list[dict[str, Any]], records: list[dict[str, Any]], path: Path
) -> None:
    by_id = {record["program_id"]: record for record in records}
    score_names = (
        "need_alignment",
        "pedagogical_coherence",
        "content_quality",
        "level_adaptation",
        "trainer_alignment",
        "progression_quality",
        "evaluation_quality",
        "originality",
    )
    payload = []
    for case in cases:
        record = by_id.get(case["id"])
        payload.append(
            {
                "program_id": case["id"],
                "input": case["input"],
                "generation_status": record["generation_status"]
                if record
                else "NOT_RUN",
                "parsed_output": record["parsed_output"] if record else None,
                "semantic_scores": {name: None for name in score_names},
                "semantic_global_score": None,
                "review_notes": [],
            }
        )
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_report(
    cases: list[dict[str, Any]],
    records: list[dict[str, Any]],
    metrics: dict[str, Any],
    path: Path,
) -> None:
    by_id = {record["program_id"]: record for record in records}
    level_rows = []
    for level in ("beginner", "intermediate", "advanced", "expert"):
        ids = {case["id"] for case in cases if case["input"]["level"] == level}
        selected = [record for record in records if record["program_id"] in ids]
        level_rows.append(
            (
                level.upper(),
                len(ids),
                sum(r["generation_status"] == "SUCCESS" for r in selected),
                sum(
                    r["automatic_metrics"]["automatic_validation_pass"]
                    for r in selected
                ),
            )
        )
    errors = Counter(
        record.get("error") or "Aucune" for record in records if record.get("error")
    )
    config = (
        records[0]["generation_config"]
        if records
        else BaselineGenerationConfig().to_dict()
    )
    lines = [
        "# Baseline — Qwen2.5-7B-Instruct",
        "",
        f"- Date : **{datetime.now(UTC).isoformat()}**",
        "- Modèle : **qwen2.5:7b-instruct**",
        f"- Configuration : `{json.dumps(config, ensure_ascii=False)}`",
        f"- Cas du test : **{len(cases)}**",
        f"- Cas tentés : **{metrics['attempted_cases']}**",
        f"- Succès : **{metrics['successful_generations']}**",
        f"- Erreurs modèle : **{metrics['model_errors']}**",
        f"- Erreurs de parsing : **{metrics['parse_errors']}**",
        f"- JSON parsable : **{metrics['json_parse_rate']:.2%}**",
        f"- Pydantic valide : **{metrics['pydantic_valid_rate']:.2%}**",
        f"- Durée conforme : **{metrics['duration_compliance_rate']:.2%}**",
        f"- Nombre de jours conforme : **{metrics['day_count_compliance_rate']:.2%}**",
        f"- Structure des modules conforme : **{metrics['module_structure_compliance_rate']:.2%}**",
        "",
        "## Problèmes les plus fréquents",
        "",
    ]
    lines.extend(f"- {error} : **{count}**" for error, count in errors.most_common())
    if not errors:
        lines.append("- Aucun problème enregistré.")
    lines += [
        "",
        "## Résultats par niveau",
        "",
        "| Niveau | Cas | Succès | Validation automatique |",
        "|---|---:|---:|---:|",
    ]
    lines.extend(
        f"| {level} | {count} | {success} | {valid} |"
        for level, count, success, valid in level_rows
    )
    lines += [
        "",
        "## Cas",
        "",
        "| ID | Niveau | Statut | JSON | Pydantic | Durée | Structure | Temps (s) |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for case in cases:
        record = by_id.get(case["id"])
        if record:
            m = record["automatic_metrics"]
            lines.append(
                f"| {case['id']} | {case['input']['level'].upper()} | {record['generation_status']} | {m['json_parsable']} | {m['pydantic_valid']} | {m['total_duration_correct']} | {m['module_structure_correct']} | {record['generation_time_seconds']} |"
            )
        else:
            lines.append(
                f"| {case['id']} | {case['input']['level'].upper()} | NOT_RUN | — | — | — | — | — |"
            )
    lines += [
        "",
        "Les scores sémantiques humains ne sont pas encore remplis. BLEU et ROUGE ne sont pas utilisés comme mesures de qualité pédagogique.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Évaluer la baseline Qwen sur le test protégé."
    )
    parser.add_argument(
        "--test", type=Path, default=ROOT / "data" / "final" / "test.jsonl"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "reports" / "baseline"
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    test_hash = sha256(args.test)
    cases = load_cases(args.test)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    generations = args.output_dir / "qwen_base_generations.jsonl"
    existing = load_existing(generations)
    if existing and not args.resume:
        raise FileExistsError(f"Sorties existantes: {generations}. Utilisez --resume.")
    completed = {record["program_id"] for record in existing}
    pending = [case for case in cases if case["id"] not in completed]
    if args.limit is not None:
        pending = pending[: args.limit]
    client = OllamaQwenClient()
    try:
        client.health()
        for case in pending:
            append_record(
                generations, generate_case(client, case, BaselineGenerationConfig())
            )
    except RuntimeError as exc:
        if pending:
            append_record(
                generations,
                {
                    "program_id": pending[0]["id"],
                    "input": pending[0]["input"],
                    "raw_response": "",
                    "parsed_output": None,
                    "generation_status": "MODEL_ERROR",
                    "generation_time_seconds": 0.0,
                    "model": client.model,
                    "generation_config": BaselineGenerationConfig().to_dict(),
                    "error": str(exc),
                    "automatic_metrics": {
                        "response_produced": False,
                        "json_parsable": False,
                        "pydantic_valid": False,
                        "required_fields_present": False,
                        "day_count_correct": False,
                        "total_duration_correct": False,
                        "day_durations_correct": False,
                        "module_durations_sum_correct": False,
                        "module_structure_correct": False,
                        "seven_hour_day_structure_correct": False,
                        "module_duration_limit_correct": False,
                        "module_types_valid": False,
                        "day_titles_distinct": False,
                        "day_objectives_distinct": False,
                        "pedagogical_objectives_present": False,
                        "teaching_methods_present": False,
                        "resources_present": False,
                        "evaluation_present": False,
                        "automatic_validation_pass": False,
                    },
                    "target_comparison": {
                        "day_count_difference": None,
                        "module_count_difference": None,
                    },
                },
            )
    records = load_existing(generations)
    metrics = metric_summary(cases, records)
    (args.output_dir / "qwen_base_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_semantic_review(
        cases, records, args.output_dir / "qwen_base_semantic_review.json"
    )
    write_report(
        cases, records, metrics, args.output_dir / "qwen_base_baseline_report.md"
    )
    if sha256(args.test) != test_hash:
        raise RuntimeError("TEST_DATASET_MODIFIED")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
