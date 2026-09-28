from uuid import UUID

from sqlalchemy import CHAR
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UUIDChar36(TypeDecorator[UUID]):
    """Portable UUID stored as the canonical hyphenated CHAR(36) form."""

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value: UUID | str | None, dialect: Dialect) -> str | None:
        del dialect
        if value is None:
            return None
        return str(value if isinstance(value, UUID) else UUID(value))

    def process_result_value(self, value: str | None, dialect: Dialect) -> UUID | None:
        del dialect
        return UUID(value) if value is not None else None
