from copy import deepcopy

from app.ai.program_generation_schemas import ProgramDraftSchema
from app.ai.program_quality_validator import audit_program_pedagogical_quality


def _rich_program() -> dict:
    titles = [
        ["Cadrage des enjeux", "Cartographie des acteurs"],
        ["Analyse des risques", "Choix des leviers"],
        ["Pilotage du plan", "Restitution des décisions"],
    ]
    days = []
    for day_position in range(1, 4):
        modules = []
        for module_position in range(1, 3):
            modules.append(
                {
                    "title": titles[day_position - 1][module_position - 1],
                    "content": (
                        f"Notions : diagnostic {day_position}.{module_position} ; acteurs "
                        f"{day_position}.{module_position} ; critères "
                        f"{day_position}.{module_position} "
                        f"; risques {day_position}.{module_position} ; plan "
                        f"{day_position}.{module_position}. Activité : analyser le cas "
                        f"{day_position}.{module_position} et restituer les décisions prises."
                    ),
                    "position": module_position,
                    "theory_minutes": 90,
                    "practice_minutes": 90,
                    "methods": (
                        ["EXPOSE", "ETUDE_DE_CAS"]
                        if day_position == 1
                        else ["EXERCICE_PRATIQUE", "MISE_EN_SITUATION"]
                    ),
                    "submodules": [],
                }
            )
        days.append(
            {
                "title": f"Jour {day_position} — Progression métier",
                "position": day_position,
                "modules": modules,
            }
        )
    return {
        "title": "Programme professionnel",
        "general_objectives": "Analyser le contexte et construire une réponse opérationnelle.",
        "prerequisites": None,
        "evaluation_method": (
            "Étude de cas finale avec restitution orale, grille d’observation et plan d’action."
        ),
        "days": days,
    }


def test_rich_program_has_no_pedagogical_quality_issue() -> None:
    draft = ProgramDraftSchema.model_validate(_rich_program())
    assert audit_program_pedagogical_quality(draft) == []


def test_quality_audit_detects_requested_problems() -> None:
    raw = deepcopy(_rich_program())
    raw["days"][0]["modules"] = raw["days"][0]["modules"][:1]
    raw["days"][0]["modules"][0]["title"] = "Mise en pratique"
    raw["days"][0]["modules"][0]["content"] = "Application des concepts."
    for day in raw["days"]:
        for module in day["modules"]:
            module["methods"] = ["EXPOSE"]
            module["content"] = "Notions : notion répétée ; principe répété ; règle répétée."
    raw["days"][0]["modules"][0]["content"] = "Application des concepts."
    raw["days"][2]["modules"][0]["title"] = raw["days"][1]["modules"][0]["title"]
    raw["evaluation_method"] = "Évaluation générale."

    issues = audit_program_pedagogical_quality(ProgramDraftSchema.model_validate(raw))
    codes = {issue.code for issue in issues}

    assert "INSUFFICIENT_OR_EXCESSIVE_RUBRICS" in codes
    assert "RUBRIC_CONTENT_TOO_POOR" in codes
    assert "GENERIC_RUBRIC_TITLE" in codes
    assert "EXCESSIVE_TITLE_REPETITION" in codes
    assert "METHODS_NOT_DIVERSE" in codes
    assert "EXCESSIVE_CONCEPT_REPETITION" in codes
    assert "EVALUATION_TOO_VAGUE" in codes
