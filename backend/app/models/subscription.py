"""
Modelo: subscriptions — Fuente de verdad de la suscripción activa (D1).
SubscriptionGuard lee ÚNICAMENTE de esta tabla para validar acceso.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin


class SubscriptionStatusEnum(str, enum.Enum):
    trial = "trial"
    active = "active"
    past_due = "past_due"
    suspended = "suspended"   # Añadido Fase 2.2 — usado por SubscriptionGuard
    cancelled = "cancelled"


class Subscription(UUIDMixin, Base):
    __tablename__ = "subscriptions"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False,
    )

    # FUENTE DE VERDAD (D1) — SubscriptionGuard verifica este campo
    status: Mapped[SubscriptionStatusEnum] = mapped_column(
        Enum(SubscriptionStatusEnum, name="subscription_status_enum"),
        nullable=False,
        default=SubscriptionStatusEnum.trial,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ends_at = fin del período actual (trial o billing) — A9
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    payment_reference: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop", back_populates="subscriptions")  # noqa: F821
    plan: Mapped["Plan"] = relationship("Plan")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Subscription shop_id={self.shop_id} status={self.status}>"
