"""
Schemas Pydantic para el dominio de Técnicos.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class TechnicianCreate(BaseModel):
    """Payload para crear un nuevo técnico."""
    full_name: str = Field(..., min_length=2, max_length=200, description="Nombre completo del técnico")
    contact: str | None = Field(None, max_length=100, description="Teléfono o contacto")
    declared_specialty: str | None = Field(None, max_length=200, description="Especialidad declarada")
    email: EmailStr | None = Field(None, description="Email del técnico para login")
    password: str | None = Field(None, min_length=8, description="Contraseña de acceso")


class TechnicianUpdate(BaseModel):
    """Payload para editar un técnico."""
    full_name: str | None = Field(None, min_length=2, max_length=200)
    contact: str | None = Field(None, max_length=100)
    declared_specialty: str | None = Field(None, max_length=200)


class TechnicianResponse(BaseModel):
    """Respuesta estándar para un técnico."""
    id: uuid.UUID
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

    model_config = {"from_attributes": True}
