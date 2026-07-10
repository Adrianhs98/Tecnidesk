"""
Script de entorno de Alembic.
Lee DB_URL desde .env e importa todos los modelos para autogenerate.

IMPORTANTE: Alembic usa conexión sincrónica (psycopg2).
            La app FastAPI usa asyncpg — son dos drivers distintos para el mismo host.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importar settings para leer DB_URL
from app.config import get_settings

# Importar Base y TODOS los modelos (necesario para autogenerate)
from app.models.base import Base  # noqa: F401
from app.models.plan import Plan  # noqa: F401
from app.models.shop import Shop  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.customer import Customer  # noqa: F401
from app.models.inventory import Inventory  # noqa: F401
from app.models.ticket import Ticket  # noqa: F401
from app.models.ticket_item import TicketItem  # noqa: F401
from app.models.ticket_evidence import TicketEvidence  # noqa: F401
from app.models.webhook_log import WebhookLog  # noqa: F401

# Configuración de logging de Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata de todos los modelos para autogenerate
target_metadata = Base.metadata

# Inyectar DB_URL desde settings, convirtiendo el driver a psycopg2 para Alembic sync
settings = get_settings()
sync_url = settings.db_url.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
).replace(
    "postgresql+asyncpg+ssl://", "postgresql+psycopg2://"
)
# Supabase direct connections (port 5432) require SSL
if "?" not in sync_url:
    sync_url += "?sslmode=require"
elif "sslmode" not in sync_url:
    sync_url += "&sslmode=require"
config.set_main_option("sqlalchemy.url", sync_url)


def run_migrations_offline() -> None:
    """Modo offline: genera SQL sin conexión real a la DB."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Modo online: conexión sincrónica con psycopg2."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
