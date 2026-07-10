"""
Modelo: ticket_evidences — Fotos/documentos adjuntos a un ticket.

Almacena URLs de archivos subidos a Cloudflare R2 (D3).
Tipos: foto del dispositivo, comprobante, diagnóstico, etc.
"""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class EvidenceTypeEnum(str, enum.Enum):
    initial_photo = "initial_photo"         # Foto del dispositivo al recibirlo
    diagnostic_photo = "diagnostic_photo"   # Foto durante diagnóstico
    repair_photo = "repair_photo"           # Foto durante reparación
    final_photo = "final_photo"             # Foto del dispositivo reparado
    document = "document"                   # Documento adjunto (PDF, etc.)


class TicketEvidence(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "ticket_evidences"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tipo de evidencia
    evidence_type: Mapped[EvidenceTypeEnum] = mapped_column(
        Enum(EvidenceTypeEnum, name="evidence_type_enum"),
        nullable=False,
    )

    # URL pública en Cloudflare R2 (D3)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Nombre original del archivo (ej: "foto_pantalla_rota.jpg")
    file_name: Mapped[str] = mapped_column(String(300), nullable=False)

    # MIME type (ej: "image/jpeg", "application/pdf")
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Tamaño en bytes
    file_size: Mapped[int] = mapped_column(nullable=False)

    # Relaciones
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="evidences")

    def __repr__(self) -> str:
        return f"<TicketEvidence type={self.evidence_type} file={self.file_name!r}>"
