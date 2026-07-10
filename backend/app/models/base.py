"""
Base de SQLAlchemy + Mixins reutilizables para todos los modelos.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Devuelve la hora UTC actual (aware)."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarativa para todos los modelos."""
    pass


class UUIDMixin:
    """Mixin que provee id UUID v4 como clave primaria."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )


class TimestampMixin:
    """
    Mixin que añade created_at y updated_at auto-gestionados.
    updated_at se actualiza automáticamente en cada UPDATE.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,  # A15: onupdate automático
        nullable=False,
    )
