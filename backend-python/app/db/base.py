from uuid import UUID

from sqlalchemy.orm import DeclarativeBase

from app.db.types import UUIDChar36


class Base(DeclarativeBase):
    type_annotation_map = {UUID: UUIDChar36()}
