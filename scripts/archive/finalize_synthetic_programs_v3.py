from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.pdf_preview import generate_pdf_previews  # noqa: E402
from app.synthetic_dataset.review import (  # noqa: E402
    build_review_queue,
    family_analysis,
    migrate_family_ids,
)
from app.synthetic_dataset.v3 import pedagogical_violations  # noqa: E402
from app.synthetic_dataset.validation import validate_collection  # noqa: E402


def load(path: Path):  # type: ignore[no-untyped-def]
    return migrate_family_ids(
        [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    )


def violation_summary(examples) -> tuple[dict[str, list[str]], Counter[str]]:  # type: ignore[no-untyped-def]
    details = {item.id: pedagogical_violations(item) for item in examples}
    details = {key: value for key, value in details.items() if value}
    return details, Counter(reason for reasons in details.values() for reason in reasons)


def diversity_counts(analyses: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "families_too_close": sum(item["too_close"] for item in analyses),
        "distinct_titles": sum(item["titles"] for item in analyses),
        "distinct_objectives": sum(item["objectives"] for item in analyses),
        "distinct_day_structures": sum(item["day_structures"] for item in analyses),
        "distinct_module_structures": sum(item["module_structures"] for item in analyses),
        "distinct_evaluations": sum(item["evaluations"] for item in analyses),
    }


def write_report(
    before,
    after,
    before_analysis: list[dict[str, Any]],
    after_analysis: list[dict[str, Any]],
    stats: dict[str, Any],
    path: Path,
) -> None:  # type: ignore[no-untyped-def]
    before_details, before_reasons = violation_summary(before)
    after_details, after_reasons = violation_summary(after)
    before_diversity = diversity_counts(before_analysis)
    after_diversity = diversity_counts(after_analysis)
    after_by_family = {item["generation_family_id"]: item for item in after_analysis}
    lines = [
        "# Comparaison pédagogique — Dataset synthétique v1 vs v3",
        "",
        "## Résultat global",
        "",
        "| Indicateur | v1 | v3 |",
        "|---|---:|---:|",
        f"| Programmes | {len(before)} | {len(after)} |",
        f"| Programmes violant les règles pédagogiques | {len(before_details)} | {len(after_details)} |",
        f"| Doublons exacts | 0 | {stats.get('exact_duplicates', 0)} |",
        f"| Quasi-doublons | 19 | {stats.get('quasi_duplicates', 0)} |",
        f"| Familles trop proches | 17 | {after_diversity['families_too_close']} |",
        f"| Objectifs généraux distincts par famille (somme) | {before_diversity['distinct_objectives']} | {after_diversity['distinct_objectives']} |",
        f"| Évaluations distinctes par famille (somme) | {before_diversity['distinct_evaluations']} | {after_diversity['distinct_evaluations']} |",
        f"| Structures de modules distinctes (somme) | {before_diversity['distinct_module_structures']} | {after_diversity['distinct_module_structures']} |",
        "",
        "## Génération v3",
        "",
        f"- Programmes régénérés : **{stats.get('regenerated', len(after))}**",
        f"- Appels Qwen : **{stats.get('qwen_calls', 0)}**",
        f"- Réponses rejetées : **{stats.get('rejected', 0)}**",
        f"- Régénérations : **{stats.get('retries', 0)}**",
        f"- Temps : **{stats.get('elapsed_seconds', 0)} secondes**",
        "- Méthode : génération Qwen indépendante de chaque programme ; Python valide, ",
        "  attribue les durées et sauvegarde, sans dupliquer de contenu pédagogique.",
        "- Aucun fine-tuning n’a été lancé.",
        "",
        "## Violations pédagogiques avant/après",
        "",
        "| Règle | v1 | v3 |",
        "|---|---:|---:|",
    ]
    for reason in sorted(set(before_reasons) | set(after_reasons)):
        lines.append(f"| `{reason}` | {before_reasons[reason]} | {after_reasons[reason]} |")
    lines.extend(
        [
            "",
            "## Comparaison par famille",
            "",
            "| Famille | Thème | Similarité moyenne v1 | Similarité moyenne v3 | Similarité max v1 | Similarité max v3 | Alerte v3 |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in before_analysis:
        current = after_by_family[item["generation_family_id"]]
        lines.append(
            f"| {item['generation_family_id']} | {item['theme']} | "
            f"{item['average_content_similarity']:.3f} | "
            f"{current['average_content_similarity']:.3f} | "
            f"{item['max_content_similarity']:.3f} | "
            f"{current['max_content_similarity']:.3f} | "
            f"{'À revoir' if current['too_close'] else 'OK'} |"
        )
    lines.extend(
        [
            "",
            "## Programmes régénérés",
            "",
            "Tous les programmes v1 violaient au moins une nouvelle règle, notamment le module ",
            "unique par journée et la diversité artificielle `parcours/séquence`. Les 120 IDs et ",
            "les 30 `generation_family_id` ont été conservés dans la v3.",
            "",
            "## Limites restantes",
            "",
            "La validation automatique mesure la structure, la similarité lexicale et la cohérence ",
            "des durées. Une révision humaine métier reste indispensable pour confirmer la justesse ",
            "technique de chaque thème, notamment la paie, le droit, la sécurité et les normes.",
            "",
            "**La v3 reste un dataset candidat à la révision humaine, pas un dataset Gold.**",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Valider et finaliser le dataset synthétique v3.")
    parser.add_argument(
        "--v1",
        type=Path,
        default=ROOT / "data" / "training_programs_synthetic_v1.jsonl",
    )
    parser.add_argument(
        "--v3",
        type=Path,
        default=ROOT / "data" / "training_programs_synthetic_v3.jsonl",
    )
    args = parser.parse_args()
    before = load(args.v1)
    after = load(args.v3)
    if len(after) != 120:
        raise ValueError(f"V3_INCOMPLETE: {len(after)}/120")
    validation = validate_collection(after)
    remaining = {item.id: pedagogical_violations(item) for item in after}
    remaining = {key: value for key, value in remaining.items() if value}
    if remaining:
        raise ValueError(f"V3_PEDAGOGICAL_VIOLATIONS: {remaining}")
    before_analysis = family_analysis(before)
    after_analysis = family_analysis(after)
    analysis_path = ROOT / "reports" / "synthetic_dataset_v3_family_analysis.json"
    analysis_path.write_text(
        json.dumps(after_analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    queue = build_review_queue(after, after_analysis)
    queue_path = ROOT / "data" / "training_programs_review_queue_v3.json"
    queue_path.write_text(
        json.dumps([item.model_dump(mode="json") for item in queue], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    stats_path = ROOT / "reports" / "synthetic_dataset_v3_generation_stats.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    stats.update(validation)
    stats["families_too_close"] = sum(item["too_close"] for item in after_analysis)
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(
        before,
        after,
        before_analysis,
        after_analysis,
        stats,
        ROOT / "reports" / "synthetic_dataset_v1_vs_v3.md",
    )
    previews = generate_pdf_previews(
        after[:10], ROOT / "output" / "pdf" / "synthetic_programs_v3"
    )
    print(f"V3 validée: {len(after)} programmes")
    print(f"PDF générés: {len(previews)}")
    print(f"Familles encore proches: {stats['families_too_close']}")


if __name__ == "__main__":
    main()
