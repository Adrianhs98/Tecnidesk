"""
Service: llm_gateway — Centralized LLM execution gateway with automatic OmniRoute fallback.

Architecture:
1. Primary call: Direct Google Gemini SDK (google-genai).
2. Fallback: OmniRoute via AsyncOpenAI (OpenAI-compatible) when primary fails.
3. Explicit failure: If tier == "reasoning" and no reasoning combo is configured,
   fails explicitly and re-raises the primary exception to avoid silent degradation.
4. Call-site independence: When all providers fail, raises an exception so each
   service can apply its own degradation policy (e.g., fail-open in safety guard,
   user error message in diagnostic router, etc.).
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Literal, Optional

from google import genai
from google.genai import types
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

LLMTier = Literal["fast", "reasoning"]


@dataclass(frozen=True)
class LLMResult:
    """Result container for LLM generation."""
    text: str
    provider: str  # "gemini" | "omniroute"
    model_used: str
    is_fallback: bool
    latency_ms: float

    def __str__(self) -> str:
        return self.text


class LLMGatewayError(Exception):
    """Raised when all available LLM providers (primary and fallback) have failed."""
    def __init__(
        self,
        message: str,
        *,
        primary_error: Exception,
        fallback_error: Optional[Exception] = None,
        tier: str = "fast",
    ):
        super().__init__(message)
        self.primary_error = primary_error
        self.fallback_error = fallback_error
        self.tier = tier


async def generate_llm_content(
    prompt: str,
    tier: LLMTier = "fast",
    *,
    temperature: float = 0.0,
    max_output_tokens: Optional[int] = None,
    timeout_seconds: Optional[float] = None,
    response_mime_type: Optional[str] = None,
    system_instruction: Optional[str] = None,
    client: Optional[genai.Client] = None,
) -> LLMResult:
    """
    Executes an LLM request against Gemini directly, falling back to OmniRoute
    if Gemini fails and a valid fallback combo is configured for the tier.

    Parameters:
        prompt: User message / prompt text.
        tier: "fast" (mapped to gemini-3.5-flash-lite / ohm-fast) or
              "reasoning" (gemini-3.6-flash / omniroute_reasoning_combo).
        temperature: Sampling temperature (default 0.0).
        max_output_tokens: Token cap (defaults to tier setting if None).
        timeout_seconds: Timeout override in seconds (defaults to gemini_primary_timeout_seconds if None).
        response_mime_type: e.g. "application/json" for structured output.
        system_instruction: Optional system instruction prompt.
        client: Optional injected google-genai Client (useful for unit tests).
    """
    settings = get_settings()

    # Determine primary model & token limits from tier
    if tier == "reasoning":
        primary_model = settings.gemini_reasoning_model
        resolved_max_tokens = max_output_tokens or settings.gemini_reasoning_max_output_tokens
    else:
        primary_model = settings.gemini_fast_model
        resolved_max_tokens = max_output_tokens or settings.gemini_fast_max_output_tokens

    resolved_timeout = timeout_seconds or settings.gemini_primary_timeout_seconds

    # 1. Primary Attempt: Google Gemini direct
    start_time = time.perf_counter()
    try:
        active_client = client or genai.Client(api_key=settings.gemini_api_key)
        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": resolved_max_tokens,
        }
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        response = await asyncio.wait_for(
            active_client.aio.models.generate_content(
                model=primary_model,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            ),
            timeout=resolved_timeout,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        if getattr(response, "candidates", None):
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            fr_str = str(finish_reason).upper()
            if "MAX_TOKENS" in fr_str:
                logger.warning(
                    f"Gemini output truncated: finish_reason={finish_reason} for tier='{tier}' "
                    f"(max_output_tokens={resolved_max_tokens}). Output may be cut off mid-sentence.",
                    extra={
                        "event": "llm_max_tokens_reached",
                        "tier": tier,
                        "model": primary_model,
                        "max_output_tokens": resolved_max_tokens,
                        "finish_reason": str(finish_reason),
                    },
                )

        return LLMResult(
            text=response.text or "",
            provider="gemini",
            model_used=primary_model,
            is_fallback=False,
            latency_ms=latency_ms,
        )
    except Exception as primary_exc:
        primary_duration_ms = (time.perf_counter() - start_time) * 1000.0
        primary_status = (
            getattr(primary_exc, "code", None)
            or getattr(primary_exc, "status_code", None)
        )
        logger.warning(
            f"Primary Gemini call failed for tier '{tier}' after {primary_duration_ms:.1f}ms: "
            f"{primary_exc.__class__.__name__}({primary_exc})",
            extra={
                "event": "llm_primary_failed",
                "tier": tier,
                "primary_model": primary_model,
                "primary_error": str(primary_exc),
                "primary_error_type": primary_exc.__class__.__name__,
                "primary_status_code": primary_status,
                "duration_ms": primary_duration_ms,
            },
        )

        # 2. Check if Fallback is possible
        fallback_combo = (
            settings.omniroute_fast_combo if tier == "fast" else settings.omniroute_reasoning_combo
        )

        if not settings.omniroute_base_url or not settings.omniroute_api_key:
            logger.info(
                f"OmniRoute fallback skipped for tier '{tier}': base_url or api_key not configured. "
                "Re-raising primary exception."
            )
            raise primary_exc

        if not fallback_combo:
            # Tier reasoning without configured combo: FAIL EXPLICITLY as per architectural decision
            logger.warning(
                f"OmniRoute fallback skipped for tier '{tier}': no combo configured. "
                "Failing explicitly to prevent hidden quality degradation."
            )
            raise primary_exc

        # 3. Fallback Attempt: OmniRoute (OpenAI-compatible)
        logger.warning(
            f"Triggering OmniRoute fallback for tier '{tier}' using combo '{fallback_combo}'",
            extra={
                "event": "llm_fallback_triggered",
                "tier": tier,
                "fallback_combo": fallback_combo,
                "primary_error": str(primary_exc),
                "primary_status_code": primary_status,
            },
        )

        fallback_start = time.perf_counter()
        try:
            openai_client = AsyncOpenAI(
                base_url=settings.omniroute_base_url,
                api_key=settings.omniroute_api_key,
                timeout=settings.omniroute_timeout_seconds,
            )

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            request_kwargs: dict[str, Any] = {
                "model": fallback_combo,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": resolved_max_tokens,
            }

            if response_mime_type == "application/json":
                request_kwargs["response_format"] = {"type": "json_object"}

            chat_completion = await openai_client.chat.completions.create(**request_kwargs)
            fallback_latency_ms = (time.perf_counter() - fallback_start) * 1000.0

            content = ""
            if chat_completion.choices and chat_completion.choices[0].message:
                choice = chat_completion.choices[0]
                content = choice.message.content or ""
                fr = getattr(choice, "finish_reason", None)
                if fr == "length":
                    logger.warning(
                        f"OmniRoute output truncated: finish_reason='length' for tier='{tier}' "
                        f"(max_tokens={resolved_max_tokens}). Output may be cut off mid-sentence.",
                        extra={
                            "event": "llm_max_tokens_reached",
                            "tier": tier,
                            "model": fallback_combo,
                            "max_output_tokens": resolved_max_tokens,
                            "finish_reason": "length",
                        },
                    )

            logger.info(
                f"OmniRoute fallback succeeded for tier '{tier}' combo '{fallback_combo}' in {fallback_latency_ms:.1f}ms",
                extra={
                    "event": "llm_fallback_succeeded",
                    "tier": tier,
                    "fallback_combo": fallback_combo,
                    "duration_ms": fallback_latency_ms,
                },
            )

            return LLMResult(
                text=content,
                provider="omniroute",
                model_used=fallback_combo,
                is_fallback=True,
                latency_ms=fallback_latency_ms,
            )
        except Exception as fallback_exc:
            fallback_duration_ms = (time.perf_counter() - fallback_start) * 1000.0
            logger.error(
                f"OmniRoute fallback also failed for tier '{tier}' after {fallback_duration_ms:.1f}ms: "
                f"{fallback_exc.__class__.__name__}({fallback_exc}). Primary error was: {primary_exc}",
                extra={
                    "event": "llm_all_providers_failed",
                    "tier": tier,
                    "fallback_combo": fallback_combo,
                    "primary_error": str(primary_exc),
                    "fallback_error": str(fallback_exc),
                    "fallback_duration_ms": fallback_duration_ms,
                },
            )
            # Raise LLMGatewayError containing both exceptions so callers can handle or inspect
            raise LLMGatewayError(
                f"Both primary Gemini and OmniRoute fallback failed for tier '{tier}': "
                f"Primary: {primary_exc} | Fallback: {fallback_exc}",
                primary_error=primary_exc,
                fallback_error=fallback_exc,
                tier=tier,
            ) from primary_exc
