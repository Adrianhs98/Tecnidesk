"""
Modelo: inventory — Repuestos e insumos del taller.
Multi-tenant: aislado por shop_id.
"""
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Inventory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "inventory"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_name: Mapped[str] = mapped_column(String(300), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    selling_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Alerta de stock bajo (Regla de negocio: si stock <= low_stock_alert → notificar)
    low_stock_alert: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop", back_populates="inventory")  # noqa: F821
    ticket_items: Mapped[list["TicketItem"]] = relationship(  # noqa: F821
        "TicketItem", back_populates="inventory_item"
    )

    def __repr__(self) -> str:
        return f"<Inventory item={self.item_name!r} stock={self.stock_quantity}>"
