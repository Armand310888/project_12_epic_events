"""Define the SQLAlchemy ORM model for employee roles."""

from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.employee import Employee


class Role(Base):
    """Represent an employee role in the database."""

    __tablename__ = "role"

    id_role: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="role",
    )

    def __repr__(self) -> str:
        return f"Role(id_role={self.id_role}, name={self.name!r})"
