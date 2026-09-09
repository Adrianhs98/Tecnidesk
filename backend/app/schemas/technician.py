"""
Schemas Pydantic para el dominio de Técnicos.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class TechnicianCreate(BaseModel):
    """Payload para crear un nuevo técnico."""
    full_name: str = Field(..., min_length=2, max_length=200, description="Nombre completo del técnico")
    contact: str | None = Field(None, max_length=100, description="Teléfono o contacto")
    declared_specialty: str | None = Field(None, max_length=200, description="Especialidad declarada")
    email: EmailStr | None = Field(None, description="Email del técnico para login")
    generate_access: bool = Field(False, description="Generar y enviar credenciales de acceso")

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("full_name must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("contact", "declared_specialty")
    @classmethod
    def sanitize_optional_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None


class TechnicianUpdate(BaseModel):
    """Payload para editar un técnico."""
    full_name: str | None = Field(None, min_length=2, max_length=200)
    contact: str | None = Field(None, max_length=100)
    declared_specialty: str | None = Field(None, max_length=200)

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("full_name must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("contact", "declared_specialty")
    @classmethod
    def sanitize_optional_text(cls, v: str | None) -> str | None:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None


class TechnicianAccessCreate(BaseModel):
    """Payload para generar acceso a un técnico existente."""
    email: EmailStr = Field(..., description="Email del técnico para login")


class TechnicianResponse(BaseModel):
    """Respuesta estándar para un técnico."""
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    full_name: str
    contact: str | None
    declared_specialty: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class InferredSpecialty(BaseModel):
    """Especialidad calculada en base a tickets históricos."""
    category: str
    emoji: str
    count: int


class TechnicianWithMetrics(TechnicianResponse):
    """Respuesta con métricas agregadas."""
    active_tickets: int
    total_tickets: int
    inferred_specialties: list[InferredSpecialty]
    attributed_value: Decimal
    delivered_value: Decimal


class ShopTotals(BaseModel):
    """Totales agrupados a nivel de taller."""
    total_tickets: int
    total_attributed: Decimal
    total_delivered: Decimal


class TechnicianMetricsTable(BaseModel):
    """Respuesta del endpoint GET /technicians/metrics"""
    technicians: list[TechnicianWithMetrics]
    shop_totals: ShopTotals


class TechnicianMeResponse(BaseModel):
    """Perfil del técnico autenticado para el portal de técnicos."""
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    full_name: str
    email: str | None = None
    role: str
    declared_specialty: str | None = None
    inferred_specialties: list[InferredSpecialty] = []
    active_tickets_count: int = 0
    completed_tickets_count: int = 0
    allow_technician_intake: bool = False

    model_config = {"from_attributes": True}
