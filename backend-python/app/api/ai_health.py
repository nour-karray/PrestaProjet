from dataclasses import asdict

from fastapi import APIRouter

from app.ai.local_llm import OllamaLocalLLMClient
from app.api.deps import CurrentAdministrator
from app.schemas.ai import AIHealthResponse

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.get("/health", response_model=AIHealthResponse)
def ai_health(_: CurrentAdministrator) -> AIHealthResponse:
    health = OllamaLocalLLMClient().health()
    return AIHealthResponse.model_validate(
        {**asdict(health), "model_available": health.status == "available"}
    )
