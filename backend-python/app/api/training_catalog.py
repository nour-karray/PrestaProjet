from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentAdministrator, DbSession
from app.models.training_catalog import TrainingCatalogItem
from app.schemas.training_catalog import TrainingCatalogItemResponse

router = APIRouter(prefix="/api", tags=["training-catalog"])


@router.get("/training-catalog", response_model=list[TrainingCatalogItemResponse])
def list_active_training_catalog(
    session: DbSession, _: CurrentAdministrator
) -> list[TrainingCatalogItemResponse]:
    items = session.scalars(
        select(TrainingCatalogItem)
        .where(TrainingCatalogItem.is_active.is_(True))
        .order_by(TrainingCatalogItem.category, TrainingCatalogItem.title)
    ).all()
    return [TrainingCatalogItemResponse.model_validate(item) for item in items]
