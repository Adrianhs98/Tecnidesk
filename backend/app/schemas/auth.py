"""
Schemas de Autenticación — Fase 2.1

LoginRequest    : body de POST /auth/login
TokenResponse   : respuesta de login y refresh (access + refresh tokens)
"""
import uuid
from pydantic import BaseModel, EmailStr, Field


class TechnicianCreate(BaseModel):
    """
    DEPRECATED: Usar TechnicianCreate de app/schemas/technician.py
    Mantenido temporalmente por compatibilidad.
    """
    shop_id: uuid.UUID = Field(..., description="ID del taller al que pertenece el técnico")
    full_name: str = Field(..., description="Nombre completo del técnico")
    email: EmailStr = Field(..., description="Email del técnico, será su usuario para login")


class LoginRequest(BaseModel):
    """Body de POST /auth/login."""

    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, description="Contraseña en texto plano")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "admin@mirepar.technidesk.com",
                    "password": "S3cur3P@ss!",
                }
            ]
        }
    }


class TokenResponse(BaseModel):
    """Respuesta de login y refresh con par de tokens JWT."""

    access_token: str = Field(..., description="JWT de acceso (60 min)")
    refresh_token: str = Field(..., description="JWT de refresh (7 días) — rotar en cada uso")
    token_type: str = Field(default="bearer")
    shop_name: str | None = Field(default=None, description="Nombre del local comercial")
    role: str | None = Field(default=None, description="Rol del usuario (admin, technician)")
    user_full_name: str | None = Field(default=None, description="Nombre completo del usuario")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "role": "technician",
                    "user_full_name": "Carlos Técnico",
                }
            ]
        }
    }


class RefreshRequest(BaseModel):
    """Body de POST /auth/refresh."""

    refresh_token: str = Field(..., description="JWT de refresh emitido en login o refresh previo")


class LogoutRequest(BaseModel):
    """Body de POST /auth/logout."""

    refresh_token: str = Field(..., description="JWT de refresh a revocar")


class RegisterRequest(BaseModel):
    """Body de registro de un nuevo taller y administrador."""

    email: EmailStr = Field(..., description="Email del usuario administrador del taller")
    shop_name: str = Field(..., min_length=2, max_length=100, description="Nombre del taller")
    contact_whatsapp: str = Field(
        ...,
        min_length=10,
        max_length=20,
        pattern=r"^\d+$",
        description="WhatsApp de contacto del taller en formato internacional sin '+'. Ej: 593991234567",
    )


class RegisterResponse(BaseModel):
    """Respuesta de registro exitoso."""

    user_id: str = Field(..., description="ID del usuario creado")
    shop_id: str = Field(..., description="ID del taller creado")
    shop_name: str = Field(..., description="Nombre del taller")
    message: str = Field(..., description="Mensaje indicando el éxito de la operación")
    generated_password: str = Field(
        ...,
        description="Contraseña temporal generada automáticamente. "
                    "Muéstrala al usuario UNA Única VEZ — no se puede recuperar después.",
    )


class PasswordResetRequest(BaseModel):
    """Body para solicitar el reset de contraseña."""
    email: EmailStr = Field(..., description="Email del usuario que solicita el reset")


class PasswordResetConfirm(BaseModel):
    """Body para confirmar el reset de contraseña con token."""
    token: str = Field(..., description="Token enviado al correo")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña, min 8 caracteres")

