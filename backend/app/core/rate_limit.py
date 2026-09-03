"""
Rate limiting global — módulo separado para evitar importaciones circulares.

El `limiter` se instancia aquí y se importa tanto en main.py como en los routers
que necesiten aplicar límites (ej. /auth/login).
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import jwt

from app.config import get_settings


def get_user_rate_limit_key(request: Request) -> str:
    """
    Determina la clave de rate limiting para un usuario autenticado o cliente:
      1. Si `request.state.user_id` fue inyectado por get_current_user -> "user:{user_id}".
      2. Fallback: extraer token Bearer JWT del header Authorization -> "user:{sub}".
      3. Fallback final: IP remota del cliente (get_remote_address).
    """
    # 1. request.state.user_id
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # 2. Authorization Bearer header JWT fallback
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        try:
            settings = get_settings()
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
                options={"verify_exp": False},
            )
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass

    # 3. Remote address
    return get_remote_address(request)


# Instancia singleton del rate limiter
limiter = Limiter(key_func=get_remote_address)
