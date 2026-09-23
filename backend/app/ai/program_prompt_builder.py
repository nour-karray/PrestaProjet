import json

from app.ai.program_generation_schemas import ProgramDraftSchema
from app.ai.program_quality_validator import ProgramQualityIssue


def build_program_prompt(context: dict) -> str:
    return (
        "RÔLE\n"
        "Tu es ingénieur pédagogique senior. Produis une vraie fiche programme professionnelle, "
        "spécifique au métier et au contexte fourni, uniquement en JSON strict.\n\n"
        "Rédige dans un français professionnel naturel et vérifie les accords grammaticaux de "
        "chaque titre avant de répondre. Rédige tous les titres et contenus en français; conserve "
        "un terme anglais uniquement s’il s’agit d’un standard métier indispensable et explique-le "
        "en français.\n\n"
        "CONTRAINTES DE SORTIE\n"
        "Respecte exactement le schéma JSON, le nombre de journées et deux niveaux maximum "
        "(modules puis sous-modules). N’ajoute jamais de champs contents, concepts, "
        "methods_and_resources, training_objectives ou pedagogical_objectives : transpose leur "
        "richesse dans les champs existants general_objectives, modules.content, submodules et "
        "methods. N’invente aucun fait sur le client ou le formateur. Ne soumets ni ne valide "
        "rien.\n\n"
        "La liste days doit contenir EXACTEMENT planned_days_count éléments du CONTEXTE. Compte "
        "les journées avant de répondre : ne déduis pas leur nombre de la durée et n’ajoute jamais "
        "une journée supplémentaire.\n\n"
        "RICHESSE PÉDAGOGIQUE OBLIGATOIRE\n"
        "- Construis une progression explicite entre les jours : cadrage et fondamentaux, "
        "compréhension, application, cas métier, approfondissement, puis synthèse ou évaluation.\n"
        "- Traite chaque module de premier niveau comme une rubrique métier de la fiche programme. "
        "Chaque journée contient 2 à 5 rubriques distinctes; pour 7 heures, vise 3 à 5 rubriques.\n"
        "- Chaque module terminal possède un titre métier précis et un content non vide détaillant "
        "environ 4 à 10 notions concrètes, séparées clairement, ainsi qu’une activité, un exercice "
        "ou un cas contextualisé lorsque pertinent.\n"
        "- Utilise les sous-modules seulement lorsqu’ils améliorent réellement la lisibilité. Un "
        "module parent avec sous-modules ne porte ni durée ni méthode; chaque élément terminal a "
        "titre, content et au moins une méthode autorisée.\n"
        "- Interdis les intitulés vagues isolés tels que Application des concepts, Révision des "
        "concepts, Connaissances théoriques ou Application pratique. Chaque intitulé doit annoncer "
        "un objet métier identifiable.\n"
        "- Varie les méthodes entre les modules et les journées parmi allowed_methods : exposé "
        "interactif, démonstration, exercice pratique, étude de cas, mise en situation, échange "
        "collectif et évaluation. Évite de répéter exactement la même combinaison chaque jour.\n"
        "- Rédige general_objectives avec plusieurs résultats observables et evaluation_method "
        "avec "
        "une modalité concrète, des livrables ou critères vérifiables.\n\n"
        "- La dernière journée conserve 2 à 5 rubriques de contenu réel : cas global, analyse, "
        "mise en situation, restitution, évaluation et plan d’action selon le thème. Elle ne doit "
        "jamais se limiter à une révision générale.\n"
        "- evaluation_method décrit une procédure distincte des objectifs : support évalué, "
        "modalité (cas, quiz, exercice, restitution ou mise en situation), critères observés et "
        "retour donné au participant.\n\n"
        "FORMAT DE DÉTAIL ATTENDU\n"
        "Dans chaque content terminal, énumère explicitement les notions au lieu de les résumer "
        "par une formule générale. Exemple de forme (à adapter au thème, sans le recopier) : "
        '"content": "Notions : indicateurs pertinents ; sources de données ; règles de contrôle ; '
        "écarts et seuils d’alerte ; causes racines ; priorisation des actions. Activité : "
        "analyser "
        'un cas métier, justifier le diagnostic et restituer un plan d’action.". '
        "Un content réduit à « introduction à », « présentation de » ou « application de » sans "
        "liste de notions précises est insuffisant.\n\n"
        "EXEMPLE DE DENSITÉ, PAS DE CONTENU À RECOPIER\n"
        "Pour une rubrique « Structurer un message professionnel », un content professionnel "
        "serait : « Notions : objectif du message ; hiérarchisation des idées ; clarté ; concision "
        "; adaptation au destinataire ; reformulation ; synthèse ; argumentation. Activité : "
        "réécrire un message métier puis justifier les choix lors d’une restitution collective. » "
        "Produis cette densité pour le thème réel de chaque rubrique.\n\n"
        "MÉTHODES DANS LE SCHÉMA EXISTANT\n"
        "Utilise uniquement les valeurs de allowed_methods. Traduis un tour de table ou une "
        "animation en ECHANGE_COLLECTIF, une présentation en EXPOSE, un jeu de rôle en "
        "MISE_EN_SITUATION et un quiz de validation en EVALUATION.\n\n"
        "ADAPTATION OBLIGATOIRE\n"
        "Adapte chaque exemple et cas au theme, client_need, target_audience, delivery_mode et aux "
        "constraints. Mobilise trainer_profile uniquement lorsque ses compétences sont "
        "pertinentes. BEGINNER : fondamentaux, vocabulaire, démonstrations et cas simples guidés. "
        "INTERMEDIATE : "
        "application autonome et diagnostic. ADVANCED : analyse et résolution de situations "
        "complexes. EXPERT : stratégie, arbitrage, conception et justification de décisions.\n\n"
        "DURÉES\n"
        "Concentre-toi sur la qualité du contenu. Fournis seulement une proportion pédagogique "
        "approximative entre théorie et pratique; le backend recalcule toutes les durées finales "
        "et il ne faut pas imposer 50/50 systématiquement.\n"
        f"SCHÉMA:{json.dumps(ProgramDraftSchema.model_json_schema(), ensure_ascii=False)}\n"
        f"CONTEXTE:{json.dumps(context, ensure_ascii=False)}"
    )


def build_program_correction_prompt(
    draft: ProgramDraftSchema,
    issues: list[ProgramQualityIssue],
    context: dict,
) -> str:
    issue_payload = [
        {"code": issue.code, "location": issue.location, "message": issue.message}
        for issue in issues
    ]
    protected_context = {
        "theme": context.get("theme"),
        "target_audience": context.get("target_audience"),
        "trainer_profile": context.get("trainer_profile"),
        "planned_days_count": context.get("planned_days_count"),
        "total_minutes": context.get("total_minutes"),
    }
    return (
        "Tu corriges pédagogiquement un programme déjà valide techniquement. Retourne le programme "
        "COMPLET en JSON strict selon exactement le même schéma.\n\n"
        "Corrige UNIQUEMENT les anomalies listées. Ne réécris pas les journées, rubriques, "
        "objectifs ou méthodes déjà conformes. Ne crée aucun fait nouveau sur le client ou le "
        "formateur.\n\n"
        "ÉLÉMENTS STRICTEMENT PROTÉGÉS\n"
        "- conserve exactement title, general_objectives et prerequisites;\n"
        "- conserve exactement le nombre, la position et l’ordre des journées;\n"
        "- conserve exactement la durée totale et le total de chaque journée; une répartition "
        "interne peut changer seulement si elle est nécessaire pour corriger une rubrique;\n"
        "- ne modifie jamais le thème, le public cible, le formateur ni les données métier "
        "d’entrée;\n"
        "- conserve toute partie qui n’est pas désignée par une anomalie.\n\n"
        "RÈGLES DE CORRECTION\n"
        "Une rubrique pauvre doit contenir au moins 4 notions métier précises, séparées par des "
        "points-virgules, et une activité contextualisée. Remplace un intitulé générique par un "
        "intitulé métier précis. Diversifie seulement les méthodes signalées. Une évaluation vague "
        "doit préciser modalité, support ou livrable, critères observés et restitution.\n\n"
        f"ANOMALIES À CORRIGER:{json.dumps(issue_payload, ensure_ascii=False)}\n"
        f"CONTEXTE PROTÉGÉ:{json.dumps(protected_context, ensure_ascii=False)}\n"
        f"PROGRAMME À CORRIGER:{draft.model_dump_json()}\n"
        f"SCHÉMA:{json.dumps(ProgramDraftSchema.model_json_schema(), ensure_ascii=False)}"
    )
