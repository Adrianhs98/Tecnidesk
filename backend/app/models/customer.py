"""
Modelo: customers — Clientes del taller de reparación.
Multi-tenant: aislado por shop_id.
"""
import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Customer(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customers"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Formato validado: 593XXXXXXXXX (12 dígitos, código Ecuador) — Regla 3
    # Almacenado limpio (sin +, espacios ni guiones), validación en schema Pydantic
    phone_number: Mapped[str] = mapped_column(String(12), nullable=False)

    email: Mapped[str] = mapped_column(String(254), nullable=False)

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop", back_populates="customers")  # noqa: F821
    tickets: Mapped[list["Ticket"]] = relationship(  # noqa: F821
        "Ticket", back_populates="customer"
    )

    # A11: Índice compuesto por shop + teléfono para búsquedas rápidas
    __table_args__ = (
        Index("ix_customers_shop_phone", "shop_id", "phone_number"),
    )

    def __repr__(self) -> str:
        return f"<Customer full_name={self.full_name!r} phone={self.phone_number!r}>"
