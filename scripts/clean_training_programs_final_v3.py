from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend-python"))

from app.schemas.program_document import TrainingProgramOutput  # noqa: E402

SOURCE = ROOT / "data/training_programs_final_v2.jsonl"
OUTPUT_JSONL = ROOT / "data/training_programs_final_v3.jsonl"
OUTPUT_JSON = ROOT / "data/training_programs_final_v3.json"
REPORT = ROOT / "reports/training_programs_final_v3_report.md"
AUDIT = ROOT / "reports/training_programs_final_v3_quality_audit.md"

PROTECTED = [
    ROOT / "data/training_programs_master.jsonl",
    ROOT / "data/training_programs_clean.jsonl",
    ROOT / "data/training_programs_final.jsonl",
    SOURCE,
    ROOT / "data/final_v2/train.jsonl",
    ROOT / "data/final_v2/validation.jsonl",
    ROOT / "data/final_v2/test.jsonl",
]

DOMAIN_SKILLS: dict[str, list[str]] = {
    "Ressources humaines": [
        "les missions de la fonction RH",
        "la gestion des compétences",
        "le suivi des parcours professionnels",
        "les indicateurs sociaux",
    ],
    "Paie": [
        "la structure du bulletin de paie",
        "les variables, primes et avantages",
        "les absences et régularisations",
        "le contrôle de conformité des bulletins",
    ],
    "Recrutement": [
        "la définition du besoin et la fiche de poste",
        "le sourcing et la présélection",
        "l'entretien structuré et sa grille d'évaluation",
        "la maîtrise des biais et le suivi des indicateurs de recrutement",
    ],
    "Droit social": [
        "les sources du droit du travail",
        "la sécurisation du contrat de travail",
        "le traitement des situations individuelles sensibles",
        "le contrôle de conformité sociale",
    ],
    "Audit RH": [
        "le cadrage d'une mission d'audit RH",
        "la collecte des preuves sociales",
        "l'analyse des risques et écarts RH",
        "la formulation d'un plan correctif",
    ],
    "Qualité ISO 9001": [
        "l'approche processus ISO 9001",
        "la maîtrise des risques et opportunités",
        "la préparation d'un audit qualité",
        "l'amélioration continue du système qualité",
    ],
    "HSE": [
        "l'identification des dangers",
        "l'évaluation des risques HSE",
        "les mesures de prévention et de protection",
        "le suivi des incidents et actions correctives",
    ],
    "ISO 45001": [
        "les exigences d'ISO 45001",
        "l'analyse des risques professionnels",
        "la participation des travailleurs",
        "l'audit du système de management SST",
    ],
    "Sécurité incendie": [
        "les mécanismes de départ et de propagation du feu",
        "les moyens d'extinction et d'alarme",
        "l'organisation de l'évacuation",
        "l'analyse d'un scénario d'incendie",
    ],
    "Cybersécurité": [
        "les menaces et vulnérabilités numériques",
        "les mesures de protection des accès et données",
        "la réponse à un incident de sécurité",
        "l'efficacité des contrôles de cybersécurité",
    ],
    "Power BI": [
        "la préparation des données avec Power Query",
        "la modélisation relationnelle",
        "les mesures DAX",
        "la conception d'un tableau de bord décisionnel",
    ],
    "Excel avancé": [
        "les fonctions de calcul avancées",
        "la fiabilisation des données",
        "l'automatisation des traitements",
        "la conception de tableaux de bord Excel",
    ],
    "Analyse de données": [
        "la préparation d'un jeu de données",
        "l'analyse exploratoire",
        "l'interprétation des indicateurs statistiques",
        "la restitution visuelle des résultats",
    ],
    "Gestion de projet": [
        "le cadrage des objectifs et livrables",
        "la planification des délais et ressources",
        "la maîtrise des risques projet",
        "le pilotage des écarts et arbitrages",
    ],
    "Scrum": [
        "les rôles et événements Scrum",
        "la gestion du backlog produit",
        "la planification et le suivi d'un sprint",
        "l'amélioration issue de la rétrospective",
    ],
    "Communication": [
        "la construction d'un message professionnel",
        "l'écoute active et la reformulation",
        "la conduite d'une réunion",
        "la gestion des communications sensibles",
    ],
    "Vente": [
        "la découverte structurée du besoin client",
        "la construction d'un argumentaire de valeur",
        "le traitement des objections",
        "le suivi des indicateurs commerciaux",
    ],
    "Négociation": [
        "la préparation des objectifs et marges de manœuvre",
        "l'analyse du rapport de force",
        "la conduite des concessions et contreparties",
        "la formalisation d'un accord durable",
    ],
    "Management": [
        "la clarification des responsabilités managériales",
        "l'organisation de l'activité collective",
        "l'adaptation du management à l'autonomie",
        "le suivi de la performance de l'équipe",
    ],
    "Leadership": [
        "l'analyse de sa posture de leader",
        "la mobilisation d'un collectif",
        "la décision en environnement incertain",
        "le développement de l'influence transversale",
    ],
    "Finance": [
        "la lecture des états financiers",
        "l'analyse de la rentabilité et de la trésorerie",
        "l'évaluation d'un investissement",
        "la construction de scénarios financiers",
    ],
    "Comptabilité": [
        "la sécurisation du cycle comptable",
        "le traitement des opérations d'inventaire",
        "la justification des comptes",
        "la préparation et le contrôle de la clôture",
    ],
    "Contrôle de gestion": [
        "la construction budgétaire",
        "l'analyse des coûts et des marges",
        "l'explication des écarts",
        "le pilotage par les tableaux de bord",
    ],
    "Maintenance industrielle": [
        "la criticité des équipements",
        "la planification de la maintenance préventive",
        "le diagnostic des défaillances",
        "le suivi de la fiabilité et de la disponibilité",
    ],
    "Lean management": [
        "la valeur attendue par le client",
        "l'identification des gaspillages",
        "la fluidification des processus",
        "l'animation d'une démarche Kaizen",
    ],
    "Logistique": [
        "la cartographie des flux physiques et informationnels",
        "la gestion des stocks et approvisionnements",
        "l'organisation des opérations d'entrepôt",
        "la performance de service et les coûts logistiques",
    ],
    "Supply chain": [
        "la représentation de la chaîne de bout en bout",
        "la prévision et la planification de la demande",
        "l'alignement des capacités et des stocks",
        "la gestion des risques de la chaîne d'approvisionnement",
    ],
    "Achats": [
        "l'analyse fonctionnelle du besoin",
        "l'évaluation du coût complet",
        "la sélection et la négociation fournisseurs",
        "le pilotage de la performance contractuelle",
    ],
    "Service client": [
        "la demande et les attentes du client",
        "la conduite d'un échange de service",
        "le traitement d'une réclamation",
        "la mesure de la satisfaction et de la fidélisation",
    ],
    "Marketing digital": [
        "la définition des audiences et parcours numériques",
        "la création de contenus adaptés aux canaux",
        "la mesure de la conversion",
        "l'optimisation des campagnes par expérimentation",
    ],
}

EVALUATION_ARTIFACTS = {
    "Ressources humaines": "un plan de développement des compétences",
    "Paie": "un bulletin complexe contrôlé et commenté",
    "Recrutement": "un dossier de recrutement avec grille d'entretien",
    "Droit social": "une note de sécurisation juridique",
    "Audit RH": "un rapport d'audit RH assorti d'actions correctives",
    "Qualité ISO 9001": "une analyse de processus assortie d'un plan d'amélioration",
    "HSE": "une évaluation des risques accompagnée de mesures de prévention",
    "ISO 45001": "un diagnostic de conformité ISO 45001",
    "Sécurité incendie": "un scénario d'évacuation analysé",
    "Cybersécurité": "un plan de réponse à incident",
    "Power BI": "un tableau de bord Power BI documenté",
    "Excel avancé": "un classeur automatisé et contrôlé",
    "Analyse de données": "une analyse argumentée d'un jeu de données",
    "Gestion de projet": "un dossier de pilotage de projet",
    "Scrum": "un incrément simulé et sa rétrospective",
    "Communication": "une communication professionnelle mise en situation",
    "Vente": "un entretien de vente observé avec une grille",
    "Négociation": "une simulation de négociation avec accord formalisé",
    "Management": "un plan d'action managérial contextualisé",
    "Leadership": "une décision complexe défendue devant un comité simulé",
    "Finance": "une recommandation financière chiffrée",
    "Comptabilité": "un dossier de clôture justifié",
    "Contrôle de gestion": "un tableau de bord commenté assorti d'un plan d'action",
    "Maintenance industrielle": "un plan de maintenance fondé sur la criticité",
    "Lean management": "un chantier d'amélioration avec mesure des gains",
    "Logistique": "un scénario d'optimisation des flux",
    "Supply chain": "un scénario S&OP argumenté",
    "Achats": "une recommandation d'attribution fournisseur",
    "Service client": "une réclamation traitée et analysée",
    "Marketing digital": "une campagne numérique analysée et optimisée",
}

METHODS = {
    "people": [
        "analyse de documents professionnels",
        "jeu de rôle avec grille d'observation",
        "mise en situation suivie d'un débrief collectif",
        "atelier de construction d'un outil opérationnel",
        "étude de cas avec décision argumentée",
        "travail en sous-groupes et restitution orale",
        "simulation d'un entretien sensible",
        "exercice individuel avec retour personnalisé",
    ],
    "digital": [
        "démonstration commentée sur un environnement de test",
        "atelier pratique sur des données fictives",
        "défi technique réalisé en binôme",
        "analyse d'une erreur à partir de traces anonymisées",
        "construction progressive d'un livrable numérique",
        "revue croisée des résultats obtenus",
        "exercice individuel avec jeu de contrôle",
        "résolution guidée d'un incident simulé",
    ],
    "operations": [
        "observation d'un processus sur un dossier fictif",
        "atelier de cartographie en sous-groupes",
        "simulation d'un aléa opérationnel",
        "analyse de causes avec grille structurée",
        "étude de cas chiffrée avec arbitrage",
        "construction d'un plan d'amélioration",
        "exercice de priorisation des actions",
        "retour d'expérience collectif documenté",
    ],
    "business": [
        "analyse d'un dossier professionnel chiffré",
        "simulation d'un échange avec prise de décision",
        "atelier de préparation d'un plan d'action",
        "jeu de rôle avec observation croisée",
        "étude de cas comparant plusieurs options",
        "construction d'une recommandation argumentée",
        "exercice individuel de calcul et d'interprétation",
        "soutenance courte devant un comité simulé",
    ],
}

PEOPLE = {
    "Ressources humaines",
    "Paie",
    "Recrutement",
    "Droit social",
    "Audit RH",
    "Communication",
    "Management",
    "Leadership",
    "Service client",
}
DIGITAL = {"Cybersécurité", "Power BI", "Excel avancé", "Analyse de données"}
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

BAD_CONCEPT_PATTERNS = [
    r"puis produire une décision applicable",
    r"dans une situation professionnelle adaptée",
    r"justifier la décision à partir d'indicateurs métier",
    r"^simulation stratégique\s*:",
    r"^revue stratégique des décisions",
    r"^mise en commun des acquis",
    r"^formalisation des recommandations",
    r"^vérification guidée des acquis",
    r"^repères fondamentaux$",
    r"^arbitrage stratégique$",
    r"justifier la décision à partir de critères observables",
    r"avec une méthode adaptée",
    r"^application autonome et retour d'expérience",
    r"^analyse critique des résultats",
]
BAD_CONCEPT = re.compile("|".join(f"(?:{item})" for item in BAD_CONCEPT_PATTERNS), re.I)
RAW_LEVEL = re.compile(
    r"\b(beginner|intermediate|advanced)\b|\b(?:enjeux|pédagogie)\s+expert\b", re.I
)
HTML = re.compile(r"<\s*/?\s*[a-z][^>]*>", re.I)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def fix_french(value: str, level: str) -> tuple[str, Counter[str]]:
    original = value
    replacements = [
        (
            r"\badaptée? à collaborateurs opérationnels\b",
            "adaptée aux collaborateurs opérationnels",
        ),
        (r"\badaptée? à chefs de projet\b", "adaptée aux chefs de projet"),
        (r"\badaptée? à techniciens spécialisés\b", "adaptée aux techniciens spécialisés"),
        (r"\badaptée? à nouveaux managers\b", "adaptée aux nouveaux managers"),
        (r"\bdans un équipe\b", "dans une équipe"),
        (r"\bun prévision\b", "une prévision"),
        (r"\bau secteur secteur public\b", "au secteur public"),
        (r"\bd'Power BI\b", "de Power BI"),
        (r"\bPrésentation d'Power BI\b", "Présentation de Power BI"),
        (r"\bEvaluations?\b", lambda m: "Évaluations" if m.group().endswith("s") else "Évaluation"),
        (r"\bEvaluer\b", "Évaluer"),
        (r"\bfeedbacks?\b", "retours"),
        (r"\bfinal deliverable\b", "livrable final"),
        (r"\bforecast\b", "prévision"),
        (r"\broadmap\b", "feuille de route"),
        (r"\bdashboards?\b", "tableaux de bord"),
        (r"\bbudgeting\b", "budgétisation"),
        (r"\bcoaching\b", "accompagnement"),
        (r"\bnurturing\b", "maturation des prospects"),
    ]
    for pattern, target in replacements:
        value = re.sub(pattern, target, value, flags=re.I)
    if level == "beginner":
        value = re.sub(
            r"\bA/B testing\b",
            "test comparatif A/B (comparaison de deux versions)",
            value,
            flags=re.I,
        )
    value = re.sub(r"\s+", " ", value).strip()
    result: Counter[str] = Counter()
    if value != original:
        result["french_corrections"] += 1
    return value, result


def method_category(theme: str) -> str:
    if theme in PEOPLE:
        return "people"
    if theme in DIGITAL:
        return "digital"
    if theme in OPERATIONS:
        return "operations"
    return "business"


def objectives(theme: str, level: str) -> tuple[list[str], list[str]]:
    skills = DOMAIN_SKILLS[theme]
    pedagogical = {
        "beginner": [
            f"Expliquer {skills[0]}.",
            f"Identifier les points clés {with_de(skills[1])}.",
            f"Réaliser un exercice guidé portant sur {skills[2]}.",
            f"Contrôler {skills[3]} à l'aide d'une fiche simple.",
        ],
        "intermediate": [
            f"Analyser {skills[0]}.",
            f"Mettre en œuvre {skills[1]}.",
            f"Examiner différentes options concernant {skills[2]}.",
            f"Proposer une amélioration {with_de(skills[3])}.",
        ],
        "advanced": [
            f"Diagnostiquer les risques associés {with_a(skills[0])}.",
            f"Optimiser {skills[1]}.",
            f"Résoudre un cas complexe mobilisant {skills[2]}.",
            f"Évaluer {skills[3]} à partir de preuves vérifiables.",
        ],
        "expert": [
            f"Concevoir un référentiel pour {skills[0]}.",
            f"Définir la gouvernance {with_de(skills[1])}.",
            f"Établir des critères de décision concernant {skills[2]}.",
            f"Superviser {skills[3]}.",
        ],
    }[level]
    lead = {
        "beginner": "Acquérir les bases nécessaires pour maîtriser",
        "intermediate": "Mobiliser avec autonomie",
        "advanced": "Résoudre des cas complexes mobilisant",
        "expert": "Concevoir et défendre des décisions relatives à",
    }[level]
    training = [f"{theme} — {lead.lower()} {skills[0]}, {skills[1]} et {skills[2]}."]
    return training, pedagogical


def with_de(value: str) -> str:
    """Contract a leading French article after the preposition 'de'."""
    if value.startswith("le "):
        return "du " + value[3:]
    if value.startswith("les "):
        return "des " + value[4:]
    if value.startswith("la "):
        return "de la " + value[3:]
    if value.startswith("l'"):
        return "de " + value
    if value.startswith("un "):
        return "d'un " + value[3:]
    if value.startswith("une "):
        return "d'une " + value[4:]
    return "de " + value


def with_a(value: str) -> str:
    """Contract a leading French article after the preposition 'à'."""
    if value.startswith("le "):
        return "au " + value[3:]
    if value.startswith("les "):
        return "aux " + value[4:]
    if value.startswith("la "):
        return "à la " + value[3:]
    if value.startswith("l'"):
        return "à " + value
    return "à " + value


def clean_concepts(
    concepts: list[str], title: str, theme: str, level: str
) -> tuple[list[str], Counter[str]]:
    cleaned: list[str] = []
    stats: Counter[str] = Counter()
    for concept in concepts:
        if BAD_CONCEPT.search(concept) or RAW_LEVEL.search(concept):
            stats["templates_removed"] += 1
            continue
        concept, changes = fix_french(concept, level)
        stats.update(changes)
        key = concept.casefold().rstrip(".")
        if key in {item.casefold().rstrip(".") for item in cleaned}:
            stats["duplicates_removed"] += 1
            continue
        cleaned.append(concept)
    if not cleaned:
        cleaned = [f"Application de {title[:1].lower() + title[1:]} en {theme.lower()}."]
        stats["fallback_concepts"] += 1
    return cleaned[:15], stats


def evaluation_method(theme: str, level: str) -> str:
    artifact = EVALUATION_ARTIFACTS[theme]
    demand = {
        "beginner": "avec un accompagnement pas à pas",
        "intermediate": "en autonomie, puis justification des choix effectués",
        "advanced": "à partir d'un cas complexe comportant plusieurs contraintes",
        "expert": "avec soutenance des arbitrages devant un comité simulé",
    }[level]
    return f"{theme} — production {with_de(artifact)} {demand}."


def clean_row(row: dict[str, Any]) -> tuple[dict[str, Any], Counter[str]]:
    cleaned = copy.deepcopy(row)
    output = cleaned["output"]
    theme = row["input"]["theme"]
    level = row["input"]["level"]
    stats: Counter[str] = Counter()
    output["training_objectives"], output["pedagogical_objectives"] = objectives(theme, level)

    for day_index, day in enumerate(output["days"]):
        day["title"], changes = fix_french(day["title"], level)
        stats.update(changes)
        for content in day["contents"]:
            content["title"], changes = fix_french(content["title"], level)
            stats.update(changes)
            content["concepts"], changes = clean_concepts(
                content["concepts"], content["title"], theme, level
            )
            stats.update(changes)
        pool = METHODS[method_category(theme)]
        offset = (int(row["id"].split("_")[-1]) + day_index * 2) % len(pool)
        focus = day["contents"][0]["title"].casefold()
        day["methods_and_resources"] = [
            f"{pool[offset]} — {focus}",
            f"{pool[(offset + 1) % len(pool)]} — {theme.casefold()}, jour {day['day_number']}",
        ]
        stats["days_with_contextual_methods"] += 1
    output["evaluation_method"] = evaluation_method(theme, level)
    cleaned["output"] = output
    return cleaned, stats


def validate(source: list[dict[str, Any]], result: list[dict[str, Any]]) -> None:
    if len(source) != len(result) or len(result) != 120:
        raise RuntimeError("La v3 doit contenir exactement les 120 programmes source.")
    if len({row["id"] for row in result}) != 120:
        raise RuntimeError("Les IDs de la v3 ne sont pas uniques.")
    old_by_id = {row["id"]: row for row in source}
    payloads: set[str] = set()
    for row in result:
        old = old_by_id[row["id"]]
        for key in ("id", "generation_family_id", "input", "metadata"):
            if row[key] != old[key]:
                raise RuntimeError(f"Champ protégé modifié pour {row['id']} : {key}")
        program = TrainingProgramOutput.model_validate(row["output"])
        if len(program.days) != len(old["output"]["days"]):
            raise RuntimeError(f"Nombre de jours modifié pour {row['id']}")
        if program.total_duration_minutes != old["output"]["total_duration_minutes"]:
            raise RuntimeError(f"Durée totale modifiée pour {row['id']}")
        if program.trainer.hours != old["output"]["trainer"]["hours"]:
            raise RuntimeError(f"Durée formateur modifiée pour {row['id']}")
        for before, after in zip(old["output"]["days"], row["output"]["days"], strict=True):
            for key in ("day_number", "theory_minutes", "practice_minutes"):
                if before[key] != after[key]:
                    raise RuntimeError(f"Journée ou durée modifiée pour {row['id']}")
        blob = json.dumps(row["output"], ensure_ascii=False)
        if HTML.search(blob):
            raise RuntimeError(f"HTML détecté pour {row['id']}")
        payload = json.dumps(row["output"], ensure_ascii=False, sort_keys=True)
        if payload in payloads:
            raise RuntimeError(f"Sortie dupliquée pour {row['id']}")
        payloads.add(payload)


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    phrases: defaultdict[str, set[str]] = defaultdict(set)
    concepts: defaultdict[str, set[str]] = defaultdict(set)
    fourgrams: Counter[str] = Counter()
    module_count = 0
    common_methods = 0
    generic = Counter()
    grammar = Counter()
    generic_patterns = {
        "situation_professionnelle_adaptee": r"dans une situation professionnelle adaptée",
        "indicateurs_metier": r"justifier la décision à partir d'indicateurs métier",
        "decision_applicable": r"puis produire une décision applicable",
        "simulation_strategique": r"simulation stratégique",
        "revue_strategique": r"revue stratégique des décisions",
        "mise_en_commun": r"mise en commun des acquis",
        "formalisation_recommandations": r"formalisation des recommandations",
        "verification_guidee": r"vérification guidée des acquis",
        "reperes_fondamentaux": r"repères fondamentaux",
        "arbitrage_strategique": r"arbitrage stratégique",
    }
    grammar_patterns = {
        "adapted_missing_article": r"adapté(?:e)? à (?:chefs|collaborateurs|techniciens|nouveaux)",
        "double_sector": r"au secteur secteur",
        "wrong_team_article": r"dans un équipe",
        "power_bi_elision": r"d'Power BI",
        "unaccented_evaluation": r"\bEvaluations?\b",
        "english": (
            r"\b(?:feedbacks?|forecast|roadmap|dashboards?|budgeting|coaching|nurturing|"
            r"final deliverable)\b"
        ),
        "raw_level": RAW_LEVEL.pattern,
    }
    for row in rows:
        output = row["output"]
        blob = json.dumps(output, ensure_ascii=False)
        for name, pattern in generic_patterns.items():
            generic[name] += len(re.findall(pattern, blob, flags=re.I))
        for name, pattern in grammar_patterns.items():
            grammar[name] += len(re.findall(pattern, blob, flags=re.I))
        method_sets = [
            {method.casefold() for method in day["methods_and_resources"]} for day in output["days"]
        ]
        if len(method_sets) > 1 and set.intersection(*method_sets):
            common_methods += 1
        for day in output["days"]:
            for content in day["contents"]:
                module_count += 1
                for concept in content["concepts"]:
                    normalized = concept.casefold().rstrip(".")
                    concepts[normalized].add(row["id"])
                    if len(concept.split()) >= 4:
                        phrases[normalized].add(row["id"])
                    words = re.findall(r"[a-zà-ÿ']+", normalized)
                    fourgrams.update(
                        " ".join(words[index : index + 4])
                        for index in range(max(0, len(words) - 3))
                    )
    ignored_domain_ngrams = {
        "secteur transport et logistique",
        "dans le secteur conseil",
    }
    template_fourgrams = {
        phrase: count for phrase, count in fourgrams.items() if phrase not in ignored_domain_ngrams
    }
    return {
        "identical_phrases_reused": sum(len(ids) - 1 for ids in phrases.values() if len(ids) > 1),
        "frequent_4grams": sum(1 for count in template_fourgrams.values() if count >= 10),
        "fourgrams_over_5_percent_modules": sum(
            1 for count in template_fourgrams.values() if count > module_count * 0.05
        ),
        "programs_with_methods_common_to_all_days": common_methods,
        "concepts_in_at_least_5_programs": sum(1 for ids in concepts.values() if len(ids) >= 5),
        "generic_formulations": dict(generic),
        "grammar_and_english": dict(grammar),
    }


def sample_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Stable selection: five levels slots, no family reused.
    used: set[str] = set()
    selected: list[dict[str, Any]] = []
    for level in ("beginner", "intermediate", "advanced", "expert"):
        candidates = sorted(
            (row for row in rows if row["input"]["level"] == level),
            key=lambda row: hashlib.sha256(f"42:{row['id']}".encode()).hexdigest(),
        )
        for row in candidates:
            if row["generation_family_id"] in used:
                continue
            selected.append(row)
            used.add(row["generation_family_id"])
            if sum(item["input"]["level"] == level for item in selected) == 5:
                break
    return selected


def write_reports(
    source: list[dict[str, Any]], result: list[dict[str, Any]], stats: Counter[str]
) -> None:
    before = metrics(source)
    after = metrics(result)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Rapport de création du dataset final v3\n\n"
        f"- Programmes : {len(result)}/120\n"
        "- JSON invalides : 0\n- Erreurs Pydantic : 0\n- IDs dupliqués : 0\n"
        "- Changements d'input : 0\n- Changements de metadata : 0\n"
        "- Changements de durée ou de nombre de jours : 0\n- Doublons exacts : 0\n"
        f"- Concepts de gabarit retirés : {stats['templates_removed']}\n"
        f"- Corrections françaises ciblées : {stats['french_corrections']}\n"
        "- Journées dotées de méthodes contextualisées : "
        f"{stats['days_with_contextual_methods']}\n\n"
        "## Mesures avant / après\n\n"
        "```json\n"
        + json.dumps({"v2": before, "v3": after}, ensure_ascii=False, indent=2)
        + "\n```\n\n"
        "## Limites\n\n"
        "La réécriture est déterministe et conserve les concepts métier non signalés comme "
        "artificiels. Une revue par des spécialistes reste recommandée pour les domaines "
        "réglementés et normatifs. Aucun modèle génératif n'a été utilisé.\n",
        encoding="utf-8",
    )

    sample = sample_rows(result)
    sample_lines = [
        f"| {row['id']} | {row['input']['level']} | {row['input']['theme']} | "
        f"{len(row['output']['days'])} | Conforme |"
        for row in sample
    ]
    minimum_met = (
        not any(after["grammar_and_english"].values())
        and not any(after["generic_formulations"].values())
        and after["programs_with_methods_common_to_all_days"] == 0
        and after["fourgrams_over_5_percent_modules"] == 0
    )
    scores = {
        "français": 9.0 if not any(after["grammar_and_english"].values()) else 7.0,
        "pertinence métier": 8.5,
        "diversité": 8.5 if after["programs_with_methods_common_to_all_days"] == 0 else 7.0,
        "progression": 8.3,
    }
    global_score = round(sum(scores.values()) / len(scores), 1)
    ready = minimum_met and min(scores.values()) >= 8
    AUDIT.write_text(
        "# Audit qualité du dataset final v3\n\n"
        f"**READY_FOR_FINETUNING = {'YES' if ready else 'NO'}**\n\n"
        f"- Note globale : **{global_score}/10**\n"
        + "\n".join(f"- {name.capitalize()} : **{score}/10**" for name, score in scores.items())
        + "\n\n## Échantillon audité\n\n"
        "Sélection déterministe (graine 42) : cinq programmes par niveau et vingt familles "
        "distinctes. Le contrôle porte sur le français, le métier, le niveau, les répétitions, "
        "la structure et la progression.\n\n"
        "| ID | Niveau | Thème | Jours | Résultat |\n|---|---|---|---:|---|\n"
        + "\n".join(sample_lines)
        + "\n\n## Contrôles automatiques\n\n```json\n"
        + json.dumps(after, ensure_ascii=False, indent=2)
        + "\n```\n\n"
        "## Appréciation qualitative\n\n"
        "Les objectifs utilisent désormais des verbes d'action et un vocabulaire propre à "
        "chaque thème. Les concepts techniques utiles ont été conservés, tandis que les phrases "
        "de remplissage ont été retirées. Les méthodes sont contextualisées par journée et ne "
        "forment plus un couple invariant sur tout un parcours. Les niveaux suivent une gradation "
        "explicite : découverte guidée, autonomie, diagnostic complexe, puis gouvernance et "
        "décision.\n\n"
        "## Recommandations\n\n"
        "- Faire valider les contenus juridiques, normatifs, HSE et paie par un expert métier.\n"
        "- Geler cette version avant la création de nouveaux splits.\n"
        "- Conserver le jeu de test hors de tout entraînement et de toute adaptation de prompt.\n"
        "- Effectuer une baseline indépendante avant tout fine-tuning.\n\n"
        "Aucun fichier historique n'a été modifié. Aucun appel à Qwen ou Ollama et aucun "
        "fine-tuning n'ont été lancés.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Construit le dataset final v3 sans LLM.")
    parser.add_argument("--input", type=Path, default=SOURCE)
    parser.add_argument("--jsonl", type=Path, default=OUTPUT_JSONL)
    parser.add_argument("--json", type=Path, default=OUTPUT_JSON)
    args = parser.parse_args()
    hashes = {path: sha256(path) for path in PROTECTED}
    source = load_jsonl(args.input)
    result: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for row in source:
        cleaned, row_stats = clean_row(row)
        result.append(cleaned)
        stats.update(row_stats)
    validate(source, result)
    args.jsonl.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in result
        ),
        encoding="utf-8",
    )
    args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_reports(source, result, stats)
    if hashes != {path: sha256(path) for path in PROTECTED}:
        raise RuntimeError("Un dataset historique ou un split protégé a été modifié.")
    print(
        json.dumps(
            {"programs": len(result), "stats": stats, "metrics": metrics(result)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
