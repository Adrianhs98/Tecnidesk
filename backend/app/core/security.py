"""
Capa de seguridad de TecniDesk.

Responsabilidades:
  - Hash y verificación de contraseñas con bcrypt.
  - Creación y verificación de JWT (access token + refresh token).
  - Algoritmo: HS256. Work factor bcrypt: configurable (default 10).

NUNCA importar modelos ORM aquí — este módulo no debe depender de DB.
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# ─── bcrypt — work factor configurable por .env (Riesgo 4 / D16) ─────────────
_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Contraseñas
# ═══════════════════════════════════════════════════════════════════════════════

def hash_password(plain_password: str) -> str:
    """Devuelve el hash bcrypt de una contraseña en texto plano."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que plain_password coincida con su hash bcrypt."""
    return _pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════════════════════════════════════════
# JWT — Access Token (60 min)
# ═══════════════════════════════════════════════════════════════════════════════

def create_access_token(
    user_id: str,
    shop_id: str,
    role: str,
) -> str:
    """
    Crea un JWT de acceso firmado con JWT_SECRET.

    Claims incluidos:
      - sub: user_id (string)
      - shop_id: UUID del taller
      - role: "admin" | "technician"
      - exp: ahora + 60 minutos
      - type: "access"
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "shop_id": shop_id,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# ═══════════════════════════════════════════════════════════════════════════════
# JWT — Refresh Token (7 días)
# ═══════════════════════════════════════════════════════════════════════════════

def create_refresh_token(user_id: str, shop_id: str) -> str:
    """
    Crea un JWT de refresh firmado con JWT_REFRESH_SECRET.

    Claims incluidos:
      - sub: user_id
      - shop_id: UUID del taller
      - exp: ahora + 7 días
      - type: "refresh"

    IMPORTANTE: Este token se hashea antes de persistir en DB (tabla refresh_tokens).
    El hash se guarda como token_hash; el token en claro solo viaja al cliente.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    payload = {
        "sub": user_id,
        "shop_id": shop_id,
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(
        payload, settings.jwt_refresh_secret, algorithm=settings.jwt_algorithm
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Verificación de tokens
# ═══════════════════════════════════════════════════════════════════════════════

def verify_access_token(token: str) -> dict:
    """
    Decodifica y verifica un access token.

    Returns:
        Payload del JWT (sub, shop_id, role, exp, type).

    Raises:
        JWTError: Si el token es inválido, expirado o tiene type incorrecto.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise JWTError("Token de acceso inválido o expirado.") from exc

    if payload.get("type") != "access":
        raise JWTError("El token no es un access token.")

    return payload


def verify_refresh_token(token: str) -> dict:
    """
    Decodifica y verifica un refresh token.

    Returns:
        Payload del JWT (sub, shop_id, exp, type).

    Raises:
        JWTError: Si el token es inválido, expirado o tiene type incorrecto.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_refresh_secret, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise JWTError("Refresh token inválido o expirado.") from exc

    if payload.get("type") != "refresh":
        raise JWTError("El token no es un refresh token.")

    return payload


# ═══════════════════════════════════════════════════════════════════════════════
# Hash de refresh token para almacenamiento seguro en DB
# ═══════════════════════════════════════════════════════════════════════════════

import hashlib
import secrets
import string

# Alfabeto curado: ASCII imprimible sin caracteres que confunden shells ni
# editores (excluye: \, ", ', `, espacio). Cada carácter ocupa 1 byte,
# por lo que 16 caracteres = 16 bytes, muy por debajo del límite de 72 de bcrypt.
_SAFE_UPPERCASE = string.ascii_uppercase          # A-Z  (26)
_SAFE_LOWERCASE = string.ascii_lowercase          # a-z  (26)
_SAFE_DIGITS    = string.digits                   # 0-9  (10)
_SAFE_SYMBOLS   = "!@#$%^&*()_+-=[]{}|;:,.<>?"   # 25 símbolos shell-safe

_PASSWORD_ALPHABET = _SAFE_UPPERCASE + _SAFE_LOWERCASE + _SAFE_DIGITS + _SAFE_SYMBOLS


def generate_random_password(length: int = 16) -> str:
    """
    Genera una contraseña segura y aleatoria de exactamente `length` caracteres.

    Garantías:
      - Al menos 1 mayúscula, 1 minúscula, 1 dígito y 1 símbolo (complejidad NIST).
      - Cada carácter ocupa exactamente 1 byte UTF-8 → seguro para bcrypt (< 72 bytes).
      - Entropía: log2(87^16) ≈ 103 bits para length=16 (impenetrable por fuerza bruta).
      - No usa truncamiento — el string generado tiene EXACTLY `length` caracteres.

    Args:
        length: Longitud deseada (mínimo 8, por debajo del límite bcrypt de 72).
    """
    if length < 8:
        raise ValueError("La longitud mínima de la contraseña es 8 caracteres.")
    if length > 72:
        raise ValueError("La longitud máxima segura para bcrypt es 72 caracteres.")

    # Garantizar al menos un carácter de cada clase (requisito de complejidad)
    required = [
        secrets.choice(_SAFE_UPPERCASE),
        secrets.choice(_SAFE_LOWERCASE),
        secrets.choice(_SAFE_DIGITS),
        secrets.choice(_SAFE_SYMBOLS),
    ]

    # Rellenar el resto con caracteres aleatorios del alfabeto completo
    rest = [secrets.choice(_PASSWORD_ALPHABET) for _ in range(length - len(required))]

    combined = required + rest
    # Barajar con CSPRNG para evitar posiciones predecibles de los requeridos
    secrets.SystemRandom().shuffle(combined)
    return "".join(combined)





def hash_refresh_token(token: str) -> str:
    """
    Devuelve el SHA-256 hex del refresh token para almacenar en DB.

    Nunca guardamos el refresh token en claro. Si la DB se compromete,
    los tokens no son recuperables (SHA-256 es one-way).
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# Cifrado Fernet — PINs de dispositivos (D2)
# ═══════════════════════════════════════════════════════════════════════════════

from cryptography.fernet import Fernet


def encrypt_pin(plain_pin: str) -> str:
    """
    Cifra un PIN de dispositivo con Fernet (AES-128 CBC + HMAC).

    Args:
        plain_pin: PIN en texto plano (ej: "1234", "patrón123").

    Returns:
        Token Fernet cifrado (string).

    Raises:
        ValueError: si FERNET_KEY no está configurado.
    """
    if not settings.fernet_key:
        raise ValueError("FERNET_KEY no está configurado en .env")

    fernet = Fernet(settings.fernet_key.encode())
    encrypted_bytes = fernet.encrypt(plain_pin.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_pin(encrypted_pin: str) -> str:
    """
    Descifra un PIN de dispositivo previamente cifrado con encrypt_pin().

    Args:
        encrypted_pin: Token Fernet cifrado.

    Returns:
        PIN en texto plano.

    Raises:
        ValueError: si FERNET_KEY no está configurado.
        cryptography.fernet.InvalidToken: si el token es inválido.
    """
    if not settings.fernet_key:
        raise ValueError("FERNET_KEY no está configurado en .env")

    fernet = Fernet(settings.fernet_key.encode())
    decrypted_bytes = fernet.decrypt(encrypted_pin.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")
