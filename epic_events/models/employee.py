"""Define the SQLAlchemy ORM model for employee."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
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
    from epic_events.models.role import Role


class Employee(Base):
    """Represent an employee in the database."""

    __tablename__ = "employee"

    id_employee: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
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

    password_hash: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1"),
    )

    id_role: Mapped[int] = mapped_column(
        ForeignKey(
            "role.id_role",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    role: Mapped["Role"] = relationship(
        back_populates="employees"
    )

    def __repr__(self) -> str:
        return (
            f"Employee(id_employee={self.id_employee}, "
            f"full_name={self.full_name!r})"
        )
