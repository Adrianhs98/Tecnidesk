"""
Servicio de cifrado Fernet para campos sensibles.

PROPÓSITO: Cifrar pin_or_password antes de persistir en la base de datos.
           Solo desencriptar en servicios internos autorizados.

SEGURIDAD:
  - Usa FERNET_KEY desde app/config.py (variable de entorno).
  - Fernet garantiza cifrado simétrico autenticado (AES-128-CBC + HMAC-SHA256).
  - Si el valor es None o vacío, las funciones retornan None sin error.
"""
from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """
    Devuelve la instancia singleton de Fernet.
    Inicialización lazy para evitar errores en imports sin .env configurado.
    """
    global _fernet
    if _fernet is None:
        settings = get_settings()
        _fernet = Fernet(settings.fernet_key.encode())
    return _fernet


def encrypt_pin(plain_text: str | None) -> str | None:
    """
    Cifra el texto con Fernet y devuelve el token como string UTF-8.

    Args:
        plain_text: PIN o contraseña en texto plano. None/vacío retorna None.

    Returns:
        Token Fernet cifrado como string, o None si el input es vacío.
    """
    if not plain_text:
        return None
    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_pin(encrypted_token: str | None) -> str | None:
    """
    Desencripta un token Fernet y devuelve el texto original.

    ADVERTENCIA: Llamar ÚNICAMENTE desde servicios internos autorizados.
                 NUNCA exponer el resultado en un schema público de API.

    Args:
        encrypted_token: Token Fernet como string. None/vacío retorna None.

    Returns:
        Texto plano desencriptado, o None si el token es vacío.

    Raises:
        InvalidToken: Si el token es inválido o fue cifrado con otra clave.
    """
    if not encrypted_token:
        return None
    fernet = _get_fernet()
    try:
        decrypted_bytes = fernet.decrypt(encrypted_token.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken as exc:
        raise InvalidToken(
            "No se pudo desencriptar pin_or_password. "
            "Verifica que FERNET_KEY sea la misma usada al cifrar."
        ) from exc
