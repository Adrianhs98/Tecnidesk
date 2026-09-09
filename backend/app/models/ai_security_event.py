"""
Model: ai_security_events — Audit log for AI prompt injection attempts and security violations.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, _utcnow

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.technician import Technician
    from app.models.ticket import Ticket


class AiSecurityEvent(UUIDMixin, Base):
    __tablename__ = "ai_security_events"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technician_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="injection_attempt",
    )
    message_excerpt: Mapped[str] = mapped_column(
        String(280),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    shop: Mapped["Shop"] = relationship("Shop")
    technician: Mapped["Technician | None"] = relationship("Technician")
    ticket: Mapped["Ticket | None"] = relationship("Ticket")
