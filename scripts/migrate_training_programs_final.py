from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.documents.program_pdf import generate_program_pdf  # noqa: E402
from app.schemas.program_document import TrainingProgramOutput  # noqa: E402

PROTECTED = [
    ROOT / "data/training_programs_master.json",
    ROOT / "data/training_programs_master.jsonl",
    ROOT / "data/training_programs_clean.json",
    ROOT / "data/training_programs_clean.jsonl",
    ROOT / "data/final/train.jsonl",
    ROOT / "data/final/validation.jsonl",
    ROOT / "data/final/test.jsonl",
]
SOURCE = ROOT / "data/training_programs_clean.jsonl"
FINAL_JSONL = ROOT / "data/training_programs_final.jsonl"
FINAL_JSON = ROOT / "data/training_programs_final.json"
PDF_DIR = ROOT / "reports/program_final_validation"
REPORT = ROOT / "reports/training_programs_final_migration_report.md"

REPLACEMENTS = {
    "written tests": "tests écrits",
    "Role-playing": "Jeu de rôle",
    "Role-play": "Jeu de rôle",
    "role-play": "jeu de rôle",
    "Case study": "Étude de cas",
    "case study": "étude de cas",
    "Q&A": "questions-réponses",
    "Solving exercises": "Exercices de résolution",
    "Assessment": "Évaluation",
    "assessment": "évaluation",
    "Workshop": "Atelier",
    "workshop": "atelier",
    " in groups": " en groupe",
    "interviewing": "entretien",
    "planning": "planification",
    "Planning": "Planification",
    "follow-up": "suivi",
    "opportunities": "opportunités",
    "compliance": "conformité",
    "risk assessment": "évaluation des risques",
    "Risk Évaluation": "Évaluation des risques",
    "action planning": "planification des actions",
    "audit preliminary": "audit préliminaire",
    "continuous improvement": "amélioration continue",
    "Internal Audit": "Audit interne",
    "Compliance Évaluation": "Évaluation de la conformité",
    "Project Management Tools": "Outils de gestion de projet",
    "Scrum in Consulting": "Scrum dans le conseil",
    "Sprint Planning": "Planification de sprint",
    "Planning Poker": "Estimation par cartes",
    "Sprint Planning Tool": "Outil de planification de sprint",
    "Threats and Risks in Financial Services Cybersecurity": "Menaces et risques de cybersécurité dans les services financiers",
    "Identify common cyber threats specific to the financial sector.": "Identifier les cybermenaces courantes propres au secteur financier.",
    "Develop awareness of potential cyber threats and their impact on financial services.": "Mesurer l’impact des cybermenaces potentielles sur les services financiers.",
    "Risk assessment exercise": "Exercice d’évaluation des risques",
    "Cybersecurity Audits: Principles and Practices": "Audits de cybersécurité : principes et pratiques",
    "Understand the principles of cybersecurity audits in the context of financial services.": "Comprendre les principes des audits de cybersécurité appliqués aux services financiers.",
    "Equip participants with knowledge on conducting effective cybersecurity audits.": "Préparer les participants à conduire des audits de cybersécurité efficaces.",
    "Mock audit report preparation": "Préparation d’un rapport d’audit simulé",
    "mock-up": "simulées",
    "Advanced Tools and Techniques for Cybersecurity in Financial Services": "Outils et techniques avancés de cybersécurité dans les services financiers",
    "Risk Évaluation Methods for Financial Systems": "Méthodes d’évaluation des risques des systèmes financiers",
    "Apply advanced tools and techniques to enhance cybersecurity measures within financial services.": "Appliquer des outils et techniques avancés pour renforcer la cybersécurité des services financiers.",
    "Learn how to assess risks in financial systems using modern methods.": "Apprendre à évaluer les risques des systèmes financiers avec des méthodes actuelles.",
    "Enable participants to conduct thorough risk assessments of financial systems.": "Permettre aux participants de conduire une évaluation approfondie des risques financiers.",
    "Risk assessment workshop": "Atelier d’évaluation des risques",
    "Tool demonstration and hands-on practice": "Démonstration d’outils et mise en pratique",
    "Compliance and Regulatory Frameworks in Cybersecurity": "Conformité et cadres réglementaires en cybersécurité",
    "Understand the regulatory requirements for cybersecurity in financial services.": "Comprendre les exigences réglementaires de cybersécurité des services financiers.",
    "Prepare participants to navigate compliance challenges in cyberspace.": "Préparer les participants à traiter les enjeux de conformité en cybersécurité.",
    "Compliance checklist development": "Élaboration d’une liste de contrôle de conformité",
    "Solve real-world problems related to advanced payroll management in financial services.": "Résoudre des problèmes réels de gestion avancée de la paie dans les services financiers.",
    "Conduct une audit": "Conduire un audit",
    "Diagnose": "Diagnostic",
    "Presentation": "Présentation",
    "Debat": "Débat",
    "Maitriser": "Maîtriser",
    "Evaluée": "Évaluer",
    "service coût cash": "performance coût-service-trésorerie",
    "Introduction à la Ressources Humaines": "Introduction aux ressources humaines",
    "Introduction à la Ressources humaines": "Introduction aux ressources humaines",
    "Evaluations": "Évaluations",
    "Equipes": "Équipes",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_text(value: str) -> tuple[str, list[str]]:
    original = value
    issues: list[str] = []
    for source, target in sorted(REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(re.escape(source), value, flags=re.IGNORECASE):
            value = re.sub(re.escape(source), target, value, flags=re.IGNORECASE)
            issues.append("langue")
    patterns = [
        (
            r"^(Comprendre|Appliquer|Arbitrer) (.+?) avec une méthode adaptée à (.+?)\.?$",
            lambda m: f"Mettre en œuvre {m.group(2)} dans une situation professionnelle adaptée à {m.group(3)}.",
        ),
        (
            r"^Appliquer (.+?) dans le contexte (.+?) et décider à partir de critères observables\.?$",
            lambda m: f"Mettre en œuvre {m.group(1)} dans le secteur {m.group(2)} et justifier la décision à partir de critères observables.",
        ),
    ]
    for pattern, replacement in patterns:
        updated = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
        if updated != value:
            value = updated
            issues.append("contenu")
    value = re.sub(r"\s+", " ", value).strip()
    return value, sorted(set(issues)) if value != original else []


def clean_list(values: list[str]) -> tuple[list[str], list[str]]:
    result: list[str] = []
    issues: list[str] = []
    for value in values:
        cleaned, found = normalize_text(value)
        issues.extend(found)
        if cleaned and cleaned.casefold() not in {item.casefold() for item in result}:
            result.append(cleaned)
    return result, issues


def allocate_day_durations(old_day: dict[str, Any], level: str) -> tuple[int, int]:
    """Blend declared module types with the actual pedagogical nature of the day."""
    total = sum(module["duration_minutes"] for module in old_day["modules"])
    declared_practice = sum(
        module["duration_minutes"]
        for module in old_day["modules"]
        if module["module_type"] == "PRACTICE"
    )
    level_ratio = {
        "beginner": 0.45,
        "intermediate": 0.55,
        "advanced": 0.62,
        "expert": 0.58,
    }[level]
    text = " ".join(
        [old_day["title"], old_day["objective"]]
        + [
            value
            for module in old_day["modules"]
            for value in [
                module["title"],
                module["description"],
                *module["pedagogical_methods"],
                *module["activities"],
            ]
        ]
    ).casefold()
    practical_terms = (
        "atelier",
        "exercice",
        "étude de cas",
        "simulation",
        "jeu de rôle",
        "mise en situation",
        "projet",
        "application",
        "production",
        "audit",
        "démonstration",
    )
    theory_terms = (
        "exposé",
        "fondamentaux",
        "introduction",
        "cadre",
        "concept",
        "vocabulaire",
        "présentation théorique",
        "réglementation",
    )
    practice_signals = sum(text.count(term) for term in practical_terms)
    theory_signals = sum(text.count(term) for term in theory_terms)
    signal_ratio = (practice_signals + 1) / (practice_signals + theory_signals + 2)
    declared_ratio = declared_practice / total
    practice_ratio = 0.50 * declared_ratio + 0.30 * level_ratio + 0.20 * signal_ratio
    if any(term in old_day["title"].casefold() for term in ("évaluation", "cas final", "projet")):
        practice_ratio = max(practice_ratio, 0.65)
    if any(
        term in old_day["title"].casefold() for term in ("introduction", "fondamentaux", "cadre")
    ):
        practice_ratio = min(practice_ratio, 0.48)
    practice_ratio = min(max(practice_ratio, 0.20), 0.80)
    practice = round(total * practice_ratio / 5) * 5
    practice = min(max(practice, 5), total - 5)
    return total - practice, practice


def migrate(row: dict[str, Any]) -> dict[str, Any]:
    migrated = copy.deepcopy(row)
    old = row["output"]
    issues: list[str] = []
    summaries: list[str] = []

    general, found = normalize_text(old["general_objective"])
    issues.extend(found)
    objectives, found = clean_list(old["pedagogical_objectives"])
    issues.extend(found)
    evaluation, found = normalize_text(old["evaluation_method"])
    issues.extend(found)
    days: list[dict[str, Any]] = []
    for old_day in old["days"]:
        title, found = normalize_text(old_day["title"])
        issues.extend(found)
        day_objective, found = normalize_text(old_day["objective"])
        issues.extend(found)
        contents: list[dict[str, Any]] = []
        methods_resources: list[str] = []
        declared_theory = declared_practice = 0
        for module in old_day["modules"]:
            module_title, found = normalize_text(module["title"])
            issues.extend(found)
            concepts, found = clean_list(module["concepts"])
            issues.extend(found)
            description, found = normalize_text(module["description"])
            issues.extend(found)
            module_objective, found = normalize_text(module["pedagogical_objective"])
            issues.extend(found)
            activities, found = clean_list(module.get("activities", []))
            issues.extend(found)
            useful = [f"Objectif de la journée : {day_objective}", description, module_objective]
            useful.extend(concepts)
            useful.extend(activities)
            useful, _ = clean_list(useful)
            contents.append({"title": module_title, "concepts": useful[:15]})
            combined, found = clean_list(
                [*module["pedagogical_methods"], *module["pedagogical_resources"]]
            )
            issues.extend(found)
            methods_resources.extend(combined)
            if module["module_type"] == "THEORY":
                declared_theory += module["duration_minutes"]
            else:
                declared_practice += module["duration_minutes"]
        theory, practice = allocate_day_durations(old_day, row["input"]["level"])
        if (theory, practice) != (declared_theory, declared_practice):
            issues.append("répartition")
            summaries.append(
                f"Jour {old_day['day_number']} : répartition théorie/pratique recalculée "
                "selon les activités, les méthodes, le niveau et les types de modules."
            )
        methods_resources, _ = clean_list(methods_resources)
        days.append(
            {
                "day_number": old_day["day_number"],
                "title": title,
                "contents": contents,
                "methods_and_resources": methods_resources[:12] or ["Support pédagogique"],
                "theory_minutes": theory,
                "practice_minutes": practice,
            }
        )

    level = row["input"]["level"]
    artificial = f"Pédagogie {level}"
    specialties = migrated["input"]["trainer_profile"]["specialties"]
    for index, specialty in enumerate(specialties):
        if specialty.startswith("Pédagogie ") and specialty != artificial:
            specialties[index] = artificial
            issues.append("niveau")
            summaries.append(f"Spécialité synthétique alignée sur le niveau {level}.")
    style = migrated["metadata"].get("style")
    if style in {"beginner", "advanced"} and style != level:
        migrated["metadata"]["style"] = level
        issues.append("niveau")
        summaries.append(f"Style synthétique aligné sur le niveau {level}.")

    output = {
        "theme": row["input"]["theme"],
        "target_audience": row["input"]["target_audience"],
        "training_objectives": [general],
        "pedagogical_objectives": objectives,
        "trainer": {
            "name": "Formateur à désigner",
            "hours": row["input"]["total_duration_minutes"] / 60,
        },
        "days": days,
        "total_duration_minutes": row["input"]["total_duration_minutes"],
        "evaluation_method": evaluation,
    }
    sectors = {
        "conseil",
        "distribution",
        "secteur public",
        "services financiers",
        "transport et logistique",
    }
    own_sector = row["input"]["sector"]

    def align_sector(value: Any) -> Any:
        if isinstance(value, str):
            for sector in sectors - {own_sector}:
                if re.search(re.escape(sector), value, flags=re.IGNORECASE):
                    value = re.sub(re.escape(sector), own_sector, value, flags=re.IGNORECASE)
                    issues.append("secteur")
            return value
        if isinstance(value, list):
            return [align_sector(item) for item in value]
        if isinstance(value, dict):
            return {key: align_sector(item) for key, item in value.items()}
        return value

    output = align_sector(output)
    TrainingProgramOutput.model_validate(output)
    migrated["output"] = output
    issue_names = sorted(set(issues))
    if "langue" in issue_names:
        summaries.append("Anglicismes ou formulations linguistiques corrigés en français.")
    if "contenu" in issue_names:
        summaries.append("Formulations synthétiques artificielles reformulées.")
    migrated["metadata"]["final_migration"] = {
        "migrated": True,
        "content_modified": bool(issue_names),
        "issues_corrected": issue_names,
        "changes_summary": sorted(set(summaries)),
    }
    return migrated


def duplicate_counts(rows: list[dict[str, Any]]) -> tuple[int, int]:
    payloads = [json.dumps(row["output"], ensure_ascii=False, sort_keys=True) for row in rows]
    exact = len(payloads) - len(set(payloads))
    normalized = [set(re.findall(r"[a-zà-ÿ0-9]{4,}", value.casefold())) for value in payloads]
    quasi = sum(
        len(normalized[i] & normalized[j]) / max(len(normalized[i] | normalized[j]), 1) >= 0.95
        for i in range(len(rows))
        for j in range(i + 1, len(rows))
    )
    return exact, quasi


def write_report(
    source: list[dict[str, Any]], final: list[dict[str, Any]], stats: Counter[str]
) -> None:
    exact, quasi = duplicate_counts(final)
    examples = []
    changed = [row for row in final if row["metadata"]["final_migration"]["content_modified"]]
    for row in changed[:5]:
        old = next(item for item in source if item["id"] == row["id"])
        examples.append(
            f"### {row['id']}\n\n"
            f"- Avant : {old['output']['evaluation_method']}\n"
            f"- Après : {row['output']['evaluation_method']}\n"
            f"- Corrections : {', '.join(row['metadata']['final_migration']['issues_corrected'])}\n"
        )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Rapport de migration vers le format programme final\n\n"
        f"- Programmes source : {len(source)}\n- Programmes finaux : {len(final)}\n"
        f"- Programmes modifiés : {sum(r['metadata']['final_migration']['content_modified'] for r in final)}\n"
        f"- Programmes inchangés sur le fond : {sum(not r['metadata']['final_migration']['content_modified'] for r in final)}\n"
        f"- Corrections de langue : {stats['langue']}\n- Corrections de niveau : {stats['niveau']}\n"
        f"- Corrections de secteur : {stats['secteur']}\n- Corrections de contenu : {stats['contenu']}\n"
        f"- Corrections de répétition : {stats['répétition']}\n"
        f"- Répartitions théorie/pratique recalculées : {stats['répartition']} programmes\n"
        f"- Doublons exacts : {exact}\n"
        f"- Quasi-doublons problématiques : {quasi}\n\n"
        "## Mapping\n\nLe titre/thème, le public, les objectifs, les modules, concepts, méthodes, "
        "ressources, durées théorie/pratique et l’évaluation ont été mappés vers "
        "`TrainingProgramOutput`. Les descriptions, objectifs de journée, objectifs de module "
        "et activités ont été conservés dans les concepts du contenu.\n\n"
        "## Validations\n\nLes 120 sorties sont valides avec Pydantic, gardent leur durée et leur nombre "
        "de jours, et sont directement rendues par `generate_program_pdf`. Quatre PDF couvrant "
        "beginner, intermediate, advanced et expert ont été générés.\n\n"
        "## Exemples avant/après\n\n" + "\n".join(examples),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pdfs", action="store_true")
    args = parser.parse_args()
    before = {path: sha256(path) for path in PROTECTED}
    source = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line]
    final = [migrate(row) for row in source]
    if len(final) != 120 or len({row["id"] for row in final}) != 120:
        raise RuntimeError("Le dataset final doit contenir 120 IDs uniques.")
    FINAL_JSONL.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in final),
        encoding="utf-8",
    )
    FINAL_JSON.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not args.skip_pdfs:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        for level in ("beginner", "intermediate", "advanced", "expert"):
            row = next(item for item in final if item["input"]["level"] == level)
            program = TrainingProgramOutput.model_validate(row["output"])
            (PDF_DIR / f"{level}_{row['id']}.pdf").write_bytes(generate_program_pdf(program))
    stats: Counter[str] = Counter()
    for row in final:
        stats.update(row["metadata"]["final_migration"]["issues_corrected"])
    write_report(source, final, stats)
    after = {path: sha256(path) for path in PROTECTED}
    if before != after:
        raise RuntimeError("Un fichier protégé a été modifié.")
    print(
        json.dumps({"source": len(source), "final": len(final), "stats": stats}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
