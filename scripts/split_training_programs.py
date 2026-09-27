from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.schemas.program_document import TrainingProgramOutput  # noqa: E402

SPLIT_NAMES = ("train", "validation", "test")
RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}
FEATURES: dict[str, Callable[[dict[str, Any]], str]] = {
    "theme": lambda item: item["input"]["theme"],
    "domain": lambda item: item["metadata"]["domain"],
    "sector": lambda item: item["input"]["sector"],
    "target_audience": lambda item: item["input"]["target_audience"],
    "level": lambda item: item["input"]["level"],
    "duration": lambda item: str(item["input"]["total_duration_minutes"]),
    "days": lambda item: str(item["input"]["planned_days_count"]),
    "style": lambda item: item["metadata"]["style"],
    "modality": lambda item: item["input"]["delivery_mode"],
    "provenance": lambda item: item["metadata"].get("generation_method") or "unknown",
}
_SPLIT_CACHE: dict[tuple[int, tuple[str, ...]], dict[str, list[dict[str, Any]]]] = {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def family_targets(family_count: int) -> dict[str, int]:
    raw = {name: family_count * RATIOS[name] for name in SPLIT_NAMES}
    targets = {name: math.floor(raw[name]) for name in SPLIT_NAMES}
    remaining = family_count - sum(targets.values())
    order = sorted(
        SPLIT_NAMES, key=lambda name: (-(raw[name] - targets[name]), SPLIT_NAMES.index(name))
    )
    for name in order[:remaining]:
        targets[name] += 1
    return targets


def distribution(items: list[dict[str, Any]], feature: str) -> Counter[str]:
    getter = FEATURES[feature]
    return Counter(getter(item) for item in items)


def stratification_score(
    splits: dict[str, list[dict[str, Any]]], all_items: list[dict[str, Any]]
) -> float:
    total = len(all_items)
    score = 0.0
    for feature in FEATURES:
        global_counts = distribution(all_items, feature)
        for _split_name, items in splits.items():
            local = distribution(items, feature)
            ratio = len(items) / total
            for value, count in global_counts.items():
                expected = count * ratio
                score += abs(local[value] - expected) / max(1.0, expected)
    return score


def split_programs(items: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    cache_key = (seed, tuple(item["id"] for item in items))
    cached = _SPLIT_CACHE.get(cache_key)
    if cached is not None:
        return {name: values.copy() for name, values in cached.items()}
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        families[item["generation_family_id"]].append(item)
    family_ids = sorted(families)
    targets = family_targets(len(family_ids))
    rng = random.Random(seed)
    best_score = float("inf")
    best: dict[str, list[dict[str, Any]]] | None = None
    # Un échantillonnage déterministe de 250 affectations offre un bon compromis
    # entre équilibre multi-critères et temps d'exécution reproductible.
    for attempt in range(250):
        order = family_ids.copy()
        if attempt:
            rng.shuffle(order)
        cursor = 0
        candidate: dict[str, list[dict[str, Any]]] = {}
        for name in SPLIT_NAMES:
            selected = order[cursor : cursor + targets[name]]
            cursor += targets[name]
            candidate[name] = sorted(
                (item for family_id in selected for item in families[family_id]),
                key=lambda item: item["id"],
            )
        score = stratification_score(candidate, items)
        signature = tuple(tuple(item["id"] for item in candidate[name]) for name in SPLIT_NAMES)
        best_signature = (
            tuple(tuple(item["id"] for item in best[name]) for name in SPLIT_NAMES)
            if best
            else None
        )
        if score < best_score or (
            score == best_score and (best_signature is None or signature < best_signature)
        ):
            best_score, best = score, candidate
    assert best is not None
    _SPLIT_CACHE[cache_key] = {name: values.copy() for name, values in best.items()}
    return best


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_splits(
    splits: dict[str, list[dict[str, Any]]], expected_ids: set[str]
) -> dict[str, int]:
    ids_by_split = {name: {item["id"] for item in values} for name, values in splits.items()}
    overlaps = sum(
        len(ids_by_split[left] & ids_by_split[right])
        for index, left in enumerate(SPLIT_NAMES)
        for right in SPLIT_NAMES[index + 1 :]
    )
    all_ids = set().union(*ids_by_split.values())
    if all_ids != expected_ids:
        raise ValueError("Perte ou ajout d'identifiants dans les splits")
    family_locations: dict[str, set[str]] = defaultdict(set)
    for name, values in splits.items():
        for item in values:
            family_locations[item["generation_family_id"]].add(name)
        for item in values:
            program = TrainingProgramOutput.model_validate(item["output"])
            if program.total_duration_minutes != item["input"]["total_duration_minutes"]:
                raise ValueError(f"Durée invalide pour {item['id']}")
            if len(program.days) != item["input"]["planned_days_count"]:
                raise ValueError(f"Nombre de jours invalide pour {item['id']}")
    family_leaks = sum(len(locations) > 1 for locations in family_locations.values())
    if overlaps or family_leaks:
        raise ValueError(f"Fuite détectée: overlaps={overlaps}, families={family_leaks}")
    return {"overlaps": overlaps, "family_leaks": family_leaks, "families": len(family_locations)}


def markdown_distribution(splits: dict[str, list[dict[str, Any]]], feature: str) -> list[str]:
    values = sorted({value for items in splits.values() for value in distribution(items, feature)})
    lines = [
        f"### {feature.capitalize()}",
        "",
        "| Valeur | Train | Validation | Test |",
        "|---|---:|---:|---:|",
    ]
    counters = {name: distribution(items, feature) for name, items in splits.items()}
    for value in values:
        lines.append(
            f"| {value} | {counters['train'][value]} | "
            f"{counters['validation'][value]} | {counters['test'][value]} |"
        )
    return lines + [""]


def write_report(
    splits: dict[str, list[dict[str, Any]]], output_dir: Path, checks: dict[str, int], report: Path
) -> None:
    total = sum(map(len, splits.values()))
    lines = [
        "# Rapport des splits du dataset de programmes",
        "",
        "## Résumé",
        "",
        f"- Total : **{total}**",
        f"- Train : **{len(splits['train'])}** ({len(splits['train']) / total:.2%})",
        f"- Validation : **{len(splits['validation'])}** ({len(splits['validation']) / total:.2%})",
        f"- Test : **{len(splits['test'])}** ({len(splits['test']) / total:.2%})",
        f"- Familles : **{checks['families']}**",
        f"- Chevauchements d'IDs : **{checks['overlaps']}**",
        f"- Fuites de familles : **{checks['family_leaks']}**",
        "- Seed : **42**",
        "",
        "La répartition 84/20/16 conserve les trente familles de quatre programmes "
        "entièrement dans un seul split.",
        "",
        "## Empreintes SHA-256",
        "",
    ]
    for name in SPLIT_NAMES:
        lines.append(f"- `{name}.jsonl` : `{sha256(output_dir / f'{name}.jsonl')}`")
    lines += ["", "## Distributions", ""]
    for feature in (
        "theme",
        "level",
        "duration",
        "days",
        "sector",
        "target_audience",
        "domain",
        "style",
        "modality",
        "provenance",
    ):
        lines.extend(markdown_distribution(splits, feature))
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")


def write_readme(
    output_dir: Path,
    checks: dict[str, int],
    splits: dict[str, list[dict[str, Any]]],
    source: Path,
) -> None:
    level_counts = {name: distribution(items, "level") for name, items in splits.items()}
    level_lines = [
        "| Niveau | Train | Validation | Test |",
        "|---|---:|---:|---:|",
    ]
    for level in ("beginner", "intermediate", "advanced", "expert"):
        level_lines.append(
            f"| {level} | {level_counts['train'][level]} | "
            f"{level_counts['validation'][level]} | {level_counts['test'][level]} |"
        )
    hashes = [
        f"- `{name}.jsonl` : `{sha256(output_dir / f'{name}.jsonl')}`" for name in SPLIT_NAMES
    ]
    (output_dir / "README.md").write_text(
        f"# Splits {output_dir.name}\n\n"
        f"Source unique : `{source.as_posix()}`. Seed : `42`.\n\n"
        "## Tailles\n\n"
        f"- Train : {len(splits['train'])}\n"
        f"- Validation : {len(splits['validation'])}\n"
        f"- Test : {len(splits['test'])}\n"
        f"- Total : {sum(len(items) for items in splits.values())}\n"
        f"- Familles indivisibles : {checks['families']}\n\n"
        "## Méthode de séparation\n\n"
        "Les familles sont affectées de manière déterministe avec la graine 42. "
        "L'algorithme compare 250 affectations et retient celle qui équilibre le mieux "
        "les niveaux, thèmes, secteurs, publics, durées, journées et modalités. Une famille "
        "est toujours placée entièrement dans un seul split ; aucune fuite de famille n'est "
        "autorisée. Les lignes sont copiées octet pour octet depuis la source.\n\n"
        "## Distribution par niveau\n\n"
        + "\n".join(level_lines)
        + "\n\n## Empreintes SHA-256\n\n"
        + "\n".join(hashes)
        + "\n\n"
        "## Jeu de test gelé\n\n"
        "`test.jsonl` est un jeu de test gelé. Il ne doit jamais être utilisé pour le "
        "fine-tuning, le choix des hyperparamètres, la modification des données train, "
        "la création d’exemples similaires ou l’ajustement des prompts après observation "
        "des résultats.\n\n"
        "Il sert uniquement à la baseline du modèle Qwen original et à l’évaluation finale "
        "du modèle fine-tuné.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Créer des splits reproductibles sans fuite de famille."
    )
    parser.add_argument("--input", type=Path, default=ROOT / "data/training_programs_final.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/final_v2")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    input_hash = sha256(args.input)
    source_bytes = args.input.read_bytes().splitlines(keepends=True)
    items = [json.loads(line.decode("utf-8")) for line in source_bytes if line.strip()]
    raw_line_by_id = {
        json.loads(line.decode("utf-8"))["id"]: line for line in source_bytes if line.strip()
    }
    if len(items) != 120 or len({item["id"] for item in items}) != 120:
        raise ValueError("La source doit contenir exactement 120 IDs uniques")
    for item in items:
        TrainingProgramOutput.model_validate(item["output"])
    splits = split_programs(items, args.seed)
    checks = validate_splits(splits, {item["id"] for item in items})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, values in splits.items():
        (args.output_dir / f"{name}.jsonl").write_bytes(
            b"".join(raw_line_by_id[item["id"]] for item in values)
        )
    if sha256(args.input) != input_hash:
        raise RuntimeError("SOURCE_FINAL_MODIFIED")
    try:
        source_label = args.input.resolve().relative_to(ROOT.resolve())
    except ValueError:
        source_label = args.input
    write_readme(args.output_dir, checks, splits, source_label)
    write_report(
        splits,
        args.output_dir,
        checks,
        ROOT / f"reports/{args.output_dir.name}_split_report.md",
    )
    print(json.dumps({name: len(values) for name, values in splits.items()} | checks, indent=2))


if __name__ == "__main__":
    main()
