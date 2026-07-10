"""
Rate limiting global — módulo separado para evitar importaciones circulares.

El `limiter` se instancia aquí y se importa tanto en main.py como en los routers
que necesiten aplicar límites (ej. /auth/login).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Instancia singleton del rate limiter
limiter = Limiter(key_func=get_remote_address)
