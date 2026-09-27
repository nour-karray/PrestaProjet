import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from math import ceil

from app.ai.program_generation_schemas import (
    ProgramDraftSchema,
    ProgramModuleDraftSchema,
    ProgramSubmoduleDraftSchema,
)


@dataclass(frozen=True)
class ProgramQualityIssue:
    code: str
    location: str
    message: str


class ProgramPedagogicalQualityError(ValueError):
    def __init__(self, issues: list[ProgramQualityIssue]) -> None:
        self.issues = issues
        super().__init__("; ".join(issue.message for issue in issues))


def validate_program_pedagogical_quality(draft: ProgramDraftSchema) -> None:
    issues = audit_program_pedagogical_quality(draft)
    if issues:
        raise ProgramPedagogicalQualityError(issues)


def audit_program_pedagogical_quality(
    draft: ProgramDraftSchema,
) -> list[ProgramQualityIssue]:
    issues: list[ProgramQualityIssue] = []
    seen_titles: set[str] = set()
    repeated_titles: set[str] = set()
    day_method_signatures: list[tuple[str, ...]] = []
    all_titles: list[str] = []
    concept_counts: Counter[str] = Counter()
    terminal_count = 0

    for day in draft.days:
        location = f"days[{day.position}]"
        if not 2 <= len(day.modules) <= 5:
            issues.append(
                ProgramQualityIssue(
                    "INSUFFICIENT_OR_EXCESSIVE_RUBRICS",
                    location,
                    "Une journée doit contenir entre 2 et 5 rubriques métier.",
                )
            )
        day_methods: set[str] = set()
        for module in day.modules:
            normalized_title = _normalize(module.title)
            all_titles.append(normalized_title)
            if _is_generic_title(normalized_title):
                issues.append(
                    ProgramQualityIssue(
                        "GENERIC_RUBRIC_TITLE",
                        f"{location}.modules[{module.position}].title",
                        f"L’intitulé « {module.title} » est trop générique.",
                    )
                )
            if normalized_title in seen_titles:
                repeated_titles.add(normalized_title)
            seen_titles.add(normalized_title)

            terminals: list[ProgramSubmoduleDraftSchema | ProgramModuleDraftSchema] = (
                list(module.submodules) if module.submodules else [module]
            )
            for terminal in terminals:
                terminal_count += 1
                day_methods.update(method.value for method in terminal.methods)
                concept_counts.update(set(_extract_notions(terminal.content or "")))
                if _notion_count(terminal.content or "") < 3:
                    issues.append(
                        ProgramQualityIssue(
                            "RUBRIC_CONTENT_TOO_POOR",
                            f"{location}.modules[{module.position}]",
                            f"La rubrique « {module.title} » contient moins de trois notions "
                            "précises.",
                        )
                    )
        day_method_signatures.append(tuple(sorted(day_methods)))

    similar_titles = any(
        _token_similarity(left, right) >= 0.75
        for index, left in enumerate(all_titles)
        for right in all_titles[index + 1 :]
    )
    if repeated_titles or similar_titles:
        issues.append(
            ProgramQualityIssue(
                "EXCESSIVE_TITLE_REPETITION",
                "days",
                "Des intitulés de rubriques sont répétés entre plusieurs journées.",
            )
        )
    dominant_method_count = max(Counter(day_method_signatures).values(), default=0)
    if len(day_method_signatures) >= 3 and dominant_method_count >= ceil(
        len(day_method_signatures) * 0.8
    ):
        issues.append(
            ProgramQualityIssue(
                "METHODS_NOT_DIVERSE",
                "days",
                "Les mêmes méthodes pédagogiques sont utilisées chaque journée.",
            )
        )
    repeated_concepts = [
        concept
        for concept, count in concept_counts.items()
        if terminal_count >= 5 and count >= max(3, ceil(terminal_count * 0.4))
    ]
    if repeated_concepts:
        issues.append(
            ProgramQualityIssue(
                "EXCESSIVE_CONCEPT_REPETITION",
                "days",
                "Certaines notions sont répétées dans une part excessive des rubriques : "
                + ", ".join(sorted(repeated_concepts)[:5])
                + ".",
            )
        )
    if _evaluation_is_too_vague(draft.evaluation_method, draft.general_objectives):
        issues.append(
            ProgramQualityIssue(
                "EVALUATION_TOO_VAGUE",
                "evaluation_method",
                "La méthode d’évaluation doit préciser une modalité et des éléments observables.",
            )
        )
    return issues


def _normalize(value: str) -> str:
    ascii_value = "".join(
        character
        for character in unicodedata.normalize("NFKD", value.casefold())
        if not unicodedata.combining(character)
    )
    return " ".join(re.sub(r"[^a-z0-9]+", " ", ascii_value).split())


def _is_generic_title(title: str) -> bool:
    return title in {
        "application des concepts",
        "application pratique",
        "connaissances theoriques",
        "mise en pratique",
        "revision des concepts",
        "revision generale",
        "theorie",
        "pratique",
    }


def _notion_count(content: str) -> int:
    return len(_extract_notions(content))


def _extract_notions(content: str) -> list[str]:
    without_labels = re.sub(r"\b(notions?|activite|exercice|cas)\s*:\s*", "", content, flags=re.I)
    parts = re.split(r"\s*(?:;|•|\n|\.\s+)\s*", without_labels)
    return [
        normalized
        for part in parts
        if len(part.strip(" .:-")) >= 4
        for normalized in [_normalize(part.strip(" .:-"))]
        if normalized and not normalized.startswith(("activite ", "exercice "))
    ]


def _token_similarity(left: str, right: str) -> float:
    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _evaluation_is_too_vague(evaluation: str, objectives: str) -> bool:
    normalized = _normalize(evaluation)
    if len(normalized) < 35 or normalized == _normalize(objectives):
        return True
    concrete_markers = {
        "cas",
        "exercice",
        "grille",
        "mise en situation",
        "plan d action",
        "presentation",
        "questionnaire",
        "quiz",
        "restitution",
    }
    return not any(marker in normalized for marker in concrete_markers)
