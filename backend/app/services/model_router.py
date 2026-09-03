"""Deterministic, observable routing for Ohm's Gemini calls."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from app.config import get_settings


@dataclass(frozen=True)
class ModelRoute:
    model: str
    route: str
    max_output_tokens: int


class ModelRouter:
    """Avoid an extra LLM call by classifying request complexity locally."""
    REASONING_TERMS = (
        "corto", "short", "pmic", "cpu", "baseband", "reball", "esquema",
        "schematic", "microsoldadura", "consumo", "no resuelve", "sigue igual",
        "varias veces", "ya probé", "ya probe", "complejo", "intermitente",
    )

    @classmethod
    def select(cls, message: str, *, ticket_context: bool, prior_messages: Iterable[object] = ()) -> ModelRoute:
        settings = get_settings()
        normalized = re.sub(r"\s+", " ", message.lower()).strip()
        previous = [re.sub(r"\s+", " ", str(getattr(item, "content", "")).lower()).strip()
                    for item in prior_messages if getattr(item, "role", None) == "technician"]
        needs_reasoning = ticket_context and (
            len(normalized) > 280 or normalized in previous or any(term in normalized for term in cls.REASONING_TERMS)
        )
        if needs_reasoning:
            return ModelRoute(settings.gemini_reasoning_model, "reasoning", settings.gemini_reasoning_max_output_tokens)
        return ModelRoute(settings.gemini_fast_model, "fast", settings.gemini_fast_max_output_tokens)
