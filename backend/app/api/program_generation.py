from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentAdministrator, DbSession
from app.schemas.training_program import TrainingProgramResponse
from app.services.program_generation import ProgramGenerationService

router = APIRouter(prefix="/api/training-cases", tags=["training-program-generation"])


@router.post("/{case_id}/program/generate-draft", response_model=TrainingProgramResponse)
def generate_program_draft(
    case_id: UUID, session: DbSession, administrator: CurrentAdministrator
) -> TrainingProgramResponse:
    return ProgramGenerationService(session).generate(case_id, administrator.id)
