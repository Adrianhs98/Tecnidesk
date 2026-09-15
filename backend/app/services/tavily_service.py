"""
Service: tavily_service — Pre-fetch web search for technical reasoning in Ohm.

Architecture:
1. Calls the Tavily REST API (https://api.tavily.com/search) directly using httpx.AsyncClient.
2. Strictly bounds execution time with a short timeout (default 2.5s).
3. Fail-open contract: returns an empty list on any error, timeout, or missing API key
   without interrupting or crashing the diagnostic assistant.
4. Returns curated web context: title, url, and snippet content.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


async def search_technical_web(
    query: str,
    device_context: str = "",
    max_results: int = 3,
    timeout_seconds: Optional[float] = None,
) -> list[dict[str, str]]:
    """
    Performs a technical web search using the Tavily REST API.

    Args:
        query: Technician query or issue description.
        device_context: Optional device context (brand, model, fault) to enrich the search.
        max_results: Maximum number of search results to return (default: 3).
        timeout_seconds: Timeout for the HTTP request (defaults to settings.tavily_timeout_seconds).

    Returns:
        A list of dicts with keys 'title', 'url', and 'content', or [] if failed/disabled.
    """
    settings = get_settings()

    if not settings.tavily_api_key:
        logger.info("Tavily search skipped: TAVILY_API_KEY is not configured.")
        return []

    clean_query = query.strip()
    if not clean_query:
        return []

    # Enrich query with device context if not already contained
    enriched_query = clean_query
    if device_context and device_context.lower() not in clean_query.lower():
        enriched_query = f"{device_context} {clean_query}".strip()

    effective_timeout = timeout_seconds if timeout_seconds is not None else settings.tavily_timeout_seconds
    start_time = time.perf_counter()

    payload: dict[str, Any] = {
        "api_key": settings.tavily_api_key,
        "query": enriched_query,
        "search_depth": "basic",
        "include_answer": False,
        "max_results": max_results,
    }

    try:
        async with httpx.AsyncClient(timeout=effective_timeout) as client:
            response = await client.post(
                TAVILY_SEARCH_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        raw_results = data.get("results", [])

        curated_results: list[dict[str, str]] = []
        for item in raw_results:
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            content = (item.get("content") or "").strip()
            if title and url:
                curated_results.append({
                    "title": title,
                    "url": url,
                    "content": content,
                })

        logger.info(
            f"Tavily search completed in {duration_ms:.1f}ms with {len(curated_results)} results.",
            extra={
                "event": "tavily_search_success",
                "query": enriched_query,
                "results_count": len(curated_results),
                "duration_ms": duration_ms,
            },
        )
        return curated_results

    except httpx.TimeoutException as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.warning(
            f"Tavily search timed out after {duration_ms:.1f}ms for query '{enriched_query}'. Fail-open.",
            extra={
                "event": "tavily_search_timeout",
                "query": enriched_query,
                "timeout_limit": effective_timeout,
                "duration_ms": duration_ms,
            },
        )
        return []

    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.warning(
            f"Tavily search failed after {duration_ms:.1f}ms: {exc.__class__.__name__}({exc}). Fail-open.",
            extra={
                "event": "tavily_search_error",
                "query": enriched_query,
                "error": str(exc),
                "error_type": exc.__class__.__name__,
                "duration_ms": duration_ms,
            },
        )
        return []
