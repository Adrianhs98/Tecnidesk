"""
Servicio de Embeddings Locales mediante Ollama y nomic-embed-text-v2-moe.
"""
from __future__ import annotations

import logging
from typing import List

import httpx

from app.config import get_settings
from app.core.exceptions import EmbeddingServiceUnavailableError

logger = logging.getLogger("tecnidesk.embedding_service")

# Constantes de configuración del modelo Nomic
MODEL_NAME = "nomic-embed-text-v2-moe:latest"
MAX_CHAR_LENGTH = 1500
QUERY_PREFIX = "search_query: "
DOCUMENT_PREFIX = "search_document: "


class EmbeddingService:
    """
    Servicio cliente para generar representaciones vectoriales densas (768 dims)
    a través del endpoint de embeddings de Ollama (local o Tailscale Funnel).
    """

    @staticmethod
    def format_query_text(brand: str, model: str, symptom: str) -> str:
        """Formatea el texto de consulta para búsqueda semántica."""
        return f"Brand: {brand.strip()} | Model: {model.strip()} | Symptom: {symptom.strip()}"

    @staticmethod
    def format_document_text(
        brand: str,
        model: str,
        symptom: str,
        cause: str,
        solution: str,
    ) -> str:
        """Formatea el texto del documento para indexación vectorial."""
        return (
            f"Brand: {brand.strip()} | Model: {model.strip()} | "
            f"Symptom: {symptom.strip()} | Cause: {cause.strip()} | "
            f"Solution: {solution.strip()}"
        )

    @classmethod
    async def get_embedding(cls, text: str, is_query: bool = False) -> List[float]:
        """
        Genera el vector de embedding para el texto dado.

        - is_query=True aplica el prefijo 'search_query: '
        - is_query=False aplica el prefijo 'search_document: '
        - Aplica truncado seguro a 1500 caracteres antes de prefijar para garantizar
          que se respeta el límite estricto de 512 tokens de contexto.
        """
        settings = get_settings()
        prefix = QUERY_PREFIX if is_query else DOCUMENT_PREFIX
        truncated_text = text[:MAX_CHAR_LENGTH]
        payload = {
            "model": MODEL_NAME,
            "input": f"{prefix}{truncated_text}",
        }

        endpoint_url = f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(endpoint_url, json=payload)
                response.raise_for_status()
                data = response.json()

                if "embeddings" not in data or not data["embeddings"]:
                    raise ValueError(f"Respuesta inesperada del servicio de embeddings: {data}")

                # Ollama /api/embed devuelve {"embeddings": [[float, ...]]}
                return data["embeddings"][0]

        except (httpx.RequestError, httpx.HTTPStatusError, ValueError, KeyError) as exc:
            logger.error(
                f"Error al contactar con el servicio de embedding en {endpoint_url}: {exc}",
                exc_info=True,
            )
            raise EmbeddingServiceUnavailableError(
                f"Local embedding service unreachable: {exc}"
            ) from exc
