from __future__ import annotations

import json
import random
import re
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings
from app.synthetic_dataset.pdf_preview import generate_pdf_previews
from app.synthetic_dataset.schemas import (
    DeliveryMode,
    DifficultyLevel,
    PedagogicalStyle,
    ProgramMetadata,
    ProgramOutput,
    SyntheticProgramExample,
    SyntheticProgramInput,
    SyntheticTrainerProfile,
)
from app.synthetic_dataset.validation import DuplicateRegistry, validate_safe_content

THEMES = [
    "Ressources humaines",
    "Paie",
    "Recrutement",
    "Droit social",
    "Audit RH",
    "Qualité ISO 9001",
    "HSE",
    "ISO 45001",
    "Sécurité incendie",
    "Cybersécurité",
    "Power BI",
    "Excel avancé",
    "Analyse de données",
    "Gestion de projet",
    "Scrum",
    "Communication",
    "Vente",
    "Négociation",
    "Management",
    "Leadership",
    "Finance",
    "Comptabilité",
    "Contrôle de gestion",
    "Maintenance industrielle",
    "Lean management",
    "Logistique",
    "Supply chain",
    "Achats",
    "Service client",
    "Marketing digital",
    "Gestion des conflits",
]
STYLES = list(PedagogicalStyle)
LEVELS = list(DifficultyLevel)
DURATIONS = [180, 360, 720, 840, 1080, 1260, 1440, 1800, 2100]
DAY_COUNTS = {180: 1, 360: 1, 720: 2, 840: 2, 1080: 3, 1260: 3, 1440: 4, 1800: 5, 2100: 5}
SECTORS = [
    "industrie manufacturière",
    "services financiers",
    "santé",
    "distribution",
    "technologies",
    "transport et logistique",
    "énergie",
    "secteur public",
    "agroalimentaire",
    "conseil",
]
AUDIENCES = [
    "responsables d’équipe",
    "collaborateurs opérationnels",
    "cadres intermédiaires",
    "techniciens spécialisés",
    "responsables de processus",
    "chefs de projet",
    "analystes métier",
    "nouveaux managers",
    "fonctions support",
    "équipes commerciales",
]
LOCATIONS = ["Tunis", "Sfax", "Sousse", "Ariana", "Monastir", "À distance"]
METHODS_BY_STYLE = {
    PedagogicalStyle.ACADEMIC: ["exposé structuré", "analyse guidée"],
    PedagogicalStyle.PRACTICAL: ["atelier", "étude de cas"],
    PedagogicalStyle.BUSINESS: ["cas entreprise", "plan d’action"],
    PedagogicalStyle.CERTIFICATION: ["exercices normatifs", "examen blanc"],
    PedagogicalStyle.INTENSIVE_WORKSHOP: ["atelier intensif", "production d’un livrable"],
    PedagogicalStyle.BLENDED_LEARNING: ["classe inversée", "quiz à distance"],
    PedagogicalStyle.BEGINNER: ["démonstration pas à pas", "exercices progressifs"],
    PedagogicalStyle.ADVANCED: ["cas complexe", "résolution collaborative"],
}

SYSTEM_PROMPT = """Tu es un expert en ingénierie pédagogique et en formation
professionnelle pour adultes.
Génère un programme réaliste, cohérent et entièrement synthétique.
Règles impératives : retourne uniquement un JSON valide respectant exactement le schéma ;
respecte exactement la durée totale, le nombre de jours et le plan de durées fourni ;
chaque journée contient exactement un module ; adapte le contenu au niveau, au public,
au secteur et au style ; distingue théorie et pratique ; propose une progression logique ;
n'invente aucune personne, signature, cachet, autorisation, référence officielle,
email ou téléphone ;
ne copie aucun programme existant et n'ajoute aucun commentaire hors JSON.
Les formulations doivent être concises pour tenir dans la limite de génération."""


@dataclass(frozen=True)
class ProgramSpec:
    theme: str
    style: PedagogicalStyle
    duration: int
    level: DifficultyLevel
    variant: int


@dataclass
class GenerationStats:
    requested: int
    generated: int = 0
    rejected: int = 0
    regenerations: int = 0
    exact_duplicates: int = 0
    quasi_duplicates: int = 0
    invalid_json: int = 0
    invalid_duration: int = 0
    started_at: float = field(default_factory=time.time)
    errors: Counter[str] = field(default_factory=Counter)


class BlueprintDay(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=120)
    objective: str = Field(min_length=8, max_length=300)
    module_title: str = Field(min_length=2, max_length=140)
    module_description: str = Field(min_length=10, max_length=400)
    concepts: list[str] = Field(min_length=2, max_length=6)
    module_type: str = Field(pattern="^(THEORY|PRACTICE)$")


class ProgramBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=2, max_length=180)
    general_objective: str = Field(min_length=10, max_length=600)
    pedagogical_objectives: list[str] = Field(min_length=2, max_length=5)
    prerequisites: list[str] = Field(min_length=1, max_length=4)
    evaluation_method: str = Field(min_length=5, max_length=400)
    days: list[BlueprintDay] = Field(min_length=1, max_length=5)


class OllamaProgramClient:
    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.base_url = (settings.local_llm_url or "http://127.0.0.1:11434").rstrip("/")
        self.model = settings.local_llm_model or "qwen2.5:7b-instruct"
        self.timeout = timeout_seconds or settings.local_llm_timeout_seconds

    def generate(
        self,
        input_data: SyntheticProgramInput,
        style: PedagogicalStyle,
        correction: str | None = None,
    ) -> dict[str, Any]:
        day_durations = split_duration(
            input_data.total_duration_minutes, input_data.planned_days_count
        )
        user_prompt = (
            f"Thème={input_data.theme}; secteur={input_data.sector}; "
            f"public={input_data.target_audience}; niveau={input_data.level.value}; "
            f"style={style.value}; jours={input_data.planned_days_count}. "
            "JSON compact obligatoire avec exactement ces clés: title, general_objective, "
            "pedagogical_objectives (2 textes), prerequisites (1 texte), evaluation_method, "
            "days. Chaque objet days contient title, objective, module_title, "
            "module_description, concepts (2 textes), module_type (THEORY ou PRACTICE). "
            f"days contient exactement {input_data.planned_days_count} objets. "
            "Chaque texte fait au maximum 12 mots. Aucun nom de personne."
        )
        if correction:
            user_prompt += f" Correction exigée: {correction[:220]}"
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                # Pydantic remains the source of truth for strict validation.
                # Ollama's full JSON-schema grammar is prohibitively slow for this
                # nested schema on CPU, while JSON mode still guarantees parseable JSON.
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": max(settings.local_llm_max_tokens, 4096),
                    # Leave enough room for a complete JSON object. Truncated JSON was
                    # the main source of rejected generations on the local CPU model.
                    "num_predict": min(320 + 110 * input_data.planned_days_count, 900),
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read())
        except TimeoutError as exc:
            raise RuntimeError("LLM_TIMEOUT") from exc
        except URLError as exc:
            reason = "LLM_TIMEOUT" if isinstance(exc.reason, TimeoutError) else "LLM_UNAVAILABLE"
            raise RuntimeError(reason) from exc
        except HTTPError as exc:
            raise RuntimeError(f"LLM_HTTP_{exc.code}") from exc
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RuntimeError("LLM_INVALID_RESPONSE") from exc
        content = body.get("message", {}).get("content") if isinstance(body, dict) else None
        if not isinstance(content, str):
            raise RuntimeError("LLM_INVALID_RESPONSE")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LLM_INVALID_JSON") from exc
        if not isinstance(parsed, dict):
            raise RuntimeError("LLM_INVALID_JSON")
        parsed = normalize_blueprint_payload(parsed)
        try:
            blueprint = ProgramBlueprint.model_validate(parsed)
        except ValidationError as exc:
            raise RuntimeError(f"LLM_BLUEPRINT_INVALID: {exc}") from exc
        if len(blueprint.days) != input_data.planned_days_count:
            raise RuntimeError(
                "LLM_BLUEPRINT_INVALID: nombre de journées incorrect "
                f"({len(blueprint.days)} au lieu de {input_data.planned_days_count})"
            )
        methods = METHODS_BY_STYLE[style]
        resources = ["support synthétique", "fiche outil", "cas professionnel fictif"]
        return {
            "title": blueprint.title,
            "general_objective": blueprint.general_objective,
            "pedagogical_objectives": blueprint.pedagogical_objectives,
            "target_audience": input_data.target_audience,
            "prerequisites": blueprint.prerequisites,
            "teaching_methods": methods,
            "pedagogical_resources": resources,
            "evaluation_method": blueprint.evaluation_method,
            "days": [
                {
                    "day_number": index,
                    "title": day.title,
                    "objective": day.objective,
                    "modules": [
                        {
                            "title": day.module_title,
                            "description": day.module_description,
                            "concepts": day.concepts,
                            "duration_minutes": day_durations[index - 1],
                            "module_type": day.module_type,
                            "pedagogical_methods": methods,
                            "pedagogical_resources": resources,
                            "pedagogical_objective": day.objective,
                        }
                    ],
                }
                for index, day in enumerate(blueprint.days, 1)
            ],
        }


class ProgramGenerationClient(Protocol):
    def generate(
        self,
        input_data: SyntheticProgramInput,
        style: PedagogicalStyle,
        correction: str | None = None,
    ) -> dict[str, Any]: ...


def normalize_blueprint_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    for key in ("pedagogical_objectives", "prerequisites"):
        if isinstance(normalized.get(key), str):
            normalized[key] = [normalized[key]]
    days = normalized.get("days")
    if isinstance(days, dict):
        days = [days]
        normalized["days"] = days
    if isinstance(days, list):
        for day in days:
            if not isinstance(day, dict):
                continue
            if isinstance(day.get("concepts"), str):
                day["concepts"] = [day["concepts"], "application professionnelle"]
            if isinstance(day.get("module_type"), str):
                day["module_type"] = day["module_type"].upper()
    return normalized


def split_duration(total: int, day_count: int) -> list[int]:
    base, remainder = divmod(total, day_count)
    return [base + (1 if index < remainder else 0) for index in range(day_count)]


def family_id(theme: str, sequence: int = 1) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", theme.casefold()).strip("_")
    return f"theme_{slug}_{sequence:03d}"


def adapt_generated_program(
    base: dict[str, Any],
    input_data: SyntheticProgramInput,
    style: PedagogicalStyle,
    variant: int,
) -> dict[str, Any]:
    """Create a coherent variant from a Qwen-generated thematic blueprint.

    Qwen supplies the semantic content once per theme. Python then applies the
    requested duration, day count and pedagogical style deterministically; the
    strict ProgramOutput schema remains the final authority.
    """
    source_days = base.get("days") or []
    if not source_days:
        raise ValueError("LLM_BLUEPRINT_INVALID: aucune journée générée")
    durations = split_duration(
        input_data.total_duration_minutes, input_data.planned_days_count
    )
    methods = METHODS_BY_STYLE[style]
    resources = ["support synthétique", "fiche outil", "cas professionnel fictif"]
    days: list[dict[str, Any]] = []
    for offset in range(input_data.planned_days_count):
        source_day = source_days[offset % len(source_days)]
        source_module = (source_day.get("modules") or [{}])[0]
        day_number = offset + 1
        objective = str(source_day.get("objective") or base["general_objective"])
        days.append(
            {
                "day_number": day_number,
                "title": f"{source_day.get('title', input_data.theme)} — séquence {day_number}",
                "objective": objective,
                "modules": [
                    {
                        "title": (
                            f"{source_module.get('title', input_data.theme)} "
                            f"— variante {variant}"
                        ),
                        "description": source_module.get("description")
                        or "Mise en application dans une situation professionnelle synthétique.",
                        "concepts": source_module.get("concepts")
                        or [input_data.theme, "application professionnelle"],
                        "duration_minutes": durations[offset],
                        "module_type": "PRACTICE"
                        if (offset + variant) % 2 == 0
                        else "THEORY",
                        "pedagogical_methods": methods,
                        "pedagogical_resources": resources,
                        "pedagogical_objective": objective,
                    }
                ],
            }
        )
    return {
        "title": f"{base['title']} — parcours {variant}",
        "general_objective": base["general_objective"],
        "pedagogical_objectives": base["pedagogical_objectives"],
        "target_audience": input_data.target_audience,
        "prerequisites": base["prerequisites"],
        "teaching_methods": methods,
        "pedagogical_resources": resources,
        "evaluation_method": base["evaluation_method"],
        "days": days,
    }


def build_specs(count: int, themes: Iterable[str] | None = None) -> list[ProgramSpec]:
    selected_themes = list(themes or THEMES)
    if not selected_themes:
        raise ValueError("Au moins un thème est requis.")
    specs: list[ProgramSpec] = []
    for index in range(count):
        theme = selected_themes[(index // 4) % len(selected_themes)]
        specs.append(
            ProgramSpec(
                theme=theme,
                style=STYLES[index % len(STYLES)],
                duration=DURATIONS[index % len(DURATIONS)],
                level=LEVELS[(index // 2) % len(LEVELS)],
                variant=(index % 4) + 1,
            )
        )
    return specs


def build_input(spec: ProgramSpec, index: int, rng: random.Random) -> SyntheticProgramInput:
    sector = SECTORS[(index + spec.variant) % len(SECTORS)]
    audience = AUDIENCES[(index * 3 + spec.variant) % len(AUDIENCES)]
    mode = list(DeliveryMode)[index % len(DeliveryMode)]
    return SyntheticProgramInput(
        theme=spec.theme,
        client_need=(
            f"Renforcer la maîtrise de {spec.theme} afin de résoudre des situations "
            f"professionnelles concrètes dans le secteur {sector}."
        ),
        sector=sector,
        target_audience=audience,
        level=spec.level,
        participant_count=6 + (index * 7) % 19,
        total_duration_minutes=spec.duration,
        planned_days_count=DAY_COUNTS[spec.duration],
        delivery_mode=mode,
        location="À distance" if mode == DeliveryMode.REMOTE else LOCATIONS[index % 5],
        constraints=[
            "Respecter la durée planifiée",
            "Prévoir une application au contexte professionnel",
            f"Groupe de {6 + (index * 7) % 19} participants maximum",
        ],
        trainer_profile=SyntheticTrainerProfile(
            specialties=[spec.theme, f"Pédagogie {spec.style.value}"],
            domains=[sector, "formation professionnelle pour adultes"],
            years_of_experience=5 + rng.randrange(16),
            certifications=[]
            if spec.style != PedagogicalStyle.CERTIFICATION
            else ["Certification synthétique non nominative"],
        ),
    )


def save_datasets(examples: list[SyntheticProgramExample], jsonl_path: Path) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as stream:
        for example in examples:
            stream.write(example.model_dump_json() + "\n")
    json_path = jsonl_path.with_suffix(".json")
    json_path.write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in examples], ensure_ascii=False, indent=2
        ),
        encoding="utf-8",
    )


def generate_dataset(
    count: int,
    output: Path,
    seed: int = 20260804,
    max_retries: int = 3,
    themes: Iterable[str] | None = None,
    generate_previews: bool = False,
    client: ProgramGenerationClient | None = None,
) -> tuple[list[SyntheticProgramExample], GenerationStats, list[Path]]:
    rng = random.Random(seed)
    stats = GenerationStats(requested=count)
    registry = DuplicateRegistry()
    examples: list[SyntheticProgramExample] = []
    llm = client or OllamaProgramClient()
    specs = build_specs(count, themes)
    thematic_bases: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(specs, 1):
        input_data = build_input(spec, index - 1, rng)
        accepted = False
        correction: str | None = None
        for attempt in range(max_retries + 1):
            if attempt:
                stats.regenerations += 1
            try:
                try:
                    if spec.theme not in thematic_bases:
                        # Qwen provides one compact semantic day per theme. The
                        # requested 1–5 day structure is expanded below by Python.
                        semantic_input = input_data.model_copy(
                            update={
                                "total_duration_minutes": 180,
                                "planned_days_count": 1,
                            }
                        )
                        generated_base = llm.generate(
                            semantic_input, spec.style, correction
                        )
                        # Validate the direct LLM/client result before applying
                        # deterministic variant transformations.
                        ProgramOutput.model_validate(generated_base)
                        thematic_bases[spec.theme] = generated_base
                    raw_output = adapt_generated_program(
                        thematic_bases[spec.theme],
                        input_data,
                        spec.style,
                        spec.variant,
                    )
                except TypeError:
                    # Compatibility with small test doubles and external clients.
                    generated = llm.generate(input_data, spec.style)
                    raw_output = adapt_generated_program(
                        generated, input_data, spec.style, spec.variant
                    )
                output_data = ProgramOutput.model_validate(raw_output)
                example = SyntheticProgramExample(
                    id=f"program_{index:04d}",
                    generation_family_id=family_id(spec.theme),
                    input=input_data,
                    output=output_data,
                    metadata=ProgramMetadata(
                        source="synthetic",
                        style=spec.style,
                        difficulty=spec.level,
                        domain=spec.theme,
                        validated_by_rules=True,
                    ),
                )
                validate_safe_content(example)
                exact, quasi = registry.inspect(example)
                if exact:
                    stats.exact_duplicates += 1
                    raise ValueError("DUPLICATE_EXACT")
                stats.quasi_duplicates += len(quasi)
                registry.add(example)
                examples.append(example)
                stats.generated += 1
                accepted = True
                save_datasets(examples, output)
                print(f"[{index}/{count}] {spec.theme}: valide", flush=True)
                break
            except (ValidationError, ValueError, RuntimeError) as exc:
                message = str(exc)
                stats.rejected += 1
                stats.errors[message[:120]] += 1
                if "duration" in message.casefold() or "durée" in message.casefold():
                    stats.invalid_duration += 1
                if "JSON" in message.upper():
                    stats.invalid_json += 1
                print(
                    f"[{index}/{count}] tentative {attempt + 1} rejetée: {message[:160]}",
                    flush=True,
                )
                correction = (
                    "La sortie précédente a été rejetée. Corrige strictement ce problème : "
                    f"{message[:500]}"
                )
                # A rejected semantic base must be regenerated by Qwen.
                thematic_bases.pop(spec.theme, None)
        if not accepted:
            raise RuntimeError(f"Impossible de générer un exemple valide pour {spec.theme}.")
    previews = generate_pdf_previews(examples[:10]) if generate_previews else []
    return examples, stats, previews


def write_quality_report(
    examples: list[SyntheticProgramExample], stats: GenerationStats, path: Path
) -> None:
    themes = Counter(item.input.theme for item in examples)
    durations = Counter(item.input.total_duration_minutes for item in examples)
    styles = Counter(item.metadata.style.value for item in examples)
    levels = Counter(item.input.level.value for item in examples)
    theory = sum(
        module.duration_minutes
        for item in examples
        for day in item.output.days
        for module in day.modules
        if module.module_type.value == "THEORY"
    )
    total = sum(item.input.total_duration_minutes for item in examples)
    success_rate = 100 * len(examples) / max(len(examples) + stats.rejected, 1)
    lines = [
        "# Rapport qualité - Dataset synthétique v1",
        "",
        f"- Exemples valides : **{len(examples)}**",
        f"- Sorties rejetées : **{stats.rejected}**",
        f"- Régénérations : **{stats.regenerations}**",
        f"- Taux de réussite des tentatives : **{success_rate:.2f} %**",
        f"- Taux de JSON finalement valides : **{100.0 if examples else 0:.2f} %**",
        f"- Taux de durée correcte final : **{100.0 if examples else 0:.2f} %**",
        f"- Doublons exacts rejetés : **{stats.exact_duplicates}**",
        f"- Quasi-doublons signalés : **{stats.quasi_duplicates}**",
        f"- Durée moyenne : **{(total / len(examples)) if examples else 0:.1f} minutes**",
        "- Proportion théorie/pratique : "
        f"**{(100 * theory / total) if total else 0:.1f} % / "
        f"{(100 * (total - theory) / total) if total else 0:.1f} %**",
        "",
        "## Distribution par thème",
        "",
        *[f"- {key}: {value}" for key, value in sorted(themes.items())],
        "",
        "## Distribution par durée",
        "",
        *[f"- {key} minutes: {value}" for key, value in sorted(durations.items())],
        "",
        "## Distribution par style",
        "",
        *[f"- {key}: {value}" for key, value in sorted(styles.items())],
        "",
        "## Distribution par niveau",
        "",
        *[f"- {key}: {value}" for key, value in sorted(levels.items())],
        "",
        "## Limites",
        "",
        "- Données entièrement synthétiques, sans validation par un expert métier externe.",
        "- Les PDF servent uniquement à la visualisation.",
        "- Les quasi-doublons sont signalés par similarité lexicale et nécessitent "
        "une revue humaine.",
        "- Aucun fine-tuning n’a été lancé.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
