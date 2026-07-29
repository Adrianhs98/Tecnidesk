"""
Modelo: technicians — Perfiles de técnicos del taller.

Entidad propia, aislada por taller (shop_id).
Desvinculada de users — los técnicos son perfiles operativos independientes.
El campo user_id es opcional para vincular, en el futuro, una cuenta de acceso real.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Technician(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "technicians"

    __table_args__ = (
        # Evita técnicos duplicados con el mismo nombre dentro del mismo taller
        UniqueConstraint("shop_id", "full_name", name="uq_technician_shop_name"),
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Contacto directo del técnico (teléfono, etc.)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Especialidad declarada manualmente por el dueño del taller
    # Separada de la especialidad inferida por historial (calculada en runtime)
    declared_specialty: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Baja lógica — no eliminar historial
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Vinculación opcional con una cuenta de usuario real (futura integración de login)
    # UNIQUE: un usuario solo puede vincularse a un perfil técnico
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop", back_populates="technicians")  # noqa: F821
    assigned_tickets: Mapped[list["Ticket"]] = relationship(  # noqa: F821
        "Ticket", back_populates="technician", foreign_keys="Ticket.technician_id"
    )

    def __repr__(self) -> str:
        return f"<Technician id={self.id} name={self.full_name!r} shop={self.shop_id}>"
