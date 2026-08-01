import json
import time
from dataclasses import dataclass
from typing import Protocol, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import ApiError

SchemaT = TypeVar("SchemaT", bound=BaseModel)


@dataclass(frozen=True)
class LLMHealth:
    status: str
    provider: str
    model: str | None
    latency_ms: int
    reason: str | None


class LocalLLMClient(Protocol):
    model_name: str | None

    def generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict: ...


class OllamaLocalLLMClient:
    def __init__(self, timeout_seconds: int | None = None) -> None:
        self.base_url = settings.local_llm_url
        self.model_name = settings.local_llm_model
        self.timeout_seconds = timeout_seconds or settings.local_llm_timeout_seconds

    def health(self) -> LLMHealth:
        started = time.perf_counter()
        if not self.base_url or not self.model_name:
            return LLMHealth("unavailable", "ollama", self.model_name, 0, "LLM_UNAVAILABLE")
        try:
            with urlopen(
                Request(f"{self.base_url.rstrip('/')}/api/tags", method="GET"),
                timeout=min(self.timeout_seconds, 10),
            ) as response:
                body = json.loads(response.read())
        except TimeoutError:
            return self._unavailable(started, "LLM_TIMEOUT")
        except URLError as exc:
            reason = "LLM_TIMEOUT" if isinstance(exc.reason, TimeoutError) else "LLM_UNAVAILABLE"
            return self._unavailable(started, reason)
        except (HTTPError, OSError, json.JSONDecodeError, UnicodeDecodeError):
            return self._unavailable(started, "LLM_UNAVAILABLE")
        models = body.get("models", []) if isinstance(body, dict) else []
        names = {
            name
            for item in models
            if isinstance(item, dict)
            for name in (item.get("name"), item.get("model"))
            if isinstance(name, str)
        }
        health_reason: str | None = (
            None if self.model_name in names else "LLM_MODEL_NOT_FOUND"
        )
        return LLMHealth(
            "available" if health_reason is None else "unavailable",
            "ollama",
            self.model_name,
            int((time.perf_counter() - started) * 1000),
            health_reason,
        )

    def _unavailable(self, started: float, reason: str) -> LLMHealth:
        return LLMHealth(
            "unavailable",
            "ollama",
            self.model_name,
            int((time.perf_counter() - started) * 1000),
            reason,
        )

    def generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict:
        health = self.health()
        if health.status != "available":
            messages = {
                "LLM_MODEL_NOT_FOUND": "Le modèle Ollama configuré n’est pas installé.",
                "LLM_TIMEOUT": "Le serveur Ollama ne répond pas dans le délai autorisé.",
                "LLM_UNAVAILABLE": "Le serveur Ollama est indisponible.",
            }
            code = health.reason or "LLM_UNAVAILABLE"
            raise ApiError(504 if code == "LLM_TIMEOUT" else 503, code, messages[code])
        schema_instruction = json.dumps(response_schema.model_json_schema(), ensure_ascii=False)
        if self.base_url is None:
            raise ApiError(503, "LLM_UNAVAILABLE", "Le serveur Ollama est indisponible.")
        payload = json.dumps(
            {
                "model": self.model_name,
                "prompt": f"{prompt}\n\nSCHÉMA JSON OBLIGATOIRE:\n{schema_instruction}",
                "format": "json",
                "stream": False,
                "options": {
                    "num_ctx": settings.local_llm_max_tokens,
                    # A CV extraction response is compact. Letting a small local model
                    # emit thousands of tokens can keep the request alive until the
                    # HTTP timeout when it starts repeating malformed JSON.
                    "num_predict": min(settings.local_llm_max_tokens, 1024),
                    "temperature": settings.local_llm_temperature,
                },
            }
        ).encode()
        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read())
        except TimeoutError as exc:
            raise ApiError(
                504, "LLM_TIMEOUT", "Le modèle local a dépassé le délai autorisé."
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ApiError(
                    504, "LLM_TIMEOUT", "Le modèle local a dépassé le délai autorisé."
                ) from exc
            raise ApiError(503, "LLM_UNAVAILABLE", "Le serveur Ollama est indisponible.") from exc
        except HTTPError as exc:
            code = "LLM_MODEL_NOT_FOUND" if exc.code == 404 else "LLM_UNAVAILABLE"
            raise ApiError(503, code, "Le serveur Ollama a refusé la requête.") from exc
        except OSError as exc:
            raise ApiError(503, "LLM_UNAVAILABLE", "Le serveur Ollama est indisponible.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ApiError(
                502, "LLM_INVALID_RESPONSE", "Ollama a retourné une réponse invalide."
            ) from exc
        if not isinstance(body, dict) or not isinstance(body.get("response"), str):
            raise ApiError(502, "LLM_INVALID_RESPONSE", "Ollama a retourné une réponse invalide.")
        return parse_json_response(body["response"])


def parse_json_response(raw_response: str) -> dict:
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ApiError(
            502,
            "LLM_INVALID_RESPONSE",
            "La réponse du modèle local n’est pas un JSON strict valide.",
        ) from exc
    if not isinstance(parsed, dict):
        raise ApiError(
            502,
            "JSON_VALIDATION_FAILED",
            "La réponse du modèle local ne respecte pas la structure attendue.",
        )
    return parsed
