from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300))
    city: Mapped[str | None] = mapped_column(String(120))
    postal_code: Mapped[str | None] = mapped_column(String(30))
    country: Mapped[str | None] = mapped_column(String(120))
    tax_identifier: Mapped[str | None] = mapped_column(String(80))
    website: Mapped[str | None] = mapped_column(String(300))
    notes: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    contacts: Mapped[list["CompanyContact"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_companies_lower_name", func.lower(name), unique=True),
        Index("ix_companies_city", city),
        Index("ix_companies_country", country),
        Index("ix_companies_is_archived", is_archived),
    )


class CompanyContact(Base):
    __tablename__ = "company_contacts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    job_title: Mapped[str | None] = mapped_column(String(150))
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    company: Mapped[Company] = relationship(back_populates="contacts")

    __table_args__ = (
        Index(
            "uq_company_contacts_primary",
            company_id,
            unique=True,
            postgresql_where=is_primary.is_(True),
            sqlite_where=is_primary.is_(True),
        ),
    )
