"""
Schemas Pydantic v2 para Subscription.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.subscription import SubscriptionStatusEnum


class SubscriptionResponse(BaseModel):
    """Respuesta al consultar una suscripción."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    shop_id: uuid.UUID
    plan_id: uuid.UUID
    status: SubscriptionStatusEnum
    started_at: datetime
    ends_at: datetime | None
    payment_reference: str | None
