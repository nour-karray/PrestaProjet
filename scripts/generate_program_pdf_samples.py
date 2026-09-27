from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.documents.program_pdf import generate_program_pdf  # noqa: E402
from app.schemas.program_document import (  # noqa: E402
    ProgramContent,
    ProgramTrainer,
    TrainingProgramDay,
    TrainingProgramOutput,
)

OUTPUT_DIR = ROOT / "reports" / "program_pdf_samples"


def sample(
    theme: str,
    audience: str,
    trainer: str,
    day_specs: list[tuple[str, list[tuple[str, list[str]]], list[str], int, int]],
    objectives: list[str],
    pedagogical: list[str],
    evaluation: str,
) -> TrainingProgramOutput:
    days = [
        TrainingProgramDay(
            day_number=index,
            title=title,
            contents=[ProgramContent(title=name, concepts=concepts) for name, concepts in contents],
            methods_and_resources=methods,
            theory_minutes=theory,
            practice_minutes=practice,
        )
        for index, (title, contents, methods, theory, practice) in enumerate(day_specs, 1)
    ]
    total = sum(day.theory_minutes + day.practice_minutes for day in days)
    return TrainingProgramOutput(
        theme=theme,
        target_audience=audience,
        training_objectives=objectives,
        pedagogical_objectives=pedagogical,
        trainer=ProgramTrainer(name=trainer, hours=total / 60),
        days=days,
        total_duration_minutes=total,
        evaluation_method=evaluation,
    )


def build_samples() -> dict[str, TrainingProgramOutput]:
    return {
        "audit_rh_sample.pdf": sample(
            "Audit RH et pilotage de la performance sociale",
            "Responsables RH, auditeurs internes et responsables de processus",
            "Nawfel Ben Labiedh",
            [
                (
                    "Cadrer un audit RH",
                    [
                        (
                            "Référentiel et périmètre",
                            ["Finalités de l’audit", "Cartographie des risques RH"],
                        ),
                        ("Préparation", ["Plan d’audit", "Échantillonnage et preuves"]),
                    ],
                    ["Exposé interactif", "Grille d’audit", "Travail en sous-groupes"],
                    180,
                    180,
                ),
                (
                    "Conduire les investigations",
                    [
                        (
                            "Entretiens et observations",
                            ["Questionnement", "Traçabilité des constats"],
                        ),
                        ("Analyse des processus", ["Recrutement", "Compétences", "Rémunération"]),
                    ],
                    ["Jeux de rôle", "Étude de cas", "Fiches processus"],
                    150,
                    210,
                ),
                (
                    "Restituer et piloter les actions",
                    [
                        (
                            "Rapport d’audit",
                            ["Classification des écarts", "Recommandations argumentées"],
                        ),
                        ("Plan d’action", ["Indicateurs", "Suivi et clôture"]),
                    ],
                    ["Atelier de rédaction", "Tableau de bord", "Simulation de restitution"],
                    120,
                    240,
                ),
            ],
            [
                "Structurer un audit RH fondé sur les risques",
                "Produire des constats exploitables pour la décision",
            ],
            [
                "Préparer et conduire les investigations",
                "Formuler des recommandations et suivre un plan d’action",
            ],
            "Évaluation continue par étude de cas, grille d’observation et soutenance d’un rapport d’audit.",
        ),
        "excel_avance_sample.pdf": sample(
            "Excel avancé : analyse, automatisation et tableaux de bord",
            "Contrôleurs de gestion, analystes et utilisateurs réguliers d’Excel",
            "Sonia Trabelsi",
            [
                (
                    "Fiabiliser et transformer les données",
                    [
                        ("Formules avancées", ["RECHERCHEX et INDEX/EQUIV", "Formules dynamiques"]),
                        ("Power Query", ["Nettoyage", "Fusion et actualisation"]),
                    ],
                    ["Démonstration guidée", "Fichiers d’exercices", "Cas progressifs"],
                    150,
                    270,
                ),
                (
                    "Modéliser et analyser",
                    [
                        ("Modèle de données", ["Relations", "Mesures et indicateurs"]),
                        ("Analyse croisée", ["TCD avancés", "Segments et chronologies"]),
                    ],
                    ["Atelier pratique", "Jeu de données métier", "Corrections commentées"],
                    120,
                    300,
                ),
                (
                    "Automatiser et restituer",
                    [
                        ("Automatisation", ["Macros enregistrées", "Contrôles et robustesse"]),
                        (
                            "Tableau de bord",
                            ["Choix des visualisations", "Navigation et actualisation"],
                        ),
                    ],
                    ["Projet fil rouge", "Poste équipé d’Excel", "Revue par les pairs"],
                    90,
                    330,
                ),
            ],
            [
                "Exploiter des données complexes avec fiabilité",
                "Construire un tableau de bord automatisé",
            ],
            [
                "Transformer des sources hétérogènes",
                "Modéliser des indicateurs",
                "Automatiser une restitution décisionnelle",
            ],
            "Mise en situation sur un classeur métier, contrôle des résultats et présentation du tableau de bord final.",
        ),
        "management_sample.pdf": sample(
            "Management opérationnel et animation d’équipe",
            "Managers de proximité et responsables d’équipe nouvellement nommés",
            "Amira Mansour",
            [
                (
                    "Adopter sa posture de manager",
                    [
                        ("Rôle et responsabilités", ["Positionnement", "Styles de management"]),
                        ("Communication", ["Écoute active", "Feedback factuel"]),
                    ],
                    ["Auto-positionnement", "Apports ciblés", "Mises en situation"],
                    180,
                    240,
                ),
                (
                    "Piloter l’activité collective",
                    [
                        ("Objectifs et délégation", ["Objectifs SMART", "Niveaux de délégation"]),
                        ("Rituels de pilotage", ["Réunion d’équipe", "Suivi des engagements"]),
                    ],
                    ["Cas d’équipe", "Canevas de délégation", "Simulation de réunion"],
                    150,
                    270,
                ),
                (
                    "Gérer les situations sensibles",
                    [
                        ("Tensions et conflits", ["Diagnostic", "Entretien de régulation"]),
                        ("Décision managériale", ["Arbitrage", "Plan de progrès"]),
                    ],
                    ["Jeux de rôle", "Analyse de pratiques", "Plan d’action individuel"],
                    120,
                    300,
                ),
            ],
            [
                "Renforcer l’efficacité managériale au quotidien",
                "Installer des pratiques de pilotage responsables",
            ],
            [
                "Adapter sa communication",
                "Déléguer et suivre l’activité",
                "Traiter une situation sensible",
            ],
            "Évaluation par mises en situation, feedback croisé et validation d’un plan d’action individuel.",
        ),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, program in build_samples().items():
        (OUTPUT_DIR / filename).write_bytes(generate_program_pdf(program))


if __name__ == "__main__":
    main()
