"""
Modelo: tickets — Orden de reparación principal.

SEGURIDAD CRÍTICA:
  pin_or_password se cifra con Fernet antes de persistir (D2).
  Nunca aparece en los schemas públicos de Pydantic.
  Solo se desencripta en la capa de servicio interna.
"""
import enum
import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class TicketStatusEnum(str, enum.Enum):
    EN_ESPERA_INGRESO = "EN_ESPERA_INGRESO"
    EN_REVISION = "EN_REVISION"
    ESPERANDO_APROBACION = "ESPERANDO_APROBACION"
    EN_REPARACION = "EN_REPARACION"
    ESPERANDO_REPUESTO = "ESPERANDO_REPUESTO"
    LISTO_PARA_RETIRAR = "LISTO_PARA_RETIRAR"
    NO_APROBADO = "NO_APROBADO"


class Ticket(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tickets"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    # FK legacy → users.id (se retirará en la migración de limpieza, Fase 8)
    assigned_technician_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # FK nueva → technicians.id (entidad propia del módulo de técnicos)
    technician_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id"),
        nullable=True,
        index=True,
    )

    device_brand: Mapped[str] = mapped_column(String(100), nullable=False)
    device_model: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_description: Mapped[str] = mapped_column(Text, nullable=False)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostic_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # CIFRADO con Fernet (D2) — almacena el token Fernet cifrado, no el PIN
    # Desencriptar ÚNICAMENTE en servicios internos autorizados
    pin_or_password: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[TicketStatusEnum] = mapped_column(
        Enum(TicketStatusEnum, name="ticket_status_enum"),
        nullable=False,
        default=TicketStatusEnum.EN_ESPERA_INGRESO,
    )

    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    # D8: currency eliminada — siempre USD

    # UUID único para URL pública sin login (Regla 5)
    # default auto-generado en nivel ORM — nunca necesita valor manual (C2)
    tracking_token: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop", back_populates="tickets")  # noqa: F821
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tickets")  # noqa: F821
    # Relación legacy → User (mantiene compatibilidad hasta la migración de limpieza)
    assigned_technician_legacy: Mapped["User | None"] = relationship(  # noqa: F821
        "User", back_populates="assigned_tickets_legacy", foreign_keys=[assigned_technician_id]
    )
    # Relación nueva → Technician (módulo de técnicos)
    technician: Mapped["Technician | None"] = relationship(  # noqa: F821
        "Technician", back_populates="assigned_tickets", foreign_keys=[technician_id]
    )
    items: Mapped[list["TicketItem"]] = relationship(  # noqa: F821
        "TicketItem", back_populates="ticket", cascade="all, delete-orphan"
    )
    evidences: Mapped[list["TicketEvidence"]] = relationship(  # noqa: F821
        "TicketEvidence", back_populates="ticket", cascade="all, delete-orphan"
    )
    webhook_logs: Mapped[list["WebhookLog"]] = relationship(  # noqa: F821
        "WebhookLog", back_populates="ticket", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["TicketStatusHistory"]] = relationship(  # noqa: F821
        "TicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketStatusHistory.changed_at.asc()"
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} status={self.status}>"
