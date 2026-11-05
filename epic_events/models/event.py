"""Define the SQLAlchemy ORM model for events."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.contract import Contract
    from epic_events.models.employee import Employee


class Event(Base):
    """Represent an event in the database."""

    __tablename__ = "event"

    __table_args__ = (
        CheckConstraint(
            "end_datetime > start_datetime",
            name="ck_event_end_datetime_later_than_start_datetime",
        ),
        CheckConstraint(
            "attendees_count > 0",
            name="ck_event_attendees_count_more_than_zero"
        ),
    )

    id_event: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    end_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    attendees_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    id_contract: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "contract.id_contract",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship(
        back_populates="events"
    )

    id_support_employee: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "employee.id_employee",
            onupdate="ON CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    support_employee: Mapped["Employee | None"] = relationship(
        back_populates="events"
    )

    def __repr__(self) -> str:
        return (
            f"Event(id_event={self.id_event}, "
            f"id_contract={self.id_contract}, "
            f"id_support_employee={self.id_support_employee}, "
            f"location={self.location!r}, "
            f"start_datetime={self.start_datetime})"
        )
