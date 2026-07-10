"""
Modelo: webhook_logs — Registro de notificaciones HTTP salientes.

Cada vez que TecniDesk envía una notificación al taller (cambio de estado
de ticket, etc.), se registra aquí para auditoría y retry.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, _utcnow


class WebhookStatusEnum(str, enum.Enum):
    pending = "pending"       # Pendiente de enviar
    sent = "sent"            # Enviado exitosamente
    failed = "failed"        # Falló después de reintentos
    retrying = "retrying"    # En proceso de reintento


class WebhookLog(UUIDMixin, Base):
    __tablename__ = "webhook_logs"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Evento que disparó el webhook (ej: "ticket.status_changed")
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # URL a la que se envió (puede ser personalizada por taller)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Payload JSON enviado (para debugging)
    payload: Mapped[str] = mapped_column(Text, nullable=False)

    # Respuesta HTTP recibida (status code + body)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Estado actual del webhook
    status: Mapped[WebhookStatusEnum] = mapped_column(
        Enum(WebhookStatusEnum, name="webhook_status_enum"),
        nullable=False,
        default=WebhookStatusEnum.pending,
    )

    # Número de intentos realizados
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relaciones
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="webhook_logs")

    def __repr__(self) -> str:
        return f"<WebhookLog event={self.event_type!r} status={self.status}>"
