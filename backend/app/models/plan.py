"""
Modelo: plans — Planes de suscripción disponibles en TecniDesk.
"""
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class Plan(UUIDMixin, Base):
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Plan name={self.name!r} price_usd={self.price_usd}>"
