"""
Modelo: ticket_items — Repuestos y mano de obra usados en una reparación.
"""
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


import enum

class ItemTypeEnum(str, enum.Enum):
    part = "part"
    labor = "labor"
    other = "other"


class TicketItem(UUIDMixin, Base):
    __tablename__ = "ticket_items"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # null si es mano de obra sin repuesto de inventario
    inventory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Tipo de ítem: repuesto, mano de obra, etc. (Obligatorio en el schema)
    item_type: Mapped[ItemTypeEnum] = mapped_column(
        Enum(ItemTypeEnum, name="item_type_enum"),
        nullable=False,
        default=ItemTypeEnum.other,
    )

    description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relaciones
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="items")  # noqa: F821
    inventory_item: Mapped["Inventory | None"] = relationship(  # noqa: F821
        "Inventory", back_populates="ticket_items"
    )

    def __repr__(self) -> str:
        return f"<TicketItem description={self.description!r} qty={self.quantity}>"
