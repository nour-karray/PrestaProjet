import re
from typing import Any, cast
from uuid import UUID

from sqlalchemy import String, func, or_, select, update
from sqlalchemy import cast as sql_cast
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.models.trainer import Trainer, TrainerCV


class TrainerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, trainer_id: UUID) -> Trainer | None:
        return self.session.get(Trainer, trainer_id)

    def list(
        self,
        search: str | None,
        include_inactive: bool,
        page: int,
        page_size: int,
        specialty: str | None = None,
    ) -> tuple[list[Trainer], int]:
        filters: list[ColumnElement[bool]] = []
        if not include_inactive:
            filters.append(Trainer.is_active.is_(True))
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Trainer.full_name.ilike(term),
                    Trainer.job_title.ilike(term),
                    Trainer.company.ilike(term),
                    Trainer.city.ilike(term),
                )
            )
        if specialty:
            stop_words = {
                "formation",
                "dans",
                "avec",
                "pour",
                "des",
                "les",
                "une",
                "sur",
                "the",
                "and",
            }
            raw_terms = [specialty.strip(), *re.findall(r"[\wÀ-ÿ]+", specialty)]
            terms = list(
                dict.fromkeys(
                    term
                    for term in raw_terms
                    if term
                    and term.casefold() not in stop_words
                    and (len(term) >= 3 or term.casefold() == "rh")
                )
            )
            specialty_filters: list[ColumnElement[bool]] = []
            for specialty_term in terms:
                like_term = f"%{specialty_term}%"
                specialty_filters.extend(
                    [
                        Trainer.job_title.ilike(like_term),
                        Trainer.notes.ilike(like_term),
                        Trainer.id.in_(
                            select(TrainerCV.trainer_id).where(
                                TrainerCV.trainer_id.is_not(None),
                                TrainerCV.parsed_json.is_not(None),
                                sql_cast(TrainerCV.parsed_json, String).ilike(like_term),
                            )
                        ),
                    ]
                )
            if specialty_filters:
                filters.append(or_(*specialty_filters))
        total = self.session.scalar(select(func.count(Trainer.id)).where(*filters)) or 0
        statement = (
            select(Trainer)
            .where(*filters)
            .order_by(Trainer.full_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def add(self, trainer: Trainer) -> None:
        self.session.add(trainer)
        self.session.flush()


class CVRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, cv_id: UUID) -> TrainerCV | None:
        return self.session.get(TrainerCV, cv_id)

    def get_by_hash(self, sha256: str) -> TrainerCV | None:
        return self.session.scalar(select(TrainerCV).where(TrainerCV.sha256 == sha256))

    def get_latest_by_trainer(self, trainer_id: UUID) -> TrainerCV | None:
        statement = (
            select(TrainerCV)
            .where(TrainerCV.trainer_id == trainer_id)
            .order_by(TrainerCV.uploaded_at.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def add(self, cv: TrainerCV) -> None:
        self.session.add(cv)
        self.session.flush()

    def list(self, page: int, page_size: int) -> tuple[list[TrainerCV], int]:
        total = self.session.scalar(select(func.count(TrainerCV.id))) or 0
        statement = (
            select(TrainerCV)
            .order_by(TrainerCV.uploaded_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement)), total

    def delete(self, cv: TrainerCV) -> None:
        self.session.delete(cv)

    def mark_processing(self, cv_id: UUID) -> bool:
        statement = (
            update(TrainerCV)
            .where(
                TrainerCV.id == cv_id,
                TrainerCV.extraction_status.in_(["UPLOADED", "FAILED"]),
            )
            .values(extraction_status="PROCESSING", extraction_error=None)
        )
        result = cast(CursorResult[Any], self.session.execute(statement))
        return bool(result.rowcount)

    def get_for_update(self, cv_id: UUID) -> TrainerCV | None:
        statement = select(TrainerCV).where(TrainerCV.id == cv_id).with_for_update()
        return self.session.scalar(statement)
