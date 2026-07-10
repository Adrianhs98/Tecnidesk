"""
Modelo: users — Personal del taller (admin o técnico).
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class UserRoleEnum(str, enum.Enum):
    admin = "admin"
    technician = "technician"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[UserRoleEnum] = mapped_column(
        Enum(UserRoleEnum, name="user_role_enum"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)

    # password_hash almacena el hash bcrypt — NUNCA la contraseña en texto plano
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    reset_password_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_password_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop", back_populates="users")  # noqa: F821
    assigned_tickets: Mapped[list["Ticket"]] = relationship(  # noqa: F821
        "Ticket", back_populates="assigned_technician", foreign_keys="Ticket.assigned_technician_id"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(  # noqa: F821
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User email={self.email!r} role={self.role}>"
