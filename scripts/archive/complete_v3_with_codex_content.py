from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.synthetic_dataset.generator import METHODS_BY_STYLE, split_duration  # noqa: E402
from app.synthetic_dataset.review import migrate_family_ids  # noqa: E402
from app.synthetic_dataset.schemas import (  # noqa: E402
    DifficultyLevel,
    ProgramMetadata,
    ProgramOutput,
    SyntheticProgramExample,
)
from app.synthetic_dataset.v3 import (  # noqa: E402
    family_similarity,
    pedagogical_violations,
    save_v3,
)
from app.synthetic_dataset.validation import DuplicateRegistry, validate_safe_content  # noqa: E402


# This pedagogical corpus was authored directly for the completion of v3.
# Python only selects the content matching the preserved input, assigns durations,
# validates it and saves it progressively. No model or external service is called.
THEME_CONTENT = {
    "Négociation": [
        ("Cadrer les intérêts en présence", "cartographie des intérêts", "mandat de négociation"),
        ("Diagnostiquer le rapport de force", "analyse du pouvoir", "zones de dépendance"),
        ("Préparer une stratégie d'entretien", "objectifs plancher et cible", "scénarios de concession"),
        ("Conduire l'exploration", "questionnement stratégique", "écoute des signaux faibles"),
        ("Construire une proposition de valeur", "argumentation différenciée", "preuves de valeur"),
        ("Traiter les objections complexes", "reformulation tactique", "désamorçage des blocages"),
        ("Piloter les concessions", "matrice de contreparties", "rythme des échanges"),
        ("Négocier en situation tendue", "gestion des tensions", "sortie d'impasse"),
        ("Formaliser un accord robuste", "clauses de sécurisation", "critères de suivi"),
        ("Évaluer une négociation", "audit de la stratégie", "retour d'expérience"),
    ],
    "Management": [
        ("Clarifier le rôle managérial", "responsabilités du manager", "cadre de décision"),
        ("Fixer des objectifs mobilisateurs", "objectifs observables", "indicateurs de réussite"),
        ("Organiser l'activité collective", "priorisation des charges", "rituels d'équipe"),
        ("Adapter son style de management", "maturité professionnelle", "autonomie graduée"),
        ("Déléguer avec contrôle", "contrat de délégation", "points de synchronisation"),
        ("Conduire un entretien de progrès", "feedback factuel", "plan de développement"),
        ("Réguler les tensions", "diagnostic relationnel", "médiation managériale"),
        ("Décider en environnement incertain", "analyse des risques", "arbitrage collectif"),
        ("Accompagner le changement", "cartographie des impacts", "engagement des acteurs"),
        ("Auditer son système managérial", "indicateurs d'équipe", "boucle d'amélioration"),
    ],
    "Leadership": [
        ("Définir son identité de leader", "sources de légitimité", "cohérence personnelle"),
        ("Formuler une vision mobilisatrice", "cap stratégique", "récit collectif"),
        ("Lire les dynamiques d'influence", "réseaux d'acteurs", "alliances informelles"),
        ("Créer la confiance", "sécurité psychologique", "exemplarité"),
        ("Mobiliser sans autorité directe", "influence transversale", "réciprocité"),
        ("Décider sous pression", "biais décisionnels", "scénarios critiques"),
        ("Développer les talents", "coaching de performance", "responsabilisation"),
        ("Conduire une transformation", "coalition de changement", "résistances systémiques"),
        ("Gérer une crise d'équipe", "communication de crise", "continuité collective"),
        ("Évaluer son impact de leader", "diagnostic 360 synthétique", "plan de progression"),
    ],
    "Finance": [
        ("Lire les états financiers", "bilan et résultat", "flux de trésorerie"),
        ("Diagnostiquer la performance", "marges et rentabilité", "structure financière"),
        ("Analyser le besoin en fonds", "cycle d'exploitation", "trésorerie nette"),
        ("Construire des prévisions", "hypothèses financières", "scénarios budgétaires"),
        ("Évaluer un investissement", "flux actualisés", "sensibilité du projet"),
        ("Arbitrer les financements", "coût du capital", "risque de liquidité"),
        ("Piloter la création de valeur", "rentabilité économique", "leviers opérationnels"),
        ("Contrôler les risques financiers", "cartographie des risques", "stress tests"),
        ("Présenter une décision financière", "note d'investissement", "argumentation chiffrée"),
        ("Auditer un modèle financier", "contrôle des hypothèses", "traçabilité des calculs"),
    ],
    "Comptabilité": [
        ("Sécuriser le cycle comptable", "organisation des pièces", "piste d'audit"),
        ("Analyser les opérations complexes", "qualification comptable", "faits générateurs"),
        ("Traiter les immobilisations", "coût d'entrée", "plans d'amortissement"),
        ("Maîtriser les provisions", "estimation des risques", "justification des montants"),
        ("Régulariser les charges et produits", "rattachement à l'exercice", "écritures d'inventaire"),
        ("Contrôler les comptes de tiers", "lettrage avancé", "analyse des soldes"),
        ("Préparer une clôture", "planning de clôture", "dossier de révision"),
        ("Détecter les anomalies", "tests de cohérence", "écritures inhabituelles"),
        ("Documenter les contrôles", "preuves comptables", "feuille de travail"),
        ("Auditer la clôture", "revue analytique", "plan de correction"),
    ],
    "Contrôle de gestion": [
        ("Cadrer le système de pilotage", "objectifs de gestion", "responsabilités budgétaires"),
        ("Construire un budget", "hypothèses d'activité", "budget flexible"),
        ("Modéliser les coûts", "coûts complets", "coûts par activité"),
        ("Analyser les écarts", "écarts volume et prix", "causes opérationnelles"),
        ("Concevoir un tableau de bord", "indicateurs décisionnels", "seuils d'alerte"),
        ("Élaborer un forecast", "atterrissage budgétaire", "scénarios glissants"),
        ("Piloter la rentabilité", "marge contributive", "mix produits"),
        ("Challenger un plan d'action", "impact financier", "priorisation des leviers"),
        ("Communiquer la performance", "commentaire de gestion", "visualisation exécutive"),
        ("Auditer le dispositif", "qualité des données", "gouvernance des indicateurs"),
    ],
    "Maintenance industrielle": [
        ("Diagnostiquer la criticité", "classification des équipements", "risques de défaillance"),
        ("Analyser les modes de panne", "AMDEC équipement", "causes racines"),
        ("Planifier la maintenance", "gammes préventives", "charge et capacité"),
        ("Préparer une intervention", "consignation", "ressources et pièces"),
        ("Fiabiliser le dépannage", "diagnostic méthodique", "contrôle après intervention"),
        ("Déployer la maintenance conditionnelle", "indicateurs de dérive", "seuils d'alerte"),
        ("Optimiser les stocks techniques", "criticité des pièces", "niveau de service"),
        ("Piloter la performance", "MTBF et MTTR", "coût global"),
        ("Conduire une analyse de panne", "arbre des causes", "actions de fiabilisation"),
        ("Auditer le plan de maintenance", "conformité des gammes", "plan d'amélioration"),
    ],
    "Lean management": [
        ("Observer la valeur client", "besoin du client", "activités à valeur ajoutée"),
        ("Cartographier un flux", "VSM actuelle", "temps de traversée"),
        ("Identifier les gaspillages", "muda mura muri", "causes de variabilité"),
        ("Stabiliser le poste", "standard de travail", "management visuel"),
        ("Fluidifier le processus", "flux tiré", "limitation des encours"),
        ("Résoudre un problème", "A3", "analyse des causes"),
        ("Animer un chantier Kaizen", "expérimentation rapide", "implication terrain"),
        ("Mesurer les gains", "indicateurs avant-après", "pérennisation"),
        ("Déployer le Lean", "gouvernance de transformation", "coaching des équipes"),
        ("Auditer la maturité", "gemba walk", "feuille de route"),
    ],
    "Logistique": [
        ("Cartographier les flux", "flux physiques", "flux d'information"),
        ("Dimensionner les stocks", "stock de sécurité", "niveau de service"),
        ("Organiser l'entrepôt", "zonage", "chemins de préparation"),
        ("Fiabiliser les inventaires", "exactitude des stocks", "analyse des écarts"),
        ("Planifier les opérations", "charge logistique", "ordonnancement"),
        ("Optimiser la préparation", "stratégies de picking", "productivité"),
        ("Piloter le transport", "plan de transport", "coût et délai"),
        ("Traiter les aléas", "gestion des ruptures", "plans de continuité"),
        ("Mesurer la performance", "OTIF", "tableau de bord logistique"),
        ("Auditer le dispositif", "diagnostic des flux", "plan d'optimisation"),
    ],
    "Supply chain": [
        ("Comprendre la chaîne étendue", "réseau de partenaires", "flux de bout en bout"),
        ("Segmenter la demande", "profils de consommation", "variabilité"),
        ("Construire une prévision", "méthodes de prévision", "mesure de l'erreur"),
        ("Aligner ventes et opérations", "processus S&OP", "arbitrages capacitaires"),
        ("Définir une politique de stock", "points de découplage", "couverture cible"),
        ("Planifier les approvisionnements", "besoins nets", "contraintes fournisseurs"),
        ("Gérer les risques", "cartographie supply chain", "scénarios de résilience"),
        ("Collaborer avec les partenaires", "partage des prévisions", "indicateurs communs"),
        ("Piloter la performance globale", "service coût cash", "tableau de bord intégré"),
        ("Auditer la résilience", "stress test", "plan de continuité"),
    ],
    "Achats": [
        ("Analyser le besoin", "spécification fonctionnelle", "coût du besoin"),
        ("Segmenter le portefeuille", "matrice de criticité", "stratégies par famille"),
        ("Analyser le marché fournisseur", "forces concurrentielles", "risques de dépendance"),
        ("Construire un appel d'offres", "critères de sélection", "grille de dépouillement"),
        ("Calculer le coût complet", "TCO", "coûts cachés"),
        ("Préparer la négociation", "objectifs achats", "leviers de contrepartie"),
        ("Contractualiser la performance", "SLA", "clauses de progrès"),
        ("Piloter les fournisseurs", "revue de performance", "plans d'action"),
        ("Gérer les risques achats", "vigilance fournisseur", "continuité"),
        ("Auditer une stratégie achats", "gains sécurisés", "feuille de route"),
    ],
    "Service client": [
        ("Comprendre le parcours client", "moments de vérité", "attentes explicites"),
        ("Adopter une communication claire", "écoute active", "reformulation"),
        ("Qualifier une demande", "diagnostic du besoin", "niveau de priorité"),
        ("Construire une réponse", "solution personnalisée", "engagement réaliste"),
        ("Traiter une réclamation", "désamorçage émotionnel", "recherche de solution"),
        ("Gérer un client difficile", "assertivité", "limites relationnelles"),
        ("Assurer le suivi", "traçabilité", "boucle de confirmation"),
        ("Mesurer la satisfaction", "indicateurs d'expérience", "analyse des verbatims"),
        ("Améliorer le service", "causes récurrentes", "plan d'amélioration"),
        ("Auditer un parcours", "client mystère synthétique", "priorités d'action"),
    ],
    "Marketing digital": [
        ("Définir une stratégie digitale", "objectifs marketing", "proposition de valeur"),
        ("Analyser les audiences", "personas", "intentions de recherche"),
        ("Concevoir un parcours d'acquisition", "tunnel de conversion", "points de contact"),
        ("Structurer une campagne de contenu", "ligne éditoriale", "calendrier de publication"),
        ("Optimiser le référencement", "architecture SEO", "qualité sémantique"),
        ("Piloter les médias payants", "ciblage", "coût d'acquisition"),
        ("Automatiser la relation", "scénarios de nurturing", "segmentation comportementale"),
        ("Mesurer la conversion", "plan de marquage", "attribution"),
        ("Optimiser par expérimentation", "A/B testing", "analyse statistique"),
        ("Auditer la performance digitale", "diagnostic multicanal", "roadmap d'optimisation"),
    ],
}

LEVEL_ACTIONS = {
    DifficultyLevel.BEGINNER: ("Comprendre", "exercice guidé", "fiche pratique"),
    DifficultyLevel.INTERMEDIATE: ("Appliquer", "étude de cas", "plan d'action"),
    DifficultyLevel.ADVANCED: ("Diagnostiquer", "audit complexe", "rapport d'optimisation"),
    DifficultyLevel.EXPERT: ("Arbitrer", "simulation stratégique", "note de décision"),
}

EVALUATIONS = [
    "Quiz raisonné et démonstration individuelle sur une situation professionnelle",
    "Étude de cas chronométrée avec grille de critères et débrief argumenté",
    "Projet d'application présenté devant un comité pédagogique simulé",
    "Audit d'un dossier fictif suivi d'une soutenance et d'un plan correctif",
]


def make_output(original: SyntheticProgramExample, variant: int) -> ProgramOutput:
    topics = THEME_CONTENT[original.input.theme]
    action, activity_kind, deliverable_kind = LEVEL_ACTIONS[original.input.level]
    day_durations = split_duration(
        original.input.total_duration_minutes, original.input.planned_days_count
    )
    methods = METHODS_BY_STYLE[original.metadata.style]
    resources = ["dossier professionnel fictif", "grille d'analyse", "support synthétique"]
    days = []
    cursor = (variant * 2) % len(topics)
    for day_index, day_duration in enumerate(day_durations, 1):
        module_count = 3 if day_duration >= 420 else 2
        durations = split_duration(day_duration, module_count)
        selected = [topics[(cursor + offset) % len(topics)] for offset in range(module_count)]
        cursor += module_count
        phase = (
            "Cadrage et diagnostic"
            if day_index == 1
            else "Évaluation et transfert"
            if day_index == len(day_durations)
            else "Application et approfondissement"
        )
        modules = []
        for module_index, ((title, concept_a, concept_b), duration) in enumerate(
            zip(selected, durations, strict=True), 1
        ):
            practical = (module_index + day_index + variant) % 2 == 0
            modules.append(
                {
                    "title": title,
                    "description": (
                        f"{action} {concept_a} dans le contexte {original.input.sector} "
                        f"et décider à partir de critères observables."
                    ),
                    "concepts": [
                        concept_a,
                        concept_b,
                        (
                            "diagnostic avancé"
                            if original.input.level == DifficultyLevel.ADVANCED
                            else "arbitrage stratégique"
                            if original.input.level == DifficultyLevel.EXPERT
                            else f"enjeux {original.input.level.value}"
                        ),
                    ],
                    "duration_minutes": duration,
                    "module_type": "PRACTICE" if practical else "THEORY",
                    "pedagogical_methods": methods,
                    "pedagogical_resources": resources,
                    "pedagogical_objective": (
                        f"{action} {concept_a} avec une méthode adaptée à "
                        f"{original.input.target_audience}."
                    ),
                    "activities": [
                        f"{activity_kind} : {concept_b}",
                        f"Restitution critique du module {module_index}",
                    ],
                }
            )
        days.append(
            {
                "day_number": day_index,
                "title": f"{phase} - {selected[0][0]}",
                "objective": (
                    f"{action} les enjeux de {selected[0][1]} puis produire une décision "
                    f"applicable au contexte {original.input.sector}."
                ),
                "pedagogical_function": phase,
                "modules": modules,
            }
        )
    evaluation = EVALUATIONS[(variant + list(DifficultyLevel).index(original.input.level)) % 4]
    return ProgramOutput.model_validate(
        {
            "title": (
                f"{original.input.theme} - {action.lower()} pour "
                f"{original.input.target_audience}"
            ),
            "general_objective": (
                f"{action} les situations de {original.input.theme} rencontrées dans le secteur "
                f"{original.input.sector} et construire une réponse professionnelle mesurable."
            ),
            "pedagogical_objectives": [
                f"Diagnostiquer un besoin lié à {original.input.theme}",
                f"Choisir les outils adaptés à {original.input.target_audience}",
                f"Traiter un cas contextualisé au secteur {original.input.sector}",
                "Évaluer les résultats et formuler une amélioration durable",
            ],
            "target_audience": original.input.target_audience,
            "prerequisites": [
                "Connaître son environnement professionnel et disposer d'un cas d'application"
            ],
            "teaching_methods": methods,
            "pedagogical_resources": resources,
            "evaluation_method": evaluation,
            "final_deliverable": (
                f"{deliverable_kind.capitalize()} consacré à {original.input.theme} "
                f"dans le secteur {original.input.sector}"
            ),
            "days": days,
        }
    )


def main() -> None:
    v1_path = ROOT / "data" / "training_programs_synthetic_v1.jsonl"
    v3_path = ROOT / "data" / "training_programs_synthetic_v3.jsonl"
    originals = migrate_family_ids(
        [json.loads(line) for line in v1_path.read_text(encoding="utf-8").splitlines()]
    )
    existing = migrate_family_ids(
        [json.loads(line) for line in v3_path.read_text(encoding="utf-8").splitlines()]
    )
    existing_ids = {item.id for item in existing}
    registry = DuplicateRegistry()
    families: dict[str, list[SyntheticProgramExample]] = {}
    for item in existing:
        registry.add(item)
        families.setdefault(item.generation_family_id, []).append(item)
    corrections = 0
    for original in originals:
        if original.id in existing_ids:
            continue
        variant = (int(original.id.rsplit("_", 1)[1]) - 1) % 4
        output = make_output(original, variant)
        metadata = ProgramMetadata.model_validate(
            {
                **original.metadata.model_dump(mode="json"),
                "diversity_revision": 3,
                "previous_version": "synthetic_v1",
                "generation_method": "codex_authored_generation",
                "qwen_attempt_count": None,
                "regenerated_at": datetime.now(UTC),
            }
        )
        candidate = SyntheticProgramExample(
            id=original.id,
            generation_family_id=original.generation_family_id,
            input=original.input,
            output=output,
            metadata=metadata,
        )
        validate_safe_content(candidate)
        reasons = pedagogical_violations(candidate)
        if reasons:
            corrections += 1
            raise ValueError(f"{candidate.id}: {reasons}")
        exact, _ = registry.inspect(candidate)
        if exact:
            corrections += 1
            raise ValueError(f"{candidate.id}: DUPLICATE_EXACT")
        similarity, closest = family_similarity(
            candidate, families.get(candidate.generation_family_id, [])
        )
        if similarity > 0.88:
            corrections += 1
            raise ValueError(
                f"{candidate.id}: FAMILY_QUASI_DUPLICATE {similarity:.3f} avec {closest}"
            )
        registry.add(candidate)
        existing.append(candidate)
        families.setdefault(candidate.generation_family_id, []).append(candidate)
        save_v3(existing, v3_path)
        print(f"[{len(existing)}/120] {candidate.id}: contenu Codex validé", flush=True)
    print(f"TOTAL={len(existing)} CORRECTIONS={corrections}")


if __name__ == "__main__":
    main()
