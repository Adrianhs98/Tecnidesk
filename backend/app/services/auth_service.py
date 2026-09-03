"""
Servicio: auth_service — Lógica de autenticación.

Responsabilidades:
  - Verificar credenciales (email + password bcrypt).
  - Emitir par de tokens (access + refresh).
  - Persistir refresh token como SHA-256 hash en refresh_tokens (D9).
  - Rotación: al renovar, revocar el token viejo, emitir uno nuevo.
  - Logout: revocar el refresh token actual.

NEVER guardamos el refresh token en claro — solo token_hash (SHA-256).
"""
import re
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_random_password,
    hash_password,
    hash_refresh_token,
    verify_password,
    verify_refresh_token,
)
from app.models.refresh_token import RefreshToken
from app.models.shop import Shop
from app.models.user import User, UserRoleEnum
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.services.email_service import send_password_reset_email

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _slugify(text: str) -> str:
    """Convierte un nombre legible en un slug válido para subdominio."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)[:30]


# ═══════════════════════════════════════════════════════════════════════════════
# Login
# ═══════════════════════════════════════════════════════════════════════════════

async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    """
    Verifica email + contraseña y devuelve el User ORM si son correctos.

    Raises:
        ValueError: si el email no existe, la contraseña es incorrecta,
                    o el usuario está inactivo.
    """
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    # Tiempo constante para evitar user-enumeration timing attacks
    # Si el usuario no existe, usamos un hash ficticio para forzar el cálculo de bcrypt
    dummy_hash = "$2b$10$uq4b054ba20e8344864eb8abbae0529d6bf2412b"
    pwd_hash = user.password_hash if user else dummy_hash
    password_ok = verify_password(password, pwd_hash)

    if user is None or not password_ok:
        raise ValueError("Credenciales incorrectas.")

    if not user.is_active:
        raise ValueError("Cuenta desactivada. Contacta al administrador.")

    return user


async def create_token_pair(
    db: AsyncSession,
    user: User,
) -> tuple[str, str]:
    """
    Crea un par (access_token, refresh_token) y persiste el hash del refresh.

    Pasos:
      1. Crear JWT de acceso (60 min).
      2. Crear JWT de refresh (7 días).
      3. Hashear refresh con SHA-256.
      4. Persistir RefreshToken en DB.
      5. Flush — commit lo gestiona get_db().

    Returns:
        (access_token_jwt, refresh_token_jwt)
    """
    now = datetime.now(timezone.utc)

    access_token = create_access_token(
        user_id=str(user.id),
        shop_id=str(user.shop_id),
        role=user.role.value,
    )
    refresh_token = create_refresh_token(
        user_id=str(user.id),
        shop_id=str(user.shop_id),
    )

    # Persiste el hash — NUNCA el token en claro (D9)
    from app.config import get_settings
    settings = get_settings()
    expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    token_record = RefreshToken(
        user_id=user.id,
        shop_id=user.shop_id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=expires_at,
        created_at=now,
    )
    db.add(token_record)
    await db.flush()

    return access_token, refresh_token


# ═══════════════════════════════════════════════════════════════════════════════
# Refresh — rotación de token (single-use)
# ═══════════════════════════════════════════════════════════════════════════════

async def rotate_refresh_token(
    db: AsyncSession,
    raw_refresh_token: str,
) -> tuple[str, str]:
    """
    Valida el refresh token, lo revoca y emite un nuevo par.

    Flujo (D9 — single-use rotation):
      1. Verificar firma JWT (JWTError si inválido/expirado).
      2. Buscar hash en DB.
      3. Verificar que no esté revocado y no haya expirado.
      4. Revocar token viejo (revoked_at = now).
      5. Emitir nuevo par y persistir en DB.

    Raises:
        ValueError: token no encontrado, revocado o expirado en DB.
        JWTError:   firma JWT inválida o expirada.
    """
    # Paso 1: Verificar firma
    try:
        payload = verify_refresh_token(raw_refresh_token)
    except JWTError as exc:
        raise ValueError("Refresh token inválido o expirado.") from exc

    user_id = payload["sub"]
    token_hash = hash_refresh_token(raw_refresh_token)

    # Paso 2-3: Buscar y validar en DB
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if token_record is None or not token_record.is_valid:
        raise ValueError("Refresh token revocado, expirado o no encontrado.")

    # Paso 4: Revocar token viejo
    token_record.revoked_at = datetime.now(timezone.utc)

    # Paso 5: Obtener usuario y emitir par nuevo
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise ValueError("Usuario no encontrado o inactivo.")

    access_token, new_refresh_token = await create_token_pair(db, user)
    return access_token, new_refresh_token, user


# ═══════════════════════════════════════════════════════════════════════════════
# Logout — revocar token actual
# ═══════════════════════════════════════════════════════════════════════════════

async def revoke_refresh_token(
    db: AsyncSession,
    raw_refresh_token: str,
) -> None:
    """
    Revoca el refresh token proporcionado (logout).

    Si el token no existe o ya fue revocado, no lanza error (idempotente).
    Si la firma es inválida, lanza ValueError.

    Raises:
        ValueError: firma JWT inválida.
    """
    try:
        verify_refresh_token(raw_refresh_token)
    except JWTError as exc:
        raise ValueError("Refresh token inválido.") from exc

    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if token_record is not None and token_record.revoked_at is None:
        token_record.revoked_at = datetime.now(timezone.utc)
        await db.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# Registro — crear taller + usuario admin
# ═══════════════════════════════════════════════════════════════════════════════

async def register_user(
    db: AsyncSession,
    payload: RegisterRequest,
) -> RegisterResponse:
    """
    Registra un nuevo taller y su usuario administrador.

    Flujo:
      1. Verificar que el email no exista en la BD.
      2. Crear el registro Shop con datos derivados del payload.
      3. Generar una contraseña aleatoria segura.
      4. Hashear la contraseña con bcrypt.
      5. Crear el User con role=admin vinculado al shop.
      6. Flush (commit lo gestiona get_db).

    Returns:
        RegisterResponse: Datos del taller y la contraseña autogenerada temporal
        que se devuelve UNA SOLA VEZ en la respuesta para el admin.

    Raises:
        ValueError: si el email ya está registrado.
    """
    # 1. Verificar email único
    existing = await db.execute(
        select(User).where(User.email == str(payload.email))
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("El email ya está registrado.")

    now = datetime.now(timezone.utc)

    # 2. Crear Shop
    subdomain = _slugify(payload.shop_name)
    # Garantizar unicidad del subdominio añadiendo sufijo si ya existe
    base_subdomain = subdomain
    counter = 1
    while True:
        dup = await db.execute(
            select(Shop).where(Shop.subdomain == subdomain)
        )
        if dup.scalar_one_or_none() is None:
            break
        subdomain = f"{base_subdomain}-{counter}"[:30]
        counter += 1

    shop = Shop(
        business_name=payload.shop_name,
        owner_name=payload.shop_name,
        subdomain=subdomain,
        contact_email=str(payload.email),
        contact_whatsapp=payload.contact_whatsapp.strip(),
        created_at=now,
    )
    db.add(shop)
    await db.flush()  # Genera shop.id

    # 3-4. Generar y hashear contraseña
    plain_password = generate_random_password(length=12)
    hashed = hash_password(plain_password)

    # 5. Crear User admin
    user = User(
        shop_id=shop.id,
        role=UserRoleEnum.admin,
        full_name=payload.shop_name,
        email=str(payload.email),
        password_hash=hashed,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # Genera user.id

    # 6. Construir respuesta
    response = RegisterResponse(
        user_id=str(user.id),
        shop_id=str(shop.id),
        shop_name=shop.business_name,
        message="Taller y usuario creados exitosamente.",
        generated_password=plain_password,
    )

    # 7. Email de bienvenida con credenciales (fire-and-forget)
    try:
        import resend as _resend  # noqa: PLC0415
        from app.config import get_settings  # noqa: PLC0415
        _settings = get_settings()
        if _settings.resend_api_key:
            _resend.api_key = _settings.resend_api_key
            login_url = f"{_settings.frontend_url.rstrip('/')}/login"
            html_body = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        max-width: 600px; margin: 0 auto; padding: 24px; background: #ffffff;
                        border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <h1 style="color: #0070f3; margin: 0 0 8px;">¡Bienvenido a TecniDesk!</h1>
                <p style="color: #555; font-size: 15px;">Tu taller <strong>{payload.shop_name}</strong> ha sido registrado exitosamente.</p>
                <table style="width:100%; border-collapse:collapse; margin: 20px 0; font-size:15px;">
                    <tr><td style="padding:8px; color:#777;">Email</td>
                        <td style="padding:8px; font-weight:bold;">{payload.email}</td></tr>
                    <tr style="background:#f9f9f9;"><td style="padding:8px; color:#777;">Contraseña temporal</td>
                        <td style="padding:8px; font-family:monospace; font-weight:bold; font-size:17px;"
                        >{plain_password}</td></tr>
                </table>
                <p style="color:#e53e3e; font-size:13px;">⚠️ Guarda esta contraseña ahora — no se volverá a mostrar.</p>
                <div style="text-align:center; margin:28px 0;">
                    <a href="{login_url}"
                       style="background:#0070f3; color:#fff; text-decoration:none;
                              padding:13px 32px; border-radius:6px; font-weight:bold;
                              font-size:15px; display:inline-block;">Ir al Panel de Control</a>
                </div>
                <p style="color:#999; font-size:12px; text-align:center;">TecniDesk — Sistema de gestión para talleres de reparación</p>
            </div>
            """
            _resend.Emails.send({
                "from": _settings.mail_from,
                "to": str(payload.email),
                "subject": f"Bienvenido a TecniDesk — credenciales de acceso | {payload.shop_name}",
                "html": html_body,
            })
    except Exception as exc:  # noqa: BLE001
        # El email de bienvenida nunca debe tumbar el registro
        print(f"⚠️  Email de bienvenida no enviado a {payload.email}: {exc}")

    return response


# ═══════════════════════════════════════════════════════════════════════════════
# Recuperación de contraseña (Forgot / Reset Password)
# ═══════════════════════════════════════════════════════════════════════════════

async def request_password_reset(db: AsyncSession, email: str) -> None:
    """Busca el usuario y le envía un email con un link de recuperación."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return  # Silently fail for security (no user enumeration)

    token = str(uuid.uuid4())
    user.reset_password_token = token
    user.reset_password_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.flush()

    from app.config import get_settings
    settings = get_settings()
    frontend_url = settings.frontend_url.rstrip("/")
    reset_link = f"{frontend_url}/reset-password?token={token}"
    
    await send_password_reset_email(to_email=email, reset_link=reset_link)


async def confirm_password_reset(db: AsyncSession, token: str, new_password: str) -> None:
    """Valida el token y actualiza la contraseña."""
    result = await db.execute(select(User).where(User.reset_password_token == token))
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("Token inválido o ha expirado.")
        
    now = datetime.now(timezone.utc)
    if not user.reset_password_expires_at or user.reset_password_expires_at < now:
        raise ValueError("El token ha expirado. Solicita uno nuevo.")
        
    user.password_hash = hash_password(new_password)
    user.reset_password_token = None
    user.reset_password_expires_at = None
    await db.flush()
