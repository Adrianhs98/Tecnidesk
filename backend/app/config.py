"""
Configuración centralizada de TecniDesk.
Lee todas las variables desde el archivo .env usando Pydantic Settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",   # Ignorar vars del .env no declaradas (ej: DATABASE_URL para psql CLI)
    )

    # Base de datos
    db_url: str

    # JWT — HS256, mínimo 64 caracteres
    jwt_secret: str
    jwt_refresh_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # Fernet — cifrado de pin_or_password
    fernet_key: str

    # bcrypt — work factor (D16). Reducir a 10 en free tier, 12 en prod con más CPU
    bcrypt_rounds: int = 10

    # Webhooks salientes
    webhook_url: str = ""
    webhook_secret: str = ""

    # Cloudflare R2
    r2_endpoint: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket_name: str = ""

    # Supabase (Storage)
    supabase_url: str = ""
    supabase_key: str = ""

    # Email Integration (Resend)
    resend_api_key: str = ""
    mail_from: str = "noreply@tecnidesk.com"
    frontend_url: str = "http://localhost:3000"

    # CORS — orígenes adicionales para desarrollo local
    # Ejemplo: "http://localhost:3000,http://localhost:5173"
    allowed_origins_dev: str = ""

    @property
    def dev_origins(self) -> list[str]:
        """Parsea la cadena de orígenes de desarrollo en una lista."""
        if not self.allowed_origins_dev:
            return []
        return [o.strip() for o in self.allowed_origins_dev.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Devuelve instancia singleton de Settings (cacheada)."""
    return Settings()

