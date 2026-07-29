import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ClientResponse(BaseModel):
    id: uuid.UUID
    shop_id: uuid.UUID
    full_name: str
    phone_number: str
    email: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
