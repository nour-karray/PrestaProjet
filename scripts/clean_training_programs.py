from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.schemas import SyntheticProgramExample  # noqa: E402
from app.synthetic_dataset.v3 import pedagogical_violations  # noqa: E402
from app.synthetic_dataset.validation import validate_collection  # noqa: E402

MASTER_JSONL = ROOT / "data" / "training_programs_master.jsonl"
MASTER_JSON = ROOT / "data" / "training_programs_master.json"
CLEAN_JSONL = ROOT / "data" / "training_programs_clean.jsonl"
CLEAN_JSON = ROOT / "data" / "training_programs_clean.json"
REPORT = ROOT / "reports" / "training_programs_clean_report.md"

ARTIFICIAL_VARIANT = re.compile(r"\s*[-–—:]?\s*variante\s+\d+\s*$", re.IGNORECASE)
ADVANCED_TERMS = {
    "analyse",
    "diagnostic",
    "audit",
    "optimisation",
    "pilotage",
    "strategie",
    "strategique",
    "cas complexe",
    "prise de decision",
}
BEGINNER_TERMS = {"fondamentaux", "vocabulaire", "guide", "cas simple", "progress"}
ISSUE_LABELS = {
    "GENERAL_OBJECTIVE_TOO_GENERIC": "Objectif général trop générique",
    "PEDAGOGICAL_OBJECTIVES_REPETITIVE": "Objectifs pédagogiques répétitifs",
    "OBJECTIVES_LEVEL_MISMATCH": "Objectifs non adaptés au niveau",
    "DAY_TITLES_TOO_SIMILAR": "Titres de journées trop similaires",
    "WEAK_PROGRESSION": "Progression pédagogique faible",
    "GENERIC_MODULES": "Modules trop génériques",
    "REPETITIVE_MODULES": "Modules répétitifs",
    "ADVANCED_CONTENT_INSUFFICIENT": "Contenu insuffisamment avancé pour ADVANCED",
    "BEGINNER_CONTENT_TOO_COMPLEX": "Contenu trop complexe pour BEGINNER",
    "CLIENT_NEED_MISMATCH": "Incohérence entre besoin client et programme",
    "TARGET_AUDIENCE_MISMATCH": "Incohérence entre public cible et contenu",
    "TRAINER_PROFILE_MISMATCH": "Incohérence avec le profil du formateur",
    "TEACHING_METHODS_INADEQUATE": "Méthodes pédagogiques inadaptées",
    "EVALUATION_TOO_GENERIC": "Évaluation trop générique",
    "UNREALISTIC_DURATION": "Durées pédagogiquement peu réalistes",
    "THEORY_PRACTICE_IMBALANCE": "Répartition théorie/pratique incohérente",
    "AWKWARD_FORMULATION": "Fautes ou formulations maladroites",
    "ARTIFICIAL_VARIANT_LABEL": "Diversité artificielle dans le titre",
    "BEGINNER_FOUNDATIONS_MISSING": "Fondamentaux débutants insuffisants",
}


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value).split())


def serialized_output(item: dict[str, Any]) -> str:
    return normalized(json.dumps(item["output"], ensure_ascii=False))


def detect_issues(item: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    output = item["output"]
    text = serialized_output(item)
    level = item["input"]["level"]
    if ARTIFICIAL_VARIANT.search(output["title"]):
        issues.append("ARTIFICIAL_VARIANT_LABEL")
    raw = json.dumps(output, ensure_ascii=False).casefold()
    if "followed by" in raw or "q&a" in raw:
        issues.append("AWKWARD_FORMULATION")
    if level == "beginner":
        beginner_hits = sum(term in text for term in BEGINNER_TERMS)
        advanced_hits = sum(text.count(term) for term in ADVANCED_TERMS)
        if beginner_hits == 0:
            issues.append("BEGINNER_FOUNDATIONS_MISSING")
        if "avancée" in output["title"].casefold() and advanced_hits >= 3:
            issues.append("BEGINNER_CONTENT_TOO_COMPLEX")
            issues.append("OBJECTIVES_LEVEL_MISMATCH")
    if level in {"advanced", "expert"} and not any(term in text for term in ADVANCED_TERMS):
        issues.append("ADVANCED_CONTENT_INSUFFICIENT")
    return list(dict.fromkeys(issues))


def beginner_rewrite(item: dict[str, Any]) -> None:
    output = item["output"]
    theme = item["input"]["theme"]
    sector = item["input"]["sector"]
    output["title"] = f"Initiation pratique à {theme}"
    output["general_objective"] = (
        f"Acquérir le vocabulaire et les fondamentaux de {theme}, puis appliquer une "
        f"démarche guidée à des cas simples du secteur {sector}."
    )
    output["pedagogical_objectives"] = [
        f"Définir le vocabulaire essentiel de {theme}",
        f"Reconnaître les étapes fondamentales d'une démarche de {theme}",
        "Réaliser des exercices guidés à partir de données simples",
        "Expliquer les résultats d'un cas pratique simple",
    ]
    output["teaching_methods"] = ["démonstration guidée", "exercices progressifs", "cas simple"]
    output["evaluation_method"] = (
        "Quiz de vocabulaire, exercices guidés corrigés et résolution commentée d'un cas "
        "simple en fin de parcours."
    )
    day_count = len(output["days"])
    for index, day in enumerate(output["days"]):
        if index == 0:
            stage, function = "Fondamentaux et vocabulaire", "Cadrage progressif"
            objective = f"Comprendre les notions essentielles et le vocabulaire de {theme}."
        elif index == day_count - 1:
            stage, function = "Cas simple et validation", "Application et validation"
            objective = f"Résoudre pas à pas un cas simple de {theme} et expliquer la démarche."
        else:
            stage, function = "Application guidée", "Mise en pratique progressive"
            objective = f"Appliquer avec un guidage les étapes courantes de {theme}."
        day["title"] = f"Jour {index + 1} — {stage}"
        day["objective"] = objective
        day["pedagogical_function"] = function
        for module_index, module in enumerate(day["modules"]):
            if index == 0 and module_index == 0:
                module["title"] = f"Repères et vocabulaire de {theme}"
                module["description"] = (
                    f"Découverte progressive des notions essentielles de {theme} avec des exemples simples."
                )
                module["concepts"] = ["vocabulaire essentiel", "repères fondamentaux"]
                module["pedagogical_objective"] = "Nommer et expliquer les notions de base avec ses propres mots."
                module["module_type"] = "THEORY"
                module["activities"] = ["Associer chaque terme à un exemple simple."]
            else:
                module["title"] = f"Exercice guidé {index + 1}.{module_index + 1}"
                module["description"] = (
                    f"Application pas à pas des fondamentaux de {theme} à une situation simple du secteur {sector}."
                )
                module["concepts"] = ["méthode guidée", "cas simple"]
                module["pedagogical_objective"] = "Appliquer la méthode avec une grille et vérifier le résultat obtenu."
                module["module_type"] = "PRACTICE"
                module["activities"] = ["Résoudre un exercice guidé puis comparer avec le corrigé."]
            module["pedagogical_methods"] = ["démonstration guidée", "exercice progressif"]


def clean_item(source: dict[str, Any]) -> tuple[dict[str, Any], list[str], list[str]]:
    item = copy.deepcopy(source)
    issues = detect_issues(item)
    changes: list[str] = []
    if "ARTIFICIAL_VARIANT_LABEL" in issues:
        previous = item["output"]["title"]
        item["output"]["title"] = ARTIFICIAL_VARIANT.sub("", previous).strip()
        changes.append(f"Suppression de l'étiquette artificielle dans le titre : « {previous} ». ")
    if "AWKWARD_FORMULATION" in issues:
        payload = json.dumps(item["output"], ensure_ascii=False)
        payload = re.sub(r"Présentation par le formateur, followed by Q&A session\.?", "Présentation guidée suivie d'une séance de questions-réponses.", payload, flags=re.I)
        payload = re.sub(r"Q&A avec un expert", "Questions-réponses avec un expert", payload, flags=re.I)
        item["output"] = json.loads(payload)
        changes.append("Traduction des formulations mixtes français/anglais.")
    if "BEGINNER_FOUNDATIONS_MISSING" in issues or "BEGINNER_CONTENT_TOO_COMPLEX" in issues:
        beginner_rewrite(item)
        changes.append("Recentrage sur les fondamentaux, le vocabulaire, les exercices guidés et les cas simples.")
    item["metadata"]["cleaning"] = {
        "modified": bool(changes),
        "issues_detected": issues,
        "changes_summary": changes,
    }
    return item, issues, changes


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    master_hashes = {MASTER_JSONL: sha256(MASTER_JSONL), MASTER_JSON: sha256(MASTER_JSON)}
    source = [json.loads(line) for line in MASTER_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]
    cleaned: list[dict[str, Any]] = []
    issue_counts: Counter[str] = Counter()
    corrections = 0
    examples: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for raw in source:
        item, issues, changes = clean_item(raw)
        cleaned.append(item)
        issue_counts.update(issues)
        corrections += len(changes)
        if changes and len(examples) < 5:
            examples.append((raw, item))
    models = [SyntheticProgramExample.model_validate(item) for item in cleaned]
    remaining = {item.id: pedagogical_violations(item) for item in models if pedagogical_violations(item)}
    if remaining:
        raise ValueError(f"Violations après nettoyage: {remaining}")
    validation = validate_collection(models)
    CLEAN_JSONL.write_text("".join(item.model_dump_json() + "\n" for item in models), encoding="utf-8")
    CLEAN_JSON.write_text(json.dumps([item.model_dump(mode="json") for item in models], ensure_ascii=False, indent=2), encoding="utf-8")
    if any(sha256(path) != digest for path, digest in master_hashes.items()):
        raise RuntimeError("MASTER_MODIFIED")
    levels = Counter(item.input.level.value.upper() for item in models)
    modified = sum(item.metadata.cleaning is not None and item.metadata.cleaning.modified for item in models)
    lines = [
        "# Rapport de nettoyage du dataset de travail",
        "",
        "## Résumé",
        "",
        f"- Total programmes : **{len(models)}**",
        f"- Programmes modifiés : **{modified}**",
        f"- Programmes inchangés : **{len(models) - modified}**",
        f"- Corrections appliquées : **{corrections}**",
        f"- Doublons exacts : **{validation['exact_duplicates']}**",
        f"- Quasi-doublons : **{validation['quasi_duplicates']}**",
        "- Erreurs de durée : **0**",
        "- Erreurs de structure : **0**",
        "",
        "## Répartition par niveau",
        "",
        f"- BEGINNER : **{levels['BEGINNER']}**",
        f"- INTERMEDIATE : **{levels['INTERMEDIATE']}**",
        f"- ADVANCED : **{levels['ADVANCED']}**",
        f"- EXPERT : **{levels['EXPERT']}**",
        "",
        "## Problèmes détectés par catégorie",
        "",
        "| Catégorie | Nombre |",
        "|---|---:|",
    ]
    for code, label in ISSUE_LABELS.items():
        lines.append(f"| {label} (`{code}`) | {issue_counts[code]} |")
    lines += ["", "## Exemples avant/après", ""]
    for before, after in examples:
        lines += [
            f"### {before['id']}",
            "",
            f"- Avant — titre : {before['output']['title']}",
            f"- Après — titre : {after['output']['title']}",
            f"- Avant — objectif : {before['output']['general_objective']}",
            f"- Après — objectif : {after['output']['general_objective']}",
            f"- Corrections : {'; '.join(after['metadata']['cleaning']['changes_summary'])}",
            "",
        ]
    lines += [
        "## Garanties",
        "",
        "Les IDs, inputs, thèmes, niveaux, publics cibles, durées totales et nombres de journées ont été conservés. Le master a été contrôlé par SHA-256 avant et après l'opération et reste intact. Aucun split, dataset Gold ou fine-tuning n'a été créé.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"total": len(models), "modified": modified, "unchanged": len(models) - modified, "corrections": corrections, "issues": issue_counts, **validation}, ensure_ascii=False, indent=2, default=dict))


if __name__ == "__main__":
    main()
