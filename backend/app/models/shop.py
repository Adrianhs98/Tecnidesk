"""
Modelo: shops — Talleres de reparación (clientes del SaaS).
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin
from app.models.subscription import SubscriptionStatusEnum


class Shop(UUIDMixin, Base):
    __tablename__ = "shops"

    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Subdominio validado — regex ^[a-z0-9-]{3,30}$ (A10, validado en schema Pydantic)
    subdomain: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)

    # Nombre de sesión para Evolution API (D5: string externo, sin lógica interna)
    whatsapp_session_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Logo opcional del taller (Whitelabel)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Configuración de SLAs por estado en formato JSON
    sla_config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    # Contacto del taller (MVP)
    contact_email: Mapped[str] = mapped_column(String(254), nullable=False)
    contact_whatsapp: Mapped[str] = mapped_column(String(20), nullable=False)

    # Estado de suscripción — sincronizado por evento desde subscriptions (D1)
    subscription_status: Mapped[SubscriptionStatusEnum] = mapped_column(
        Enum(SubscriptionStatusEnum, name="shop_subscription_status_enum"),
        nullable=False,
        default=SubscriptionStatusEnum.trial,
    )

    # Referencia histórica de fin de trial — NO usar en lógica de negocio (A9 / D1)
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relaciones
    technicians: Mapped[list["Technician"]] = relationship(  # noqa: F821
        "Technician", back_populates="shop", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(  # noqa: F821
        "Subscription", back_populates="shop", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="shop", cascade="all, delete-orphan"
    )
    customers: Mapped[list["Customer"]] = relationship(  # noqa: F821
        "Customer", back_populates="shop", cascade="all, delete-orphan"
    )
    inventory: Mapped[list["Inventory"]] = relationship(  # noqa: F821
        "Inventory", back_populates="shop", cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(  # noqa: F821
        "Ticket", back_populates="shop", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Shop subdomain={self.subdomain!r} status={self.subscription_status}>"
