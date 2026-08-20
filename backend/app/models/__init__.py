"""
Paquete de modelos SQLAlchemy.
IMPORTANTE: Importar TODOS los modelos para que Alembic los detecte.
"""
from app.models.base import Base

# Importar todos los modelos en orden de dependencias
from app.models.plan import Plan
from app.models.shop import Shop
from app.models.subscription import Subscription
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.technician import Technician
from app.models.ticket import Ticket
from app.models.ticket_item import TicketItem
from app.models.webhook_log import WebhookLog
from app.models.ticket_evidence import TicketEvidence
from app.models.diagnostic import (
    DiagnosticCase,
    DiagnosticConversation,
    DiagnosticMessage,
    DiagnosticQueryLog,
)

__all__ = [
    "Base",
    "Plan",
    "Shop",
    "Subscription",
    "User",
    "RefreshToken",
    "Customer",
    "Inventory",
    "Technician",
    "Ticket",
    "TicketItem",
    "WebhookLog",
    "TicketEvidence",
    "DiagnosticCase",
    "DiagnosticConversation",
    "DiagnosticMessage",
    "DiagnosticQueryLog",
]
