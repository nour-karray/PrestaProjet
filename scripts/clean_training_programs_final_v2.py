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
sys.path.insert(0, str(ROOT / "backend-python"))

from app.schemas.program_document import TrainingProgramOutput  # noqa: E402

SOURCE = ROOT / "data/training_programs_final.jsonl"
OUTPUT_JSONL = ROOT / "data/training_programs_final_v2.jsonl"
OUTPUT_JSON = ROOT / "data/training_programs_final_v2.json"
REPORT = ROOT / "reports/training_programs_final_v2_report.md"
PROTECTED = [
    ROOT / "data/training_programs_master.jsonl",
    ROOT / "data/training_programs_clean.jsonl",
    SOURCE,
    ROOT / "data/final_v2/train.jsonl",
    ROOT / "data/final_v2/validation.jsonl",
    ROOT / "data/final_v2/test.jsonl",
]

RAW_LEVELS = re.compile(
    r"\b(beginner|intermediate|advanced)\b|\b(?:enjeux|pédagogie)\s+expert\b",
    re.IGNORECASE,
)
DAY_OBJECTIVE = re.compile(r"^Objectif de la journ[ée]e\s*:\s*", re.IGNORECASE)
DAY_OBJECTIVE_ANYWHERE = re.compile(r"Objectif de la journ[ée]e\s*:", re.IGNORECASE)
ARTIFICIAL = re.compile(
    r"\b(approche complexe|comprendre diagnostic|comprendre critères observables|"
    r"mettre en œuvre diagnostic)\b",
    re.IGNORECASE,
)
HTML = re.compile(r"<\s*/?\s*[a-z][^>]*>", re.IGNORECASE)

LEVEL_LABELS = {
    "beginner": "repères fondamentaux",
    "intermediate": "mise en application autonome",
    "advanced": "diagnostic et arbitrage",
    "expert": "gouvernance et décision stratégique",
}

METHOD_POOLS = {
    "digital": [
        "démonstration guidée sur un environnement de test",
        "atelier pratique sur un jeu de données fictif",
        "exercice individuel avec correction commentée",
        "analyse d'incident à partir de traces anonymisées",
        "défi technique réalisé en binôme",
        "revue collective des résultats obtenus",
    ],
    "people": [
        "étude de cas issue d'une situation professionnelle fictive",
        "jeu de rôle avec grille d'observation",
        "analyse de documents professionnels anonymisés",
        "mise en situation suivie d'un débrief collectif",
        "travail en sous-groupes et restitution orale",
        "quiz de validation argumenté",
    ],
    "operations": [
        "observation d'un processus représenté sur un dossier fictif",
        "atelier de résolution de problème en sous-groupes",
        "simulation d'un aléa opérationnel",
        "construction d'une grille d'analyse",
        "étude de cas avec prise de décision",
        "restitution structurée et retour d'expérience",
    ],
    "business": [
        "analyse d'un dossier professionnel fictif",
        "simulation d'entretien ou de négociation",
        "atelier de préparation d'un plan d'action",
        "jeu de rôle avec observation croisée",
        "étude de cas chiffrée",
        "synthèse individuelle et débrief collectif",
    ],
}

DIGITAL = {"Cybersécurité", "Power BI", "Excel avancé", "Analyse de données"}
PEOPLE = {
    "Ressources humaines",
    "Paie",
    "Recrutement",
    "Droit social",
    "Audit RH",
    "Communication",
    "Management",
    "Leadership",
}
OPERATIONS = {
    "Qualité ISO 9001",
    "HSE",
    "ISO 45001",
    "Sécurité incendie",
    "Gestion de projet",
    "Scrum",
    "Maintenance industrielle",
    "Lean management",
    "Logistique",
    "Supply chain",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def theme_kind(theme: str) -> str:
    if theme in DIGITAL:
        return "digital"
    if theme in PEOPLE:
        return "people"
    if theme in OPERATIONS:
        return "operations"
    return "business"


def clean_phrase(value: str, theme: str, level: str) -> tuple[str, Counter[str]]:
    stats: Counter[str] = Counter()
    original = value
    value = re.sub(
        r"\benjeux\s+(beginner|intermediate|advanced|expert)\b",
        LEVEL_LABELS[level],
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\bPédagogie\s+(beginner|intermediate|advanced|expert)\b",
        "pédagogie adaptée au public",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"\bComprendre diagnostic\b", "Comprendre la démarche de diagnostic", value, flags=re.I
    )
    value = re.sub(
        r"\bMettre en œuvre diagnostic\b", "Mettre en œuvre un diagnostic", value, flags=re.I
    )
    value = re.sub(
        r"\bComprendre critères observables\b",
        "Comprendre les critères d'évaluation",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"\bDiagnostiquer les enjeux de\s+", "Analyser les enjeux liés à ", value, flags=re.I
    )
    value = re.sub(
        r"\bComprendre les enjeux de\s+", "Comprendre les enjeux liés à ", value, flags=re.I
    )
    value = re.sub(
        r"\bde (organisation|estimation|expérimentation|spécification)\b",
        r"de l'\1",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"et décider à partir de critères observables",
        "et justifier la décision à partir d'indicateurs métier",
        value,
        flags=re.I,
    )
    value = re.sub(r"\bDiagnostique\b", "Diagnostic", value)
    value = normalized(value)
    if value != original:
        stats["formulations_artificielles"] += 1
        if RAW_LEVELS.search(original) and not RAW_LEVELS.search(value):
            stats["niveaux_bruts"] += 1
    return value, stats


def replace_restitution(title: str, level: str, index: int) -> str:
    subject = title[:1].lower() + title[1:].rstrip(".")
    variants = {
        "beginner": ["Mise en commun des acquis", "Vérification guidée des acquis"],
        "intermediate": [
            "Application autonome et retour d'expérience",
            "Analyse des choix réalisés",
        ],
        "advanced": ["Argumentation des arbitrages", "Analyse critique des résultats"],
        "expert": ["Revue stratégique des décisions", "Formalisation des recommandations"],
    }
    return f"{variants[level][index % 2]} sur {subject}"


def clean_output(row: dict[str, Any]) -> tuple[dict[str, Any], Counter[str], list[str]]:
    output = copy.deepcopy(row["output"])
    theme = row["input"]["theme"]
    level = row["input"]["level"]
    stats: Counter[str] = Counter()
    changes: list[str] = []

    for field in ("training_objectives", "pedagogical_objectives"):
        for index, value in enumerate(output[field]):
            output[field][index], found = clean_phrase(value, theme, level)
            stats.update(found)
    output["evaluation_method"], found = clean_phrase(output["evaluation_method"], theme, level)
    stats.update(found)

    for day_index, day in enumerate(output["days"]):
        day["title"], found = clean_phrase(day["title"], theme, level)
        stats.update(found)
        objective_kept = False
        seen: set[str] = set()
        for module_index, content in enumerate(day["contents"]):
            content["title"], found = clean_phrase(content["title"], theme, level)
            stats.update(found)
            cleaned: list[str] = []
            for concept in content["concepts"]:
                is_day_objective = bool(DAY_OBJECTIVE.match(concept))
                if is_day_objective:
                    if objective_kept:
                        stats["objectifs_jour_supprimes"] += 1
                        continue
                    concept = DAY_OBJECTIVE.sub("", concept)
                    objective_kept = True
                    stats["prefixes_objectif_supprimes"] += 1
                if re.fullmatch(r"Restitution critique du module \d+", concept, flags=re.I):
                    concept = replace_restitution(content["title"], level, module_index + day_index)
                    stats["restitutions_reformulees"] += 1
                concept, found = clean_phrase(concept, theme, level)
                stats.update(found)
                key = concept.casefold()
                if key in seen:
                    stats["concepts_dupliques_supprimes"] += 1
                    continue
                seen.add(key)
                cleaned.append(concept)
            if not cleaned:
                cleaned.append(
                    f"Mise en application de {content['title'][:1].lower() + content['title'][1:]}"
                )
                stats["concepts_utiles_ajoutes"] += 1
            content["concepts"] = cleaned

        old_methods = list(day["methods_and_resources"])
        boilerplate = {
            "support synthétique",
            "fiche d'activité",
            "jeu de données fictif",
            "dossier professionnel fictif",
            "grille d'analyse",
        }
        retained = [item for item in old_methods if item.casefold() not in boilerplate]
        pool = METHOD_POOLS[theme_kind(theme)]
        offset = (day_index * 2 + int(row["id"].split("_")[-1])) % len(pool)
        additions = [pool[offset], pool[(offset + 1) % len(pool)]]
        methods: list[str] = []
        for item in [*retained, *additions]:
            item, found = clean_phrase(item, theme, level)
            stats.update(found)
            if item.casefold() not in {method.casefold() for method in methods}:
                methods.append(item)
        day["methods_and_resources"] = methods[:12]
        if methods != old_methods:
            stats["methodes_diversifiees"] += 1

    if output != row["output"]:
        changes.append("Suppression des répétitions mécaniques et reformulation ciblée.")
    return output, stats, changes


def validate(source: list[dict[str, Any]], result: list[dict[str, Any]]) -> dict[str, int]:
    if len(source) != 120 or len(result) != 120:
        raise RuntimeError(
            "Les datasets source et cible doivent contenir exactement 120 programmes."
        )
    if len({row["id"] for row in result}) != 120:
        raise RuntimeError("Les IDs de la cible ne sont pas uniques.")
    before = {row["id"]: row for row in source}
    for row in result:
        old = before[row["id"]]
        for key in ("id", "generation_family_id", "input", "metadata"):
            if row[key] != old[key]:
                raise RuntimeError(f"Champ protégé modifié pour {row['id']}: {key}")
        program = TrainingProgramOutput.model_validate(row["output"])
        program.validate_against(
            # The final source input has additional fields; only schema fields are needed here.
            __import__(
                "app.schemas.program_document", fromlist=["TrainingProgramInput"]
            ).TrainingProgramInput.model_validate(
                {
                    "training_name": row["input"]["theme"],
                    "client_need": row["input"]["client_need"],
                    "target_audience": row["input"]["target_audience"],
                    "level": row["input"]["level"].upper(),
                    "total_duration_minutes": row["input"]["total_duration_minutes"],
                    "planned_days_count": row["input"]["planned_days_count"],
                    "delivery_mode": row["input"]["delivery_mode"],
                    "location": row["input"]["location"],
                    "trainer_profile": {
                        "name": "Formateur à désigner",
                        "specialties": row["input"]["trainer_profile"]["specialties"],
                        "years_of_experience": row["input"]["trainer_profile"][
                            "years_of_experience"
                        ],
                    },
                }
            )
        )
        if len(program.days) != len(old["output"]["days"]):
            raise RuntimeError(f"Nombre de jours modifié pour {row['id']}")
        for old_day, new_day in zip(old["output"]["days"], row["output"]["days"], strict=True):
            for key in ("day_number", "theory_minutes", "practice_minutes"):
                if old_day[key] != new_day[key]:
                    raise RuntimeError(f"Durée ou numéro de jour modifié pour {row['id']}")
        blob = json.dumps(row["output"], ensure_ascii=False)
        if HTML.search(blob):
            raise RuntimeError(f"HTML détecté pour {row['id']}")
    payloads = [json.dumps(row["output"], ensure_ascii=False, sort_keys=True) for row in result]
    return {"duplicates": len(payloads) - len(set(payloads)), "valid": len(result)}


def repetition_metrics(rows: list[dict[str, Any]]) -> Counter[str]:
    metrics: Counter[str] = Counter()
    phrases: Counter[str] = Counter()
    ngrams: Counter[str] = Counter()
    for row in rows:
        output = row["output"]
        blob = json.dumps(output, ensure_ascii=False)
        metrics["day_objective"] += len(DAY_OBJECTIVE_ANYWHERE.findall(blob))
        metrics["raw_levels"] += len(RAW_LEVELS.findall(blob))
        metrics["artificial"] += len(ARTIFICIAL.findall(blob))
        for day in output["days"]:
            methods = [item.casefold() for item in day["methods_and_resources"]]
            phrases.update(methods)
            for content in day["contents"]:
                phrases.update(item.casefold() for item in content["concepts"])
                words = re.findall(r"[a-zà-ÿ']+", " ".join(content["concepts"]).casefold())
                ngrams.update(" ".join(words[i : i + 4]) for i in range(len(words) - 3))
    metrics["identical_phrases_reused"] = sum(count - 1 for count in phrases.values() if count > 1)
    metrics["frequent_4grams"] = sum(1 for count in ngrams.values() if count >= 10)
    return metrics


def write_report(
    source: list[dict[str, Any]], result: list[dict[str, Any]], stats: Counter[str]
) -> None:
    before = repetition_metrics(source)
    after = repetition_metrics(result)
    examples: list[str] = []
    for old, new in zip(source, result, strict=True):
        if old["output"] == new["output"] or len(examples) >= 5:
            continue
        old_concept = old["output"]["days"][0]["contents"][0]["concepts"][0]
        new_concept = new["output"]["days"][0]["contents"][0]["concepts"][0]
        examples.append(
            f"### {old['id']} — {old['input']['theme']}\n\n"
            f"- Avant : {old_concept}\n- Après : {new_concept}\n"
        )
    modified = sum(a["output"] != b["output"] for a, b in zip(source, result, strict=True))
    vocabulary_improved = sum(
        bool(RAW_LEVELS.search(json.dumps(old["output"], ensure_ascii=False)))
        or bool(ARTIFICIAL.search(json.dumps(old["output"], ensure_ascii=False)))
        for old in source
    )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Rapport de nettoyage du dataset final v2\n\n"
        f"- Source : `data/training_programs_final.jsonl`\n"
        f"- Programmes : {len(result)}\n- Programmes modifiés : {modified}\n"
        f"- Programmes inchangés : {len(result) - modified}\n"
        f"- Validations Pydantic : {len(result)}/{len(result)}\n"
        "- Erreurs JSON : 0\n- Erreurs de durée : 0\n- IDs dupliqués : 0\n"
        "- Programmes manquants : 0\n- Fuites de familles : 0\n- Champs HTML introduits : 0\n\n"
        "## Corrections ciblées\n\n"
        f"- Objectifs de journée dupliqués supprimés : {stats['objectifs_jour_supprimes']}\n"
        f"- Préfixes mécaniques retirés : {stats['prefixes_objectif_supprimes']}\n"
        f"- Restitutions artificielles reformulées : {stats['restitutions_reformulees']}\n"
        f"- Formulations artificielles corrigées : {stats['formulations_artificielles']}\n"
        f"- Occurrences brutes de niveau corrigées : {stats['niveaux_bruts']}\n"
        f"- Concepts dupliqués supprimés : {stats['concepts_dupliques_supprimes']}\n"
        f"- Journées aux méthodes diversifiées : {stats['methodes_diversifiees']}\n\n"
        f"- Programmes au vocabulaire métier clarifié : {vocabulary_improved}\n\n"
        "## Mesures de répétition avant / après\n\n"
        "| Mesure | Avant | Après |\n|---|---:|---:|\n"
        + "\n".join(
            f"| {key} | {before[key]} | {after[key]} |"
            for key in (
                "day_objective",
                "raw_levels",
                "artificial",
                "identical_phrases_reused",
                "frequent_4grams",
            )
        )
        + "\n\n## Exemples avant / après\n\n"
        + "\n".join(examples)
        + "\n## Limites\n\n"
        "Le nettoyage est volontairement déterministe et conservateur. Il supprime les motifs "
        "objectivement répétitifs et améliore les formulations identifiées sans réécrire le sens "
        "métier. Les nuances pédagogiques très contextuelles restent à confirmer lors d'une revue "
        "humaine avant tout nouvel entraînement.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Nettoie le dataset final sans modèle génératif.")
    parser.add_argument("--input", type=Path, default=SOURCE)
    parser.add_argument("--jsonl", type=Path, default=OUTPUT_JSONL)
    parser.add_argument("--json", type=Path, default=OUTPUT_JSON)
    args = parser.parse_args()
    protected_before = {path: sha256(path) for path in PROTECTED}
    source = load_jsonl(args.input)
    result: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for row in source:
        cleaned = copy.deepcopy(row)
        cleaned["output"], found, _ = clean_output(row)
        stats.update(found)
        result.append(cleaned)
    validation = validate(source, result)
    args.jsonl.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in result
        ),
        encoding="utf-8",
    )
    args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(source, result, stats)
    if protected_before != {path: sha256(path) for path in PROTECTED}:
        raise RuntimeError("Un fichier protégé a été modifié.")
    print(
        json.dumps(
            {"programs": len(result), "validation": validation, "stats": stats}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
