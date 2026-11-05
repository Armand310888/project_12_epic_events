"""Define the SQLAlchemy ORM model for customer contracts."""

from decimal import Decimal
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    func,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from epic_events.database import Base

if TYPE_CHECKING:
    from epic_events.models.customer import Customer


class Contract(Base):
    """Represent a customer's contract in the database."""

    __tablename__ = "contract"

    __table_args__ = (
        CheckConstraint(
            "total_amount >= 0",
            name="ck_contract_total_amount_nonnegative",
        ),
        CheckConstraint(
            "outstanding_balance >= 0",
            name="ck_contract_outstanding_balance_nonnegative",
        ),
        CheckConstraint(
            "outstanding_balance <= total_amount",
            name="ck_contract_outstanding_balance_"
            "equal_or_less_than_total_amount"
        ),
        CheckConstraint(
            "is_signed IN (0, 1)",
            name="ck_contract_is_signed_boolean"
        )
    )

    id_contract: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2
        ),
        nullable=False

    )

    outstanding_balance: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False
    )

    creation_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )

    is_signed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("0"),
    )

    id_customer: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "customer.id_customer",
            onupdate="CASCADE",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="contracts"
    )

    def __repr__(self) -> str:
        return (
            f"Contract(id_contract={self.id_contract}, "
            f"id_customer={self.id_customer})"
        )
