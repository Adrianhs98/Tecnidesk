"""
Servicio: diagnostic_service — Búsqueda semántica vectorial de casos de diagnóstico.

Responsabilidades:
  1. Recibir un síntoma en texto libre, generar su embedding con EmbeddingService.
  2. Ejecutar una búsqueda vectorial de similitud del coseno contra `diagnostic_cases`
     usando la extensión pgvector y el índice HNSW (vector_cosine_ops).
  3. Aplicar filtro multi-tenant estricto: un shop_id solo ve sus propios casos reales
     (`real_validated`) más los casos sintéticos globales (`shop_id IS NULL`).
  4. Calcular un puntaje compuesto que priorice `real_validated` sobre `synthetic`.
  5. Registrar cada consulta en `diagnostic_query_log` para métricas de madurez.

SEGURIDAD (Multi-Tenant):
  - La cláusula WHERE SIEMPRE incluye: (shop_id = :target_shop OR shop_id IS NULL).
  - Un taller NUNCA puede ver ni recibir como resultado un caso `real_validated`
    que pertenezca a otro taller.
  - Los casos `synthetic` (shop_id IS NULL) son globales por diseño.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, text, case as sa_case, literal, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmbeddingServiceUnavailableError
from app.models.diagnostic import DiagnosticCase, DiagnosticQueryLog
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger("tecnidesk.diagnostic_service")


# ─── Configuration Constants ─────────────────────────────────────────────────

# Cosine distance threshold. pgvector's `<=>` returns distance (0 = identical,
# 2 = opposite). We reject results beyond this value as "insufficient evidence".
# A threshold of 0.45 means cosine similarity >= 0.55, which is a reasonable
# cutoff for the nomic-embed-text-v2 model on multilingual repair text.
DISTANCE_THRESHOLD: float = 0.45

# Maximum number of candidate results to return from the vector search.
MAX_RESULTS: int = 5

# Bonus applied to the composite score for `real_validated` cases.
# This makes a real case with distance 0.35 score better than a synthetic
# case with distance 0.30, because real-world validated data is inherently
# more trustworthy.
REAL_CASE_BONUS: float = 0.10


# ─── Result Dataclasses ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class RetrievedCase:
    """A single diagnostic case returned from the vector search."""

    case_id: uuid.UUID
    source_type: str              # 'synthetic' | 'real_validated'
    device_brand: str
    device_model: str
    symptom_text: str
    diagnosed_cause: str
    solution_applied: str
    repair_time_minutes: Optional[int]
    estimated_cost: Optional[Decimal]
    cosine_distance: float        # Raw pgvector <=> distance (lower = more similar)
    similarity_score: float       # 1.0 - cosine_distance (higher = more similar)
    composite_score: float        # similarity_score + source bonus (final ranking value)
    shop_id: Optional[uuid.UUID]  # NULL for synthetics, shop UUID for real cases


@dataclass
class DiagnosticSearchResult:
    """
    Complete result from a diagnostic search operation.
    Contains the ranked cases and metadata about the query.
    """

    query_text: str
    cases: list[RetrievedCase] = field(default_factory=list)
    had_sufficient_evidence: bool = True
    top_source_type: Optional[str] = None
    top_similarity_score: Optional[float] = None

    @property
    def is_empty(self) -> bool:
        return len(self.cases) == 0


# ─── Domain Exceptions ───────────────────────────────────────────────────────

class DiagnosticSearchError(Exception):
    """Generic error during diagnostic search."""


class InsufficientEvidenceError(Exception):
    """
    All retrieved cases fall below the similarity threshold.
    The caller should use the `had_sufficient_evidence = false` fallback path.
    """


# ─── Core Search Function ────────────────────────────────────────────────────

async def search_similar_cases(
    db: AsyncSession,
    shop_id: uuid.UUID,
    device_brand: str,
    device_model: str,
    symptom_text: str,
    *,
    ticket_id: Optional[uuid.UUID] = None,
    max_results: int = MAX_RESULTS,
    distance_threshold: float = DISTANCE_THRESHOLD,
) -> DiagnosticSearchResult:
    """
    Search for diagnostic cases semantically similar to the given symptom.

    Steps:
        1. Build a query string from brand/model/symptom.
        2. Generate the query embedding via EmbeddingService.
        3. Execute a pgvector cosine distance search with multi-tenant isolation.
        4. Rank results by composite score (distance + source_type bonus).
        5. Log the query to diagnostic_query_log for telemetry.

    Args:
        db:                 Active async database session.
        shop_id:            The calling tenant's shop UUID (for multi-tenant filter).
        device_brand:       Brand of the device being diagnosed (e.g. "Samsung").
        device_model:       Model of the device (e.g. "Galaxy A54 5G").
        symptom_text:       Free-text symptom description from the technician.
        ticket_id:          Optional ticket UUID to link in the query log.
        max_results:        Maximum number of cases to return (default: 5).
        distance_threshold: Cosine distance cutoff — cases beyond this are rejected.

    Returns:
        DiagnosticSearchResult with ranked cases and evidence metadata.

    Raises:
        EmbeddingServiceUnavailableError: If Ollama/Tailscale is unreachable.
        DiagnosticSearchError: For unexpected database or processing errors.
    """
    # ── Step 1: Build the query text ──────────────────────────────────────
    query_text = EmbeddingService.format_query_text(device_brand, device_model, symptom_text)
    logger.info("Diagnostic search for shop=%s | query='%s'", shop_id, query_text[:120])

    # ── Step 2: Generate the query embedding ──────────────────────────────
    try:
        query_embedding = await EmbeddingService.get_embedding(query_text, is_query=True)
    except EmbeddingServiceUnavailableError:
        logger.error("Embedding service unavailable during diagnostic search.")
        raise
    except Exception as exc:
        logger.error("Unexpected error generating embedding: %s", exc, exc_info=True)
        raise DiagnosticSearchError(f"Failed to generate query embedding: {exc}") from exc

    # ── Step 3: Build the multi-tenant vector search query ────────────────
    #
    # SQL equivalent:
    #   SELECT *, (embedding <=> :query_vector) AS cosine_distance
    #   FROM   diagnostic_cases
    #   WHERE  (shop_id = :shop_id OR shop_id IS NULL)
    #     AND  (embedding <=> :query_vector) < :threshold
    #   ORDER BY cosine_distance ASC
    #   LIMIT  :max_results;
    #
    # The `<=>` operator is the cosine distance operator from pgvector.
    # Lower values = more similar. The HNSW index accelerates this.

    cosine_distance_expr = DiagnosticCase.embedding.cosine_distance(query_embedding)

    # Multi-tenant isolation: own real cases + global synthetics only
    tenant_filter = or_(
        DiagnosticCase.shop_id == shop_id,
        DiagnosticCase.shop_id.is_(None),
    )

    stmt = (
        select(
            DiagnosticCase,
            cosine_distance_expr.label("cosine_distance"),
        )
        .where(
            and_(
                tenant_filter,
                cosine_distance_expr < distance_threshold,
            )
        )
        .order_by(cosine_distance_expr.asc())
        .limit(max_results)
    )

    try:
        result = await db.execute(stmt)
        rows = result.all()
    except Exception as exc:
        logger.error("Database error during vector search: %s", exc, exc_info=True)
        raise DiagnosticSearchError(f"Vector search query failed: {exc}") from exc

    # ── Step 4: Build ranked results with composite scoring ───────────────
    retrieved_cases: list[RetrievedCase] = []

    for row in rows:
        case_obj: DiagnosticCase = row[0]
        raw_distance: float = float(row[1])

        similarity = 1.0 - raw_distance
        bonus = REAL_CASE_BONUS if case_obj.source_type == "real_validated" else 0.0
        composite = similarity + bonus

        retrieved_cases.append(
            RetrievedCase(
                case_id=case_obj.id,
                source_type=case_obj.source_type,
                device_brand=case_obj.device_brand,
                device_model=case_obj.device_model,
                symptom_text=case_obj.symptom_text,
                diagnosed_cause=case_obj.diagnosed_cause,
                solution_applied=case_obj.solution_applied,
                repair_time_minutes=case_obj.repair_time_minutes,
                estimated_cost=case_obj.estimated_cost,
                cosine_distance=raw_distance,
                similarity_score=similarity,
                composite_score=composite,
                shop_id=case_obj.shop_id,
            )
        )

    # Re-sort by composite score descending (real_validated floats to the top)
    retrieved_cases.sort(key=lambda c: c.composite_score, reverse=True)

    # ── Step 5: Determine evidence sufficiency ────────────────────────────
    had_sufficient = len(retrieved_cases) > 0

    search_result = DiagnosticSearchResult(
        query_text=query_text,
        cases=retrieved_cases,
        had_sufficient_evidence=had_sufficient,
        top_source_type=retrieved_cases[0].source_type if had_sufficient else None,
        top_similarity_score=retrieved_cases[0].similarity_score if had_sufficient else None,
    )

    # ── Step 6: Log the query for telemetry ───────────────────────────────
    await _log_diagnostic_query(
        db=db,
        shop_id=shop_id,
        ticket_id=ticket_id,
        query_text=query_text,
        result=search_result,
    )

    logger.info(
        "Search complete: %d results | sufficient=%s | top_score=%.4f | top_source=%s",
        len(retrieved_cases),
        had_sufficient,
        search_result.top_similarity_score or 0.0,
        search_result.top_source_type or "none",
    )

    return search_result


# ─── Telemetry Logging ────────────────────────────────────────────────────────

async def _log_diagnostic_query(
    db: AsyncSession,
    shop_id: uuid.UUID,
    ticket_id: Optional[uuid.UUID],
    query_text: str,
    result: DiagnosticSearchResult,
) -> None:
    """
    Persist a query record to diagnostic_query_log for maturity metrics.

    Captures the top result's case_id, source_type, similarity score, and
    whether the search produced sufficient evidence for reasoning.
    This never raises — failures are logged and swallowed.
    """
    try:
        top_case = result.cases[0] if result.cases else None

        log_entry = DiagnosticQueryLog(
            shop_id=shop_id,
            ticket_id=ticket_id,
            query_text=query_text,
            top_case_id=top_case.case_id if top_case else None,
            source_type_used=top_case.source_type if top_case else None,
            similarity_score=top_case.similarity_score if top_case else None,
            had_sufficient_evidence=result.had_sufficient_evidence,
        )
        db.add(log_entry)
        # Flush (but don't commit — the caller's session controls the transaction).
        await db.flush()
        logger.debug("Diagnostic query logged: shop=%s, sufficient=%s", shop_id, result.had_sufficient_evidence)

    except Exception as exc:
        # Telemetry must never break the main search flow.
        logger.warning("Failed to log diagnostic query (non-fatal): %s", exc)
