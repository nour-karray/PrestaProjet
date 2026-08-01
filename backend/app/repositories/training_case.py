from datetime import date
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.elements import ColumnElement

from app.models.training_case import (
    ActivityLog,
    TrainingCase,
    TrainingCaseCounter,
    TrainingCaseStatus,
)


class TrainingCaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def next_reference(self, year: int) -> str:
        if self.session.get_bind().dialect.name == "postgresql":
            self.session.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": 4_200_000 + year},
            )
        counter = self.session.get(TrainingCaseCounter, year, with_for_update=True)
        if counter is None:
            counter = TrainingCaseCounter(year=year, next_value=2)
            self.session.add(counter)
            number = 1
        else:
            number = counter.next_value
            counter.next_value += 1
        self.session.flush()
        return f"TR-{year}-{number:06d}"

    def add(self, training_case: TrainingCase) -> None:
        self.session.add(training_case)
        self.session.flush()

    def get(self, case_id: UUID) -> TrainingCase | None:
        statement = (
            select(TrainingCase)
            .where(TrainingCase.id == case_id)
            .options(
                joinedload(TrainingCase.company),
                joinedload(TrainingCase.primary_contact),
                joinedload(TrainingCase.trainer),
            )
        )
        return self.session.scalar(statement)

    def get_for_update(self, case_id: UUID) -> TrainingCase | None:
        return self.session.scalar(
            select(TrainingCase).where(TrainingCase.id == case_id).with_for_update()
        )

    def list(
        self,
        *,
        reference: str | None,
        company_id: UUID | None,
        theme: str | None,
        status: TrainingCaseStatus | None,
        created_from: date | None,
        created_to: date | None,
        desired_start_from: date | None,
        desired_start_to: date | None,
        include_archived: bool,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[TrainingCase], int]:
        filters: list[ColumnElement[bool]] = []
        if not include_archived:
            filters.append(TrainingCase.is_archived.is_(False))
        if reference:
            filters.append(TrainingCase.reference.ilike(f"%{reference}%"))
        if company_id:
            filters.append(TrainingCase.company_id == company_id)
        if theme:
            filters.append(TrainingCase.theme.ilike(f"%{theme}%"))
        if status:
            filters.append(TrainingCase.status == status.value)
        if created_from:
            filters.append(func.date(TrainingCase.created_at) >= created_from)
        if created_to:
            filters.append(func.date(TrainingCase.created_at) <= created_to)
        if desired_start_from:
            filters.append(TrainingCase.desired_start_date >= desired_start_from)
        if desired_start_to:
            filters.append(TrainingCase.desired_start_date <= desired_start_to)

        total = self.session.scalar(select(func.count(TrainingCase.id)).where(*filters)) or 0
        order_column = getattr(TrainingCase, sort_by)
        order = order_column.desc() if sort_order == "desc" else order_column.asc()
        statement = (
            select(TrainingCase)
            .where(*filters)
            .options(
                joinedload(TrainingCase.company),
                joinedload(TrainingCase.primary_contact),
                joinedload(TrainingCase.trainer),
            )
            .order_by(order)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.session.scalars(statement).unique()), total

    def dashboard_counts(self) -> tuple[int, int, int]:
        active = (
            self.session.scalar(
                select(func.count(TrainingCase.id)).where(
                    TrainingCase.is_archived.is_(False),
                    TrainingCase.status != TrainingCaseStatus.ANNULE.value,
                )
            )
            or 0
        )
        cancelled = (
            self.session.scalar(
                select(func.count(TrainingCase.id)).where(
                    TrainingCase.status == TrainingCaseStatus.ANNULE.value,
                    TrainingCase.is_archived.is_(False),
                )
            )
            or 0
        )
        archived = (
            self.session.scalar(
                select(func.count(TrainingCase.id)).where(TrainingCase.is_archived.is_(True))
            )
            or 0
        )
        return active, cancelled, archived


class ActivityRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, activity: ActivityLog) -> None:
        self.session.add(activity)

    def list_for_case(self, case_id: UUID) -> list[ActivityLog]:
        statement = (
            select(ActivityLog)
            .where(ActivityLog.training_case_id == case_id)
            .order_by(ActivityLog.created_at.desc())
        )
        return list(self.session.scalars(statement))
