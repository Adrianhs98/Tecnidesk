"""
Schemas Pydantic para el dominio de Tickets (Órdenes de Reparación).
Aisla los datos sensibles de los endpoints.
"""
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, computed_field, EmailStr, model_validator

from app.models.ticket import TicketStatusEnum
from app.models.ticket_item import ItemTypeEnum


# ═══════════════════════════════════════════════════════════════════════════════
# Schemas Base & Relacionados
# ═══════════════════════════════════════════════════════════════════════════════

class CustomerBasicInfo(BaseModel):
    """Información mínima del cliente embebida en las respuestas."""
    id: uuid.UUID
    full_name: str
    phone_number: str
    email: str

    model_config = {"from_attributes": True}


class TechnicianBasicInfo(BaseModel):
    """Información abstracta del usuario asignado al Ticket."""
    id: uuid.UUID
    full_name: str

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Ticket Items: Creación y Respuesta
# ═══════════════════════════════════════════════════════════════════════════════

class TicketItemCreate(BaseModel):
    """Input para añadir repuestos o mano de obra a un ticket."""
    inventory_id: uuid.UUID | None = Field(
        None, description="ID del repuesto en el inventario, None si es solo mano de obra."
    )
    item_type: ItemTypeEnum = Field(
        ..., description="'part', 'labor' o 'other'."
    )
    description: str = Field(
        ..., min_length=2, max_length=300, description="Descripción del trabajo/ítem."
    )
    quantity: int = Field(
        ..., gt=0, description="Cantidad a añadir (mínimo 1)."
    )
    unit_price: Decimal = Field(
        ..., ge=0, description="Precio unitario exacto en USD (>= 0)."
    )


class TicketItemResponse(BaseModel):
    """Respuesta pública para los ítems dentro de una orden de reparación."""
    id: uuid.UUID
    inventory_id: uuid.UUID | None
    item_type: ItemTypeEnum
    description: str
    quantity: int
    unit_price: Decimal

    model_config = {"from_attributes": True}


class TicketEvidenceResponse(BaseModel):
    """Respuesta pública para las evidencias (fotos/documentos) de un ticket."""
    id: uuid.UUID
    evidence_type: str
    file_url: str
    file_name: str
    mime_type: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketStatusHistoryResponse(BaseModel):
    """Respuesta pública para el historial de transiciones de estado de un ticket."""
    id: uuid.UUID
    ticket_id: uuid.UUID
    from_status: str | None = None
    to_status: str
    changed_by_user_id: uuid.UUID | None = None
    changed_at: datetime
    reason: str | None = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Ticket Principal: Inputs
# ═══════════════════════════════════════════════════════════════════════════════

class TicketCreate(BaseModel):
    """Payload para crear un nuevo Ticket."""
    client_email: EmailStr = Field(
        ..., description="Email del cliente. Si no existe en el taller, se crea automáticamente."
    )
    client_name: str | None = Field(
        None, description="Nombre del cliente (opcional para fallback interno)."
    )
    client_phone: str | None = Field(
        None, description="Teléfono del cliente (opcional para fallback interno)."
    )
    device_brand: str = Field(
        ..., min_length=2, max_length=100, description="Marca del dispositivo."
    )
    device_model: str = Field(
        ..., min_length=2, max_length=100, description="Modelo del dispositivo."
    )
    issue_description: str = Field(
        ..., min_length=5, description="Fallo reportado o motivo del servicio."
    )
    internal_notes: str | None = Field(
        None, description="Observaciones confidenciales del técnico."
    )
    pin_or_password: str | None = Field(
        None, max_length=50, description="PIN o Patrón descifrado (será encriptado vía Fernet)."
    )

    assignment_mode: str = Field(
        default="unassigned",
        pattern=r"^(manual|random|unassigned)$",
        description="Modo de asignación: manual, random o unassigned"
    )
    technician_id: uuid.UUID | None = Field(
        None,
        description="UUID del técnico. Requerido si assignment_mode == 'manual'"
    )

    @model_validator(mode="after")
    def validate_assignment(self):
        if self.assignment_mode == "manual" and self.technician_id is None:
            raise ValueError("technician_id es obligatorio cuando assignment_mode es 'manual'")
        return self


class TicketUpdate(BaseModel):
    """Payload para actualizaciones generales u opcionales."""
    status: TicketStatusEnum | None = None
    assigned_technician_id: uuid.UUID | None = Field(
        None, description="UUID del técnico a asignar."
    )
    internal_notes: str | None = None
    diagnostic_notes: str | None = None
    requires_approval: bool | None = None


class TicketAssignIn(BaseModel):
    """Payload específico para asignar técnico (usado en el router para claridad)."""
    technician_id: uuid.UUID


class TicketStatusUpdateIn(BaseModel):
    """Payload específico para status (usado en el router para claridad)."""
    status: TicketStatusEnum


class TicketDiagnosticUpdate(BaseModel):
    """Payload para enviar diagnóstico y presupuesto al cliente."""
    diagnostic_notes: str = Field(..., min_length=5)
    labor_cost: float = Field(..., ge=0)


# ═══════════════════════════════════════════════════════════════════════════════
# Ticket Principal: Outputs
# ═══════════════════════════════════════════════════════════════════════════════

class TicketResponse(BaseModel):
    """
    Serializador de Repuesta Base (ej. POST /tickets).
    SEGURIDAD: No declara 'pin_or_password' explícitamente.
    """
    id: uuid.UUID
    shop_id: uuid.UUID
    customer_id: uuid.UUID
    assigned_technician_id: uuid.UUID | None
    technician_id: uuid.UUID | None = None

    tracking_token: str
    device_brand: str
    device_model: str
    issue_description: str
    internal_notes: str | None
    diagnostic_notes: str | None
    requires_approval: bool

    status: TicketStatusEnum
    total_cost: Decimal | None

    # Contraseña/PIN desencriptado — solo disponible en respuestas para técnicos.
    # NUNCA incluir en PublicTicketResponse.
    device_password: str | None = None

    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class TicketListResponse(TicketResponse):
    """
    Serializador de Repuesta para listados (GET /tickets).
    Incluye info básica del cliente.
    """
    customer: CustomerBasicInfo | None = None
    technician: TechnicianBasicInfo | None = None


class TicketDetailResponse(TicketResponse):
    """
    Serializador de Repuesta para el detalle profundo (GET /tickets/{id}).
    Incluye arrays anidados y relaciones extendidas.
    """
    customer: CustomerBasicInfo | None = None
    technician: TechnicianBasicInfo | None = None
    items: list[TicketItemResponse] = []
    evidences: list[TicketEvidenceResponse] = []
    status_history: list[TicketStatusHistoryResponse] = []


class TicketStatsResponse(BaseModel):
    """Estadísticas agregadas del taller calculadas en PostgreSQL."""
    total: int
    activos: int
    listos: int
    espera: int


class PublicTicketResponse(BaseModel):
    """
    Respuesta pública y reducida para el portal de rastreo de clientes.
    """
    device_brand: str
    device_model: str
    issue_description: str
    status: TicketStatusEnum
    diagnostic_notes: str | None = None
    total_cost: Decimal | None = None
    requires_approval: bool
    contact_whatsapp: str | None = None
    tracking_token: str | None = None
    evidences: list[TicketEvidenceResponse] = []
    created_at: datetime
    updated_at: datetime | None
    
    shop_name: str | None = None
    shop_logo_url: str | None = None

    model_config = {"from_attributes": True}

    @computed_field
    def status_label(self) -> str:
        status_map = {
            "EN_ESPERA_INGRESO": "Recibido, en fila de revisión",
            "EN_REVISION": "En revisión y diagnóstico técnico",
            "ESPERANDO_APROBACION": "Esperando tu aprobación del presupuesto",
            "ESPERANDO_REPUESTO": "Esperando llegada de repuestos",
            "EN_REPARACION": "En proceso de reparación",
            "LISTO_PARA_RETIRAR": "¡Listo! Puedes pasar a retirar tu equipo",
            "NO_APROBADO": "Reparación no aprobada / Cancelada",
        }
        return status_map.get(self.status.value, str(self.status.value))


class RejectTicketRequest(BaseModel):
    """Payload para rechazar un presupuesto con motivo opcional."""
    rejection_reason: str | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# Operational Workbench Analytics (Fase 5: Cycle Times & Bottlenecks)
# ═══════════════════════════════════════════════════════════════════════════════

class StageDurationMetric(BaseModel):
    """Métrica de duración y cuello de botella para un estado específico."""
    status: TicketStatusEnum
    label: str
    avg_hours: float
    percentage_of_total: float
    is_bottleneck: bool


class CycleTimeAnalyticsResponse(BaseModel):
    """Respuesta con métricas agregadas de Lead Time, Cycle Time y Cuello de Botella."""
    lead_time_avg_hours: float
    cycle_time_avg_hours: float
    sla_compliance_rate: float
    bottleneck_stage: TicketStatusEnum | None = None
    bottleneck_stage_label: str | None = None
    tickets_analyzed_count: int
    completed_tickets_count: int
    active_tickets_count: int
    stage_durations: list[StageDurationMetric]
    time_window_days: int


