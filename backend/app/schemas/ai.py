from typing import Literal

from pydantic import BaseModel


class AIHealthResponse(BaseModel):
    status: Literal["available", "unavailable"]
    provider: Literal["ollama"]
    model: str | None
    model_available: bool
    latency_ms: int
    reason: str | None
