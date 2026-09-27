import json
import time
from dataclasses import dataclass
from threading import Lock
from typing import Protocol, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel

from app.core.config import settings
from app.core.errors import ApiError

SchemaT = TypeVar("SchemaT", bound=BaseModel)

# CPU-only inference is deliberately serialized. Concurrent generations make
# each request slower and can force an 8 GB Windows host to page heavily.
_generation_lock = Lock()


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
    def __init__(
        self,
        timeout_seconds: int | None = None,
        model_name: str | None = None,
        max_tokens: int | None = None,
        keep_alive: str | None = None,
    ) -> None:
        self.base_url = settings.local_llm_url
        self.model_name = model_name or settings.local_llm_model
        self.timeout_seconds = timeout_seconds or settings.local_llm_timeout_seconds
        self.max_tokens = max_tokens or settings.local_llm_max_tokens
        self.keep_alive = keep_alive or settings.local_llm_keep_alive

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
        with _generation_lock:
            return self._generate_structured(prompt, response_schema)

    def _generate_structured(self, prompt: str, response_schema: type[SchemaT]) -> dict:
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
                # Ollama emits progress chunks while a very slow CPU generation
                # is still healthy. Reading the NDJSON stream prevents the socket
                # timeout from treating a long generation as a dead server.
                "stream": True,
                "keep_alive": self.keep_alive,
                "options": {
                    "num_ctx": settings.local_llm_num_ctx,
                    "num_predict": self.max_tokens,
                    "num_thread": settings.local_llm_num_thread,
                    "num_batch": settings.local_llm_num_batch,
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
                generated = _read_streamed_response(response.read())
        except TimeoutError as exc:
            raise ApiError(
                504, "LLM_TIMEOUT", "Le modèle local a dépassé le délai autorisé."
            ) from exc
        except HTTPError as exc:
            if exc.code == 404:
                raise ApiError(
                    503,
                    "LLM_MODEL_NOT_FOUND",
                    "Le modèle Ollama configuré n’est pas installé.",
                ) from exc
            raise ApiError(
                502,
                "LLM_GENERATION_FAILED",
                "Ollama a refusé ou interrompu la génération.",
                {"http_status": exc.code},
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, TimeoutError):
                raise ApiError(
                    504, "LLM_TIMEOUT", "Le modèle local a dépassé le délai autorisé."
                ) from exc
            raise ApiError(503, "LLM_UNAVAILABLE", "Le serveur Ollama est indisponible.") from exc
        except OSError as exc:
            raise ApiError(503, "LLM_UNAVAILABLE", "Le serveur Ollama est indisponible.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ApiError(
                502, "LLM_INVALID_RESPONSE", "Ollama a retourné une réponse invalide."
            ) from exc
        return parse_json_response(generated)


def _read_streamed_response(raw_body: bytes) -> str:
    chunks: list[str] = []
    try:
        for raw_line in raw_body.splitlines():
            if not raw_line.strip():
                continue
            body = json.loads(raw_line)
            if not isinstance(body, dict) or not isinstance(body.get("response"), str):
                raise ValueError
            chunks.append(body["response"])
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise ApiError(
            502, "LLM_INVALID_RESPONSE", "Ollama a retourné une réponse invalide."
        ) from exc
    if not chunks:
        raise ApiError(502, "LLM_INVALID_RESPONSE", "Ollama a retourné une réponse invalide.")
    return "".join(chunks)


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
