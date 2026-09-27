from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TrainingCatalogItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    title: str
    is_active: bool
