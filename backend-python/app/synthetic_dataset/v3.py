from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings
from app.synthetic_dataset.generator import METHODS_BY_STYLE, split_duration
from app.synthetic_dataset.review import content_signature
from app.synthetic_dataset.schemas import (
    DifficultyLevel,
    ProgramMetadata,
    ProgramOutput,
    SyntheticProgramExample,
)
from app.synthetic_dataset.validation import DuplicateRegistry, validate_safe_content

ADVANCED_MARKERS = {
    "analyse",
    "approfondissement",
    "architecture",
    "audit",
    "avancé",
    "complexe",
    "conformité",
    "contrôle",
    "diagnostic",
    "expertise",
    "gouvernance",
    "modélisation",
    "optimisation",
    "pilotage",
    "régularisation",
    "risque",
    "stratégie",
    "stratégique",
}
ARTIFICIAL_SUFFIX = re.compile(r"\b(?:séquence|parcours)\s*\d+\b", re.IGNORECASE)


class V3ModuleBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=140)
    description: str = Field(min_length=12, max_length=400)
    concepts: list[str] = Field(min_length=2, max_length=6)
    pedagogical_objective: str = Field(min_length=8, max_length=300)
    activities: list[str] = Field(min_length=1, max_length=4)
    module_type: str = Field(pattern="^(THEORY|PRACTICE)$")


class V3DayBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=160)
    objective: str = Field(min_length=8, max_length=350)
    pedagogical_function: str = Field(min_length=3, max_length=160)
    modules: list[V3ModuleBlueprint] = Field(min_length=2, max_length=5)


class V3ProgramBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=180)
    general_objective: str = Field(min_length=12, max_length=600)
    pedagogical_objectives: list[str] = Field(min_length=3, max_length=7)
    prerequisites: list[str] = Field(min_length=1, max_length=5)
    evaluation_method: str = Field(min_length=8, max_length=500)
    final_deliverable: str = Field(min_length=4, max_length=300)
    days: list[V3DayBlueprint] = Field(min_length=1, max_length=5)


class V3Client(Protocol):
    calls: int

    def generate(
        self,
        example: SyntheticProgramExample,
        variant_index: int,
        forbidden_summary: str,
        correction: str | None = None,
    ) -> dict[str, Any]: ...


class OllamaV3Client:
    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.base_url = (settings.local_llm_url or "http://127.0.0.1:11434").rstrip("/")
        self.model = settings.local_llm_model or "qwen2.5:7b-instruct"
        self.timeout = timeout_seconds or settings.local_llm_timeout_seconds
        self.calls = 0

    def health(self) -> None:
        request = Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with urlopen(request, timeout=min(self.timeout, 15)) as response:
                body = json.loads(response.read())
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("LLM_UNAVAILABLE") from exc
        names = {item.get("name") for item in body.get("models", [])}
        if self.model not in names:
            raise RuntimeError(f"LLM_MODEL_MISSING: {self.model}")

    def generate(
        self,
        example: SyntheticProgramExample,
        variant_index: int,
        forbidden_summary: str,
        correction: str | None = None,
    ) -> dict[str, Any]:
        self.calls += 1
        input_data = example.input
        day_durations = split_duration(
            input_data.total_duration_minutes, input_data.planned_days_count
        )
        module_requirements = [3 if value >= 420 else 2 for value in day_durations]
        special = ""
        if "paie" in input_data.theme.casefold():
            special = (
                " Pour Paie avancée, couvrir sans répétition: cadre juridique et rubriques "
                "complexes; variables, primes et avantages; absences et retenues; "
                "régularisations; entrées et sorties; contrôle des écarts; audit de paie; "
                "étude de cas finale."
            )
        prompt = (
            f"Tu génères la variante {variant_index} d'une famille de quatre programmes. "
            "Cette variante doit être réellement différente sur objectifs, modules, activités, "
            "exercices, livrable, évaluation et progression. Ne modifie pas seulement la durée "
            "ou quelques formulations. Retourne uniquement un JSON valide. "
            f"Thème={input_data.theme}; besoin={input_data.client_need}; "
            f"secteur={input_data.sector}; "
            f"public={input_data.target_audience}; niveau={input_data.level.value}; "
            f"style={example.metadata.style.value}; "
            f"durée={input_data.total_duration_minutes} minutes; "
            f"jours={input_data.planned_days_count}; durées_jours={day_durations}; "
            f"modules_minimum_par_jour={module_requirements}; "
            f"contraintes={input_data.constraints}. "
            "JSON exact: title, general_objective, pedagogical_objectives (3-7), prerequisites, "
            "evaluation_method, final_deliverable, days. Chaque jour: title, objective, "
            "pedagogical_function, modules (2-5). Chaque module: title, description, concepts "
            "(2-6), pedagogical_objective, activities (1-4), module_type THEORY ou PRACTICE. "
            "Les titres et objectifs des jours sont uniques. Progression: cadrage/fondamentaux, "
            "application/approfondissement, puis étude de cas/audit/projet/évaluation. "
            "Aucun module ne remplit seul une journée. Aucun suffixe parcours ou séquence. "
            "Chaque texte reste concis. "
            f"Éléments interdits déjà utilisés: {forbidden_summary or 'aucun'}。"
            f"{special}"
        )
        if correction:
            prompt += f" Correction obligatoire après rejet: {correction[:700]}"
        if input_data.planned_days_count == 1:
            prompt += (
                " Le tableau days doit contenir EXACTEMENT UN objet. La progression cadrage, "
                "application et évaluation doit apparaître dans les modules de cette seule journée."
            )
        if input_data.level in {DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT}:
            prompt += (
                " Les concepts doivent employer explicitement un vocabulaire avancé tel que "
                "audit, analyse, diagnostic, optimisation, pilotage, conformité ou stratégie."
            )
        response_schema = V3ProgramBlueprint.model_json_schema()
        days_schema = response_schema["properties"]["days"]
        days_schema["minItems"] = input_data.planned_days_count
        days_schema["maxItems"] = input_data.planned_days_count
        modules_schema = response_schema["$defs"]["V3DayBlueprint"]["properties"][
            "modules"
        ]
        modules_schema["minItems"] = max(module_requirements)
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Tu es ingénieur pédagogique senior. Tu produis uniquement un objet "
                            "JSON strict, sans markdown, sans données personnelles ni "
                            "références officielles."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "format": response_schema,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": max(settings.local_llm_max_tokens, 8192),
                    "num_predict": min(1100 + 450 * input_data.planned_days_count, 3200),
                },
            },
            ensure_ascii=False,
        ).encode()
        request = Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
            content = body["message"]["content"]
        except TimeoutError as exc:
            raise RuntimeError("LLM_TIMEOUT") from exc
        except URLError as exc:
            raise RuntimeError("LLM_UNAVAILABLE") from exc
        except HTTPError as exc:
            raise RuntimeError(f"LLM_HTTP_{exc.code}") from exc
        except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError("LLM_INVALID_JSON") from exc
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            tail = content[-120:].replace("\n", " ")
            raise RuntimeError(
                f"LLM_INVALID_JSON length={len(content)} tail={tail}"
            ) from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("LLM_INVALID_JSON")
        return parsed


@dataclass
class V3Stats:
    scanned: int = 0
    violating: int = 0
    regenerated: int = 0
    calls: int = 0
    rejected: int = 0
    retries: int = 0
    started_at: float = field(default_factory=time.time)
    errors: Counter[str] = field(default_factory=Counter)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.started_at


def normalized(value: str) -> str:
    return " ".join(ARTIFICIAL_SUFFIX.sub("", value).casefold().split())


def pedagogical_violations(example: SyntheticProgramExample) -> list[str]:
    reasons: list[str] = []
    day_titles = [normalized(day.title) for day in example.output.days]
    day_objectives = [normalized(day.objective) for day in example.output.days]
    if len(day_titles) != len(set(day_titles)):
        reasons.append("DAY_TITLES_REPEATED")
    if len(day_objectives) != len(set(day_objectives)):
        reasons.append("DAY_OBJECTIVES_REPEATED")
    artificial_day = any(
        ARTIFICIAL_SUFFIX.search(day.title) for day in example.output.days
    )
    if artificial_day or ARTIFICIAL_SUFFIX.search(example.output.title):
        reasons.append("ARTIFICIAL_DIVERSITY_SUFFIX")
    module_titles: list[str] = []
    for day in example.output.days:
        duration = sum(module.duration_minutes for module in day.modules)
        module_titles.extend(normalized(module.title) for module in day.modules)
        if len(day.modules) < 2:
            reasons.append("DAY_HAS_FEWER_THAN_TWO_MODULES")
        if duration > 240 and len(day.modules) < 2:
            reasons.append("SINGLE_MODULE_LONG_DAY")
        if duration >= 420 and len(day.modules) < 3:
            reasons.append("SEVEN_HOUR_DAY_FEWER_THAN_THREE_MODULES")
        if any(module.duration_minutes > 240 for module in day.modules):
            reasons.append("MODULE_OVER_240_MINUTES")
        if example.metadata.diversity_revision == 3:
            if not day.pedagogical_function:
                reasons.append("PEDAGOGICAL_FUNCTION_MISSING")
            if any(not module.activities for module in day.modules):
                reasons.append("ACTIVITY_MISSING")
    if module_titles:
        most_common = Counter(module_titles).most_common(1)[0][1]
        if most_common / len(module_titles) > 0.5:
            reasons.append("MODULE_TITLES_MAJORITY_IDENTICAL")
    if example.input.level in {DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT}:
        concepts = {
            word.casefold()
            for day in example.output.days
            for module in day.modules
            for concept in module.concepts
            for word in re.findall(r"[\wÀ-ÿ]+", concept)
        }
        if len(concepts & ADVANCED_MARKERS) < 1:
            reasons.append("ADVANCED_LEVEL_NOT_REFLECTED")
    return sorted(set(reasons))


def _allocate(total: int, count: int) -> list[int]:
    values = split_duration(total, count)
    if any(value > 240 for value in values):
        raise ValueError("MODULE_OVER_240_MINUTES")
    return values


def build_v3_output(
    blueprint: V3ProgramBlueprint,
    original: SyntheticProgramExample,
) -> ProgramOutput:
    if len(blueprint.days) != original.input.planned_days_count:
        raise ValueError("DAY_COUNT_MISMATCH")
    day_durations = split_duration(
        original.input.total_duration_minutes, original.input.planned_days_count
    )
    methods = METHODS_BY_STYLE[original.metadata.style]
    resources = ["support synthétique", "fiche d'activité", "jeu de données fictif"]
    days: list[dict[str, Any]] = []
    for index, (day, day_duration) in enumerate(zip(blueprint.days, day_durations, strict=True), 1):
        required = 3 if day_duration >= 420 else 2
        if len(day.modules) < required:
            raise ValueError(f"DAY_{index}_MODULE_COUNT_TOO_LOW")
        durations = _allocate(day_duration, len(day.modules))
        days.append(
            {
                "day_number": index,
                "title": day.title,
                "objective": day.objective,
                "pedagogical_function": day.pedagogical_function,
                "modules": [
                    {
                        **module.model_dump(),
                        "duration_minutes": durations[module_index],
                        "pedagogical_methods": methods,
                        "pedagogical_resources": resources,
                    }
                    for module_index, module in enumerate(day.modules)
                ],
            }
        )
    return ProgramOutput.model_validate(
        {
            "title": blueprint.title,
            "general_objective": blueprint.general_objective,
            "pedagogical_objectives": blueprint.pedagogical_objectives,
            "target_audience": original.input.target_audience,
            "prerequisites": blueprint.prerequisites,
            "teaching_methods": methods,
            "pedagogical_resources": resources,
            "evaluation_method": blueprint.evaluation_method,
            "final_deliverable": blueprint.final_deliverable,
            "days": days,
        }
    )


def family_forbidden_summary(accepted: list[SyntheticProgramExample]) -> str:
    if not accepted:
        return "aucun"
    parts: list[str] = []
    for item in accepted:
        parts.append(
            "objectifs="
            + "; ".join(item.output.pedagogical_objectives[:4])
            + " | modules="
            + "; ".join(
                module.title for day in item.output.days for module in day.modules
            )
            + " | évaluation="
            + item.output.evaluation_method
            + " | livrable="
            + (item.output.final_deliverable or "")
        )
    return " || ".join(parts)[-2500:]


def family_similarity(
    candidate: SyntheticProgramExample, accepted: list[SyntheticProgramExample]
) -> tuple[float, str]:
    if not accepted:
        return 0.0, ""
    best = 0.0
    closest = ""
    candidate_text = content_signature(candidate)
    for item in accepted:
        ratio = SequenceMatcher(None, candidate_text, content_signature(item)).ratio()
        if ratio > best:
            best = ratio
            closest = item.id
    return best, closest


def save_v3(examples: list[SyntheticProgramExample], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(example.model_dump_json() + "\n" for example in examples),
        encoding="utf-8",
    )
    output.with_suffix(".json").write_text(
        json.dumps(
            [example.model_dump(mode="json") for example in examples],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def regenerate_v3(
    originals: list[SyntheticProgramExample],
    output: Path,
    client: V3Client,
    max_retries: int = 3,
    resume_examples: list[SyntheticProgramExample] | None = None,
) -> tuple[list[SyntheticProgramExample], V3Stats, dict[str, list[str]]]:
    stats = V3Stats(scanned=len(originals))
    violations = {item.id: pedagogical_violations(item) for item in originals}
    violations = {key: value for key, value in violations.items() if value}
    stats.violating = len(violations)
    accepted_by_family: dict[str, list[SyntheticProgramExample]] = defaultdict(list)
    final: list[SyntheticProgramExample] = []
    registry = DuplicateRegistry()
    resumed = {item.id: item for item in (resume_examples or [])}
    for original in originals:
        if original.id in resumed:
            previous = resumed[original.id]
            final.append(previous)
            registry.add(previous)
            accepted_by_family[previous.generation_family_id].append(previous)
            stats.regenerated += 1
            continue
        if original.id not in violations:
            final.append(original)
            registry.add(original)
            accepted_by_family[original.generation_family_id].append(original)
            continue
        family = accepted_by_family[original.generation_family_id]
        correction: str | None = None
        accepted = False
        for attempt in range(1, max_retries + 2):
            try:
                raw = client.generate(
                    original,
                    len(family) + 1,
                    family_forbidden_summary(family),
                    correction,
                )
                blueprint = V3ProgramBlueprint.model_validate(raw)
                output_data = build_v3_output(blueprint, original)
                metadata = ProgramMetadata.model_validate(
                    {
                        **original.metadata.model_dump(mode="json"),
                        "diversity_revision": 3,
                        "previous_version": "synthetic_v1",
                        "generation_method": "independent_qwen_generation",
                        "qwen_attempt_count": attempt,
                        "regenerated_at": datetime.now(UTC),
                    }
                )
                candidate = SyntheticProgramExample(
                    id=original.id,
                    generation_family_id=original.generation_family_id,
                    input=original.input,
                    output=output_data,
                    metadata=metadata,
                )
                validate_safe_content(candidate)
                reasons = pedagogical_violations(candidate)
                if reasons:
                    raise ValueError(";".join(reasons))
                similarity, closest = family_similarity(candidate, family)
                if similarity > 0.88:
                    raise ValueError(
                        f"FAMILY_QUASI_DUPLICATE {similarity:.3f} avec {closest}"
                    )
                exact, _ = registry.inspect(candidate)
                if exact:
                    raise ValueError("DUPLICATE_EXACT")
                registry.add(candidate)
                family.append(candidate)
                final.append(candidate)
                stats.regenerated += 1
                accepted = True
                save_v3(final, output)
                print(
                    f"[{len(final)}/{len(originals)}] {candidate.id}: régénéré "
                    f"(tentative {attempt})",
                    flush=True,
                )
                break
            except (RuntimeError, ValueError, ValidationError) as exc:
                stats.rejected += 1
                stats.errors[str(exc)[:160]] += 1
                if attempt > 1:
                    stats.retries += 1
                correction = (
                    "La variante a été rejetée. Corrige ces défauts sans reprendre les éléments "
                    f"interdits: {str(exc)[:700]}"
                )
                print(
                    f"[{len(final) + 1}/{len(originals)}] rejet tentative {attempt}: {exc}",
                    flush=True,
                )
        if not accepted:
            save_v3(final, output)
            raise RuntimeError(f"V3_ABORTED_AFTER_RETRIES: {original.id}")
    stats.calls = client.calls
    return final, stats, violations
