"""Schemas for the Admin Assistant (Ohm) shop-level conversational interface."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class AdminAssistantQueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="Natural language message or shortcut text from administrator.")

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("El mensaje no puede estar vacío.")
        return trimmed


class AdminAssistantQueryResponse(BaseModel):
    reply: str = Field(..., description="Natural language response synthesized by Ohm.")
    intent: Optional[str] = Field(None, description="Matched intent from closed catalog or None if unclassified.")
    data: Optional[Dict[str, Any]] = Field(None, description="Structured metrics associated with the query, if applicable.")
