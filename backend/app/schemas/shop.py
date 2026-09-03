"""
Schemas Pydantic — Shop (Taller)
"""
import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class ShopCreate(BaseModel):
    """Schema para crear un nuevo taller (onboarding)."""

    business_name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Nombre comercial del taller",
        examples=["Reparaciones El Rayo"],
    )
    owner_name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Nombre completo del dueño",
        examples=["Juan Pérez"],
    )
    subdomain: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Subdominio único (solo minúsculas, números y guiones)",
        examples=["el-rayo", "reparaciones-jp"],
    )
    whatsapp_session_name: str | None = Field(
        None,
        max_length=100,
        description="Nombre de sesión para Evolution API (opcional)",
        examples=["elrayo_whatsapp"],
    )
    contact_email: EmailStr = Field(
        ...,
        description="Email de contacto del taller",
        examples=["contacto@elrayo.com"],
    )
    contact_whatsapp: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="WhatsApp de contacto del taller (formato internacional)",
        examples=["593991234567"],
    )
    admin_email: EmailStr = Field(
        ...,
        description="Email del primer usuario administrador",
        examples=["admin@elrayo.com"],
    )
    admin_password: str = Field(
        ...,
        min_length=8,
        description="Contraseña del administrador (mínimo 8 caracteres)",
    )

    @field_validator("subdomain")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        """Valida que el subdomain cumpla con el patrón ^[a-z0-9-]{3,30}$"""
        if not re.match(r"^[a-z0-9-]{3,30}$", v):
            raise ValueError(
                "El subdomain solo puede contener minúsculas, números y guiones "
                "(mínimo 3, máximo 30 caracteres)"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "business_name": "Reparaciones El Rayo",
                    "owner_name": "Juan Pérez",
                    "subdomain": "el-rayo",
                    "whatsapp_session_name": "elrayo_whatsapp",
                    "contact_email": "contacto@elrayo.com",
                    "contact_whatsapp": "593991234567",
                    "admin_email": "admin@elrayo.com",
                    "admin_password": "S3cur3P@ss!2024",
                }
            ]
        }
    }


class ShopResponse(BaseModel):
    """Schema de respuesta para Shop (sin datos sensibles)."""

    id: str
    business_name: str
    owner_name: str
    subdomain: str
    contact_email: str
    contact_whatsapp: str
    subscription_status: str
    trial_ends_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShopOnboardingResponse(BaseModel):
    """Respuesta completa del onboarding (shop + email del admin creado)."""

    shop: ShopResponse
    admin_email: str = Field(
        ...,
        description="Email del administrador creado (para login posterior)",
    )


ALLOWED_SLA_STATUSES = {"EN_ESPERA_INGRESO", "EN_REVISION", "EN_REPARACION"}


class SlaConfigUpdate(BaseModel):
    """Schema para actualizar los umbrales de SLA configurables por taller."""

    custom_thresholds: dict[str, int] = Field(
        ...,
        description="Mapa de estado a horas de SLA (1-720)",
        examples=[{"EN_REVISION": 12, "EN_REPARACION": 36}],
    )

    @field_validator("custom_thresholds", mode="before")
    @classmethod
    def validate_keys_and_values(cls, v: dict[str, int]) -> dict[str, int]:
        if not isinstance(v, dict):
            raise ValueError("custom_thresholds debe ser un objeto/diccionario.")
        for k, val in v.items():
            if k not in ALLOWED_SLA_STATUSES:
                raise ValueError(f"Estado '{k}' no es configurable para SLA.")
            if isinstance(val, bool) or not isinstance(val, int) or val < 1 or val > 720:
                raise ValueError(f"Horas para '{k}' deben ser un entero entre 1 y 720.")
        return v


# Alias para compatibilidad de nomenclatura
SlaConfigUpdateRequest = SlaConfigUpdate


class SlaConfigResponse(BaseModel):
    """Schema de respuesta con la configuración efectiva y defaults de SLA."""

    effective_thresholds: dict[str, int] = Field(
        ...,
        description="Umbrales resultantes combinando defaults con overrides del taller",
    )
    custom_thresholds: dict[str, int] = Field(
        ...,
        description="Overrides configurados explícitamente por el taller",
    )
    default_thresholds: dict[str, int] = Field(
        ...,
        description="Umbrales por defecto del sistema",
    )

