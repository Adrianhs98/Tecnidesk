"""
Router: /auth — Autenticación de usuarios (Fase 2.1)

Endpoints:
  POST /auth/login    — Credenciales → par de tokens JWT (rate limit: 5/min/IP)
  POST /auth/refresh  — Rota refresh token (single-use / D9)
  POST /auth/logout   — Revoca refresh token actual

Decisión D9:  refresh tokens stateful (tabla refresh_tokens, hash SHA-256).
Riesgo 4/5:  rate limiting 5 req/min/IP en /login vía slowapi.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.rate_limit import limiter
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.services.auth_service import (
    authenticate_user,
    create_token_pair,
    register_user,
    revoke_refresh_token,
    rotate_refresh_token,
    request_password_reset,
    confirm_password_reset,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── POST /auth/login ─────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description=(
        "Autentica con email y contraseña. Devuelve access_token (60 min) y "
        "refresh_token (7 días). Rate limit: **5 intentos/min por IP** (Riesgo 4)."
    ),
)
@limiter.limit("5/minute")
async def login(
    request: Request,               # requerido por slowapi para extraer IP
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    POST /auth/login
    Smoke test: ST-08.

    Errores posibles:
      401: credenciales incorrectas o cuenta inactiva.
      429: límite de rate excedido (slowapi).
    """
    try:
        user = await authenticate_user(db, str(payload.email), payload.password)
        access_token, refresh_token = await create_token_pair(db, user)
        
        # Obtener nombre del local para el frontend
        from sqlalchemy import select
        from app.models.shop import Shop
        shop_res = await db.execute(select(Shop).where(Shop.id == user.shop_id))
        shop = shop_res.scalar_one_or_none()
        shop_name = shop.business_name if shop else None
        
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        shop_name=shop_name,
    )


# ─── POST /auth/refresh ───────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar tokens",
    description=(
        "Recibe el refresh_token actual, lo revoca e irradia un nuevo par. "
        "Cada token solo puede usarse una vez (single-use rotation — D9)."
    ),
)
async def refresh_tokens(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """POST /auth/refresh — Smoke test: ST-09."""
    try:
        access_token, new_refresh = await rotate_refresh_token(db, payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
    )


# ─── POST /auth/logout ────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
    description=(
        "Revoca el refresh_token actual. "
        "El access_token seguirá siendo válido hasta su expiración (60 min). "
        "Para invalidación inmediata de access tokens usar una blacklist — Paso 4."
    ),
)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """POST /auth/logout — Smoke test: ST-10."""
    try:
        await revoke_refresh_token(db, payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ─── POST /auth/register ──────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar taller y usuario admin",
    description=(
        "Crea un nuevo taller y su usuario administrador. "
        "Genera una contraseña aleatoria segura que se devuelve UNA SOLA VEZ "
        "en la respuesta para entregarla al técnico/admin."
    ),
)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /auth/register

    Errores posibles:
      400: email ya registrado o subdominio duplicado.
    """
    try:
        response = await register_user(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return response


# ─── POST /auth/forgot-password ───────────────────────────────────────────────

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña",
    description="Si el email existe, se enviará un enlace de recuperación."
)
async def forgot_password(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    await request_password_reset(db, str(payload.email))
    return {"message": "Si el email existe recibirás instrucciones en tu correo."}


# ─── POST /auth/reset-password ────────────────────────────────────────────────

@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Confirmar nueva contraseña",
    description="Utiliza el token proporcionado por correo para guardar la nueva contraseña."
)
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    try:
        await confirm_password_reset(db, payload.token, payload.new_password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        ) from exc
        
    return {"message": "Contraseña actualizada correctamente."}
