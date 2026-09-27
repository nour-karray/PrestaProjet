from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.synthetic_dataset.schemas import ProgramOutput, SyntheticProgramInput


@dataclass(frozen=True)
class BaselineGenerationConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_new_tokens: int = 3200
    num_ctx: int = 4096
    seed: int = 42
    timeout: int = 300
    max_attempts: int = 2

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaselineModelClient(Protocol):
    model: str

    def health(self) -> None: ...

    def generate(self, prompt: str, config: BaselineGenerationConfig) -> str: ...


class OllamaQwenClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5:7b-instruct",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def health(self) -> None:
        request = Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read())
        except (OSError, TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise RuntimeError("MODEL_UNAVAILABLE") from exc
        names = {entry.get("name") for entry in payload.get("models", [])}
        if self.model not in names:
            raise RuntimeError(f"MODEL_NOT_FOUND: {self.model}")

    def generate(self, prompt: str, config: BaselineGenerationConfig) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Tu es ingénieur pédagogique. Retourne uniquement le JSON demandé."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "format": ProgramOutput.model_json_schema(),
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "top_p": config.top_p,
                    "num_predict": config.max_new_tokens,
                    "num_ctx": config.num_ctx,
                    "seed": config.seed,
                },
            },
            ensure_ascii=False,
        ).encode()
        request = Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=config.timeout) as response:
                payload = json.loads(response.read())
            return str(payload["message"]["content"])
        except TimeoutError as exc:
            raise RuntimeError("MODEL_TIMEOUT") from exc
        except URLError as exc:
            raise RuntimeError("MODEL_UNAVAILABLE") from exc
        except HTTPError as exc:
            raise RuntimeError(f"MODEL_HTTP_ERROR_{exc.code}") from exc
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("MODEL_INVALID_RESPONSE") from exc


def build_prompt(input_data: dict[str, Any]) -> str:
    validated = SyntheticProgramInput.model_validate(input_data)
    schema = ProgramOutput.model_json_schema()
    return (
        "Crée un programme de formation complet à partir de cette demande uniquement. "
        "Respecte exactement la durée totale et le nombre de jours. Chaque journée contient "
        "2 à 5 modules, et une journée de 420 minutes contient au moins 3 modules. Aucun module "
        "ne dépasse 240 minutes. Les titres et objectifs des journées sont distincts. Les types "
        "autorisés sont THEORY et PRACTICE. Retourne uniquement un objet JSON strict conforme "
        "au schéma.\nINPUT:\n"
        f"{json.dumps(validated.model_dump(mode='json'), ensure_ascii=False)}\n"
        f"SCHEMA:\n{json.dumps(schema, ensure_ascii=False)}"
    )


def parse_json_response(raw_response: str) -> dict[str, Any]:
    value = raw_response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", value, flags=re.DOTALL | re.I)
    if fenced:
        value = fenced.group(1)
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("La réponse JSON doit être un objet.")
    return parsed


def deterministic_metrics(
    input_data: dict[str, Any], parsed: dict[str, Any] | None
) -> dict[str, bool]:
    metrics = {
        "response_produced": parsed is not None,
        "json_parsable": parsed is not None,
        "pydantic_valid": False,
        "required_fields_present": False,
        "day_count_correct": False,
        "total_duration_correct": False,
        "day_durations_correct": False,
        "module_durations_sum_correct": False,
        "module_structure_correct": False,
        "seven_hour_day_structure_correct": False,
        "module_duration_limit_correct": False,
        "module_types_valid": False,
        "day_titles_distinct": False,
        "day_objectives_distinct": False,
        "pedagogical_objectives_present": False,
        "teaching_methods_present": False,
        "resources_present": False,
        "evaluation_present": False,
        "automatic_validation_pass": False,
    }
    if parsed is None:
        return metrics
    required = set(ProgramOutput.model_fields)
    metrics["required_fields_present"] = required <= set(parsed)
    try:
        output = ProgramOutput.model_validate(parsed)
        metrics["pydantic_valid"] = True
    except ValidationError:
        return metrics
    days = output.days
    metrics["day_count_correct"] = len(days) == input_data["planned_days_count"]
    day_totals = [sum(module.duration_minutes for module in day.modules) for day in days]
    total = sum(day_totals)
    metrics["total_duration_correct"] = total == input_data["total_duration_minutes"]
    metrics["module_durations_sum_correct"] = metrics["total_duration_correct"]
    metrics["day_durations_correct"] = sum(day_totals) == input_data["total_duration_minutes"]
    metrics["module_structure_correct"] = all(2 <= len(day.modules) <= 5 for day in days)
    metrics["seven_hour_day_structure_correct"] = all(
        total_minutes != 420 or len(day.modules) >= 3
        for day, total_minutes in zip(days, day_totals, strict=True)
    )
    metrics["module_duration_limit_correct"] = all(
        module.duration_minutes <= 240 for day in days for module in day.modules
    )
    metrics["module_types_valid"] = all(
        module.module_type.value in {"THEORY", "PRACTICE"} for day in days for module in day.modules
    )
    metrics["day_titles_distinct"] = len({day.title.casefold().strip() for day in days}) == len(
        days
    )
    metrics["day_objectives_distinct"] = len(
        {day.objective.casefold().strip() for day in days}
    ) == len(days)
    metrics["pedagogical_objectives_present"] = bool(output.pedagogical_objectives)
    metrics["teaching_methods_present"] = bool(output.teaching_methods) and all(
        module.pedagogical_methods for day in days for module in day.modules
    )
    metrics["resources_present"] = bool(output.pedagogical_resources) and all(
        module.pedagogical_resources for day in days for module in day.modules
    )
    metrics["evaluation_present"] = bool(output.evaluation_method.strip())
    required_checks = [
        key for key in metrics if key not in {"response_produced", "automatic_validation_pass"}
    ]
    metrics["automatic_validation_pass"] = all(metrics[key] for key in required_checks)
    return metrics


def generate_case(
    client: BaselineModelClient,
    case: dict[str, Any],
    config: BaselineGenerationConfig,
) -> dict[str, Any]:
    prompt = build_prompt(case["input"])
    started = time.perf_counter()
    raw_response = ""
    error: str | None = None
    for _attempt in range(config.max_attempts):
        try:
            raw_response = client.generate(prompt, config)
            error = None
            break
        except RuntimeError as exc:
            error = str(exc)
    elapsed = time.perf_counter() - started
    parsed: dict[str, Any] | None = None
    status = "MODEL_ERROR" if error else "SUCCESS"
    if not error:
        try:
            parsed = parse_json_response(raw_response)
        except (json.JSONDecodeError, ValueError) as exc:
            status, error = "PARSE_ERROR", str(exc)
    metrics = deterministic_metrics(case["input"], parsed)
    target = case["output"]
    target_modules = sum(len(day["modules"]) for day in target["days"])
    generated_modules = (
        sum(len(day.get("modules", [])) for day in parsed.get("days", [])) if parsed else None
    )
    return {
        "program_id": case["id"],
        "input": case["input"],
        "raw_response": raw_response,
        "parsed_output": parsed,
        "generation_status": status,
        "generation_time_seconds": round(elapsed, 4),
        "model": client.model,
        "generation_config": config.to_dict(),
        "error": error,
        "automatic_metrics": metrics,
        "target_comparison": {
            "day_count_difference": len(parsed.get("days", [])) - len(target["days"])
            if parsed
            else None,
            "module_count_difference": generated_modules - target_modules
            if generated_modules is not None
            else None,
        },
    }
