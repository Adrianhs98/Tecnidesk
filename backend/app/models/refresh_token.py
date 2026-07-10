"""
Modelo: refresh_tokens — Tokens de refresco stateful (D9).

Estrategia de seguridad:
  - token_hash: SHA-256 del refresh token JWT. Nunca guardamos el token en claro.
  - Single-use: al hacer /auth/refresh, el token actual se revoca (revoked_at = now)
    y se emite uno nuevo.
  - /auth/logout: marca el token como revocado (revoked_at = now).
  - shop_id: FK denormalizada para filtros rápidos sin JOIN a users.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, _utcnow


class RefreshToken(UUIDMixin, Base):
    __tablename__ = "refresh_tokens"

    # FK al usuario propietario del token
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FK al taller — denormalizada para filtros rápidos en SubscriptionGuard (D1)
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 del token JWT — nunca el token en claro
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # Cuándo expira el refresh token (mirrors JWT exp)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # NULL = activo. NOT NULL = revocado manualmente (logout) o rotado (/refresh)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Relaciones
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")  # noqa: F821

    @property
    def is_valid(self) -> bool:
        """True si el token no ha sido revocado y aún no ha expirado."""
        from datetime import timezone as tz
        now = datetime.now(tz.utc)
        return self.revoked_at is None and self.expires_at > now

    def __repr__(self) -> str:
        revoked = "revocado" if self.revoked_at else "activo"
        return f"<RefreshToken user_id={self.user_id} {revoked}>"
