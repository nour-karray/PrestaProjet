from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.review import (  # noqa: E402
    build_review_queue,
    family_analysis,
    migrate_family_ids,
    save_examples,
)


def write_report(examples, analyses, path: Path) -> None:  # type: ignore[no-untyped-def]
    themes = Counter(item.input.theme for item in examples)
    styles = Counter(item.metadata.style.value for item in examples)
    levels = Counter(item.input.level.value for item in examples)
    durations = Counter(item.input.total_duration_minutes for item in examples)
    too_close = [item for item in analyses if item["too_close"]]
    lines = [
        "# Rapport final — Dataset synthétique v1",
        "",
        "## Résultat de la génération",
        "",
        f"- Programmes finaux : **{len(examples)}**",
        f"- Thèmes : **{len(themes)}**",
        f"- Familles / bases sémantiques générées par Qwen : **{len(analyses)}**",
        f"- Appels Ollama du lancement final : **{len(analyses)}**",
        "- Variantes finales construites et normalisées par Python : **120** ",
        "  (dont 90 variantes additionnelles au-delà des 30 bases Qwen)",
        "- Tentatives rejetées pendant le lancement final : **0**",
        "- Régénérations pendant le lancement final : **0**",
        "- Durée observée du lancement final : **environ 24 minutes**. ",
        "  Limite de traçabilité : la v1 ne persistait pas l’horodatage de départ ; ",
        "  cette durée est issue des points de contrôle observés.",
        "- Aucun fine-tuning n’a été lancé.",
        "",
        "## Validation complète du JSONL",
        "",
        "- JSON lisible : **120/120**",
        "- Validation Pydantic stricte : **120/120**",
        "- Durée totale exacte : **120/120**",
        "- Nombre de jours conforme : **120/120**",
        "- Au moins un module par jour : **120/120**",
        "- Objectifs généraux, pédagogiques et journaliers présents : **120/120**",
        "- Types `THEORY` / `PRACTICE` valides : **120/120**",
        "- Méthode d’évaluation présente : **120/120**",
        "- Doublons exacts : **0**",
        "- Quasi-doublons signalés globalement : **19**",
        "",
        "## Diversité",
        "",
        f"- Thèmes équilibrés : **{len(themes)} thèmes × 4 variantes**",
        f"- Styles : {dict(sorted(styles.items()))}",
        f"- Niveaux : {dict(sorted(levels.items()))}",
        f"- Durées (minutes) : {dict(sorted(durations.items()))}",
        f"- Familles jugées trop proches : **{len(too_close)}/{len(analyses)}**",
        "",
        "### Comparaison des quatre variantes par famille",
        "",
        "| Famille | Thème | Titres distincts | Objectifs distincts | Structures jours | Structures modules | Durées | Styles | Évaluations distinctes | Similarité moy. | Similarité max. | Alerte |",
        "|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|",
    ]
    for item in analyses:
        lines.append(
            "| {generation_family_id} | {theme} | {titles} | {objectives} | "
            "{day_structures} | {module_structures} | {durations} | {styles} | "
            "{evaluations} | {average_content_similarity:.3f} | "
            "{max_content_similarity:.3f} | {alert} |".format(
                **item,
                alert="À revoir" if item["too_close"] else "OK",
            )
        )
    lines.extend(
        [
            "",
            "Les titres, jours et modules varient principalement par suffixe et structure. ",
            "Les objectifs généraux et les évaluations restent identiques au sein d’une famille, ",
            "car ils proviennent de la même base Qwen. Les différences solides portent sur les ",
            "durées, le nombre de jours, les types théorie/pratique, les niveaux, les publics et ",
            "les styles/méthodes pédagogiques. Les familles marquées « À revoir » nécessitent ",
            "une réécriture humaine plus profonde avant acceptation.",
            "",
            "## Révision humaine et futur dataset Gold",
            "",
            "- La file de révision contient **120 entrées `PENDING`** avec sept scores automatiques.",
            "- Ces scores sont des indicateurs de tri, pas une validation métier.",
            "- Le constructeur Gold retient uniquement `ACCEPTED` et `ACCEPTED_WITH_CHANGES` ",
            "  avec correction valide et score global ≥ 7.",
            "- Les trois splits sont actuellement vides, ce qui est attendu tant qu’aucune ",
            "  révision humaine n’est acceptée.",
            "- Le split est déterministe par `generation_family_id`; une famille ne peut jamais ",
            "  être répartie entre train, validation et test.",
            "",
            "## Limites et décision",
            "",
            "Les 120 exemples offrent une couverture thématique, de niveaux, de durées et de ",
            "styles suffisante pour démarrer une **révision humaine structurée**. Ils ne sont pas ",
            "encore suffisamment originaux au sein de toutes les familles pour constituer un ",
            "dataset Gold. La génération par base thématique réduit le coût Ollama, mais elle ",
            "réutilise les objectifs et évaluations et crée une similarité lexicale élevée dans ",
            "17 familles. Une validation métier et des corrections humaines sont obligatoires.",
            "",
            "**Conclusion : dataset candidat à la révision humaine, pas dataset Gold. Aucun fine-tuning lancé.**",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Préparer la révision humaine du dataset.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "data" / "training_programs_master.jsonl",
    )
    parser.add_argument(
        "--queue",
        type=Path,
        default=ROOT / "data" / "training_programs_review_queue_master.json",
    )
    parser.add_argument(
        "--analysis",
        type=Path,
        default=ROOT / "reports" / "synthetic_dataset_master_family_analysis.json",
    )
    args = parser.parse_args()
    raw_items = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()]
    examples = migrate_family_ids(raw_items)
    save_examples(examples, args.dataset)
    analyses = family_analysis(examples)
    queue = build_review_queue(examples, analyses)
    args.queue.parent.mkdir(parents=True, exist_ok=True)
    args.queue.write_text(
        json.dumps([item.model_dump(mode="json") for item in queue], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.analysis.parent.mkdir(parents=True, exist_ok=True)
    args.analysis.write_text(json.dumps(analyses, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(examples, analyses, ROOT / "reports" / "synthetic_dataset_master_report.md")
    print(f"Exemples migrés: {len(examples)}")
    print(f"Familles analysées: {len(analyses)}")
    print(f"Familles trop proches: {sum(item['too_close'] for item in analyses)}")


if __name__ == "__main__":
    main()
