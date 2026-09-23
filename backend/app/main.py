from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai_health import router as ai_health_router
from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.program_generation import router as program_generation_router
from app.api.trainers import router as trainers_router
from app.api.training_cases import router as training_cases_router
from app.api.training_catalog import router as training_catalog_router
from app.api.training_documents import router as training_documents_router
from app.api.training_needs import router as training_needs_router
from app.api.training_pricings import router as training_pricings_router
from app.api.training_programs import router as training_programs_router
from app.core.config import settings
from app.core.errors import ApiError, api_error_handler

app = FastAPI(
    title="Gestion des formations API",
    version="0.1.0",
    description="Backend de l'application de gestion des formations professionnelles.",
)
app.add_exception_handler(ApiError, api_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.frontend_url).rstrip("/")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(ai_health_router)
app.include_router(companies_router)
app.include_router(training_cases_router)
app.include_router(training_catalog_router)
app.include_router(training_needs_router)
app.include_router(training_programs_router)
app.include_router(program_generation_router)
app.include_router(training_pricings_router)
app.include_router(training_documents_router)
app.include_router(trainers_router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
