import json

from app.ai.program_generation_schemas import ProgramDraftSchema


def build_program_prompt(context: dict) -> str:
    return (
        "Tu es ingénieur pédagogique. Propose un brouillon professionnel uniquement en JSON. "
        "Respecte exactement le schéma et la durée totale en minutes. N’invente aucun fait sur "
        "le client. Les propositions pédagogiques génériques sont autorisées. Progression logique, "
        "théorie/pratique équilibrées, exercices si pertinents. Deux niveaux maximum. Un module "
        "avec sous-modules n’a ni durée ni méthode; les éléments terminaux ont titre, contenu, "
        "durée positive et au moins une méthode autorisée. Ne soumets ni ne valide rien.\n"
        f"SCHÉMA:{json.dumps(ProgramDraftSchema.model_json_schema(), ensure_ascii=False)}\n"
        f"CONTEXTE:{json.dumps(context, ensure_ascii=False)}"
    )
