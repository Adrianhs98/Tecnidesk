"""
Modelo: ticket_status_history — Registro inmutable de transiciones de estado de tickets.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TicketStatusHistory(UUIDMixin, Base):
    __tablename__ = "ticket_status_history"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
        index=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Relaciones
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="status_history")  # noqa: F821
    changed_by_user: Mapped["User | None"] = relationship(  # noqa: F821
        "User", foreign_keys=[changed_by_user_id]
    )

    def __repr__(self) -> str:
        return (
            f"<TicketStatusHistory id={self.id} ticket_id={self.ticket_id} "
            f"from={self.from_status} to={self.to_status} changed_at={self.changed_at}>"
        )
