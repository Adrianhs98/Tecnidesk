"""
Modelos SQLAlchemy para el Sistema de Diagnóstico Asistido por IA con RAG Explicable.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, _utcnow

if TYPE_CHECKING:
    from app.models.shop import Shop
    from app.models.technician import Technician
    from app.models.ticket import Ticket


class DiagnosticCase(UUIDMixin, TimestampMixin, Base):
    """
    Casos de diagnóstico indexados para búsqueda semántica vectorial.
    Contiene casos sintéticos de referencia y casos reales validados por talleres.
    """
    __tablename__ = "diagnostic_cases"

    shop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    origin_ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
    derived_from_case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'synthetic' | 'real_validated'
    device_brand: Mapped[str] = mapped_column(String(100), nullable=False)
    device_model: Mapped[str] = mapped_column(String(100), nullable=False)
    symptom_text: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosed_cause: Mapped[str] = mapped_column(Text, nullable=False)
    solution_applied: Mapped[str] = mapped_column(Text, nullable=False)
    repair_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(768), nullable=False)

    # Relaciones
    shop: Mapped[Optional["Shop"]] = relationship("Shop", foreign_keys=[shop_id])
    origin_ticket: Mapped[Optional["Ticket"]] = relationship("Ticket", foreign_keys=[origin_ticket_id])
    derived_from_case: Mapped[Optional["DiagnosticCase"]] = relationship(
        "DiagnosticCase",
        remote_side="DiagnosticCase.id",
        foreign_keys=[derived_from_case_id],
    )
    conversations: Mapped[List["DiagnosticConversation"]] = relationship(
        "DiagnosticConversation",
        back_populates="diagnostic_case",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('synthetic', 'real_validated')",
            name="ck_diagnostic_cases_source_type",
        ),
        Index("ix_diagnostic_cases_shop_brand_model", "shop_id", "device_brand", "device_model"),
        Index(
            "ix_diagnostic_cases_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )


class DiagnosticConversation(UUIDMixin, Base):
    """
    Hilo de conversación interactiva técnico-asistente para diagnóstico y corrección.
    """
    __tablename__ = "diagnostic_conversations"

    diagnostic_case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_cases.id", ondelete="CASCADE"),
        nullable=True,
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    technician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id"),
        nullable=False,
    )
    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        server_default="open",
        nullable=False,
    )  # 'open' | 'confirmed' | 'corrected' | 'abandoned'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relaciones
    diagnostic_case: Mapped[Optional["DiagnosticCase"]] = relationship(
        "DiagnosticCase",
        back_populates="conversations",
    )
    ticket: Mapped["Ticket"] = relationship("Ticket")
    technician: Mapped["Technician"] = relationship("Technician")
    shop: Mapped["Shop"] = relationship("Shop")
    messages: Mapped[List["DiagnosticMessage"]] = relationship(
        "DiagnosticMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="DiagnosticMessage.created_at",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'confirmed', 'corrected', 'abandoned')",
            name="ck_diagnostic_conversations_status",
        ),
    )


class DiagnosticMessage(UUIDMixin, Base):
    """
    Mensaje individual dentro de una conversación de diagnóstico.
    """
    __tablename__ = "diagnostic_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'system' | 'technician' | 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Relaciones
    conversation: Mapped["DiagnosticConversation"] = relationship(
        "DiagnosticConversation",
        back_populates="messages",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('system', 'technician', 'assistant')",
            name="ck_diagnostic_messages_role",
        ),
    )


class DiagnosticQueryLog(UUIDMixin, Base):
    """
    Registro de telemetría de consultas de diagnóstico para calcular la madurez del modelo
    y analizar tasas de evidencia.
    """
    __tablename__ = "diagnostic_query_log"

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    top_case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type_used: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    had_sufficient_evidence: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=sa.text("true"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Relaciones
    shop: Mapped["Shop"] = relationship("Shop")
    ticket: Mapped[Optional["Ticket"]] = relationship("Ticket")
    top_case: Mapped[Optional["DiagnosticCase"]] = relationship("DiagnosticCase")
