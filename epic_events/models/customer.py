"""Define the SQLAlchemy ORM model for customer."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    func,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.employee import Employee


class Customer(Base):
    """Represent a customer in the database."""

    __tablename__ = "customer"

    id_customer: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
        unique=True,
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    company: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    creation_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    last_update_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        ),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1")
    )

    id_sales_employee: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "employee.id_employee",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False
    )

    sales_employee: Mapped["Employee"] = relationship(
        back_populates="customers",
    )

    def __repr__(self) -> str:
        return (
            f"Customer(id_customer={self.id_customer}, "
            f"full_name={self.full_name!r})"
        )
