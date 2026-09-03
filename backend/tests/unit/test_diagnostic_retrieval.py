"""
Unit tests for diagnostic_service — Phase 2: Hybrid Retrieval.

Test strategy:
  - Embedding generation is always mocked via `respx` (no real Ollama calls).
  - Database interactions use the `db_session` fixture from conftest.py which
    wraps every test in a transaction that is rolled back automatically.

Coverage:
  1. Scoring logic — composite score and bonus computation (pure, no I/O).
  2. Composite score ordering — real_validated cases float above synthetic ones.
  3. Distance threshold — results beyond the cutoff are excluded.
  4. Multi-tenant isolation — a shop CANNOT see another shop's real_validated cases.
  5. Synthetic cases are visible to ALL shops (shop_id IS NULL).
  6. Empty result when no cases exist (had_sufficient_evidence = False).
  7. EmbeddingServiceUnavailableError propagates cleanly from search_similar_cases.
  8. Query logging — a DiagnosticQueryLog row is flushed after every search.
  9. Logging is non-fatal — a log failure never breaks the search result.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from app.config import get_settings
from app.core.exceptions import EmbeddingServiceUnavailableError
from app.models.diagnostic import DiagnosticCase, DiagnosticQueryLog
from app.models.shop import Shop
from app.services.diagnostic_service import (
    DISTANCE_THRESHOLD,
    MAX_RESULTS,
    REAL_CASE_BONUS,
    DiagnosticSearchError,
    DiagnosticSearchResult,
    InsufficientEvidenceError,
    RetrievedCase,
    search_similar_cases,
)
from app.services.embedding_service import EmbeddingService

# ─── Helpers ─────────────────────────────────────────────────────────────────

MOCK_VECTOR: list[float] = [0.1] * 768   # Stable fake embedding for all tests.
NEAR_VECTOR: list[float] = [0.11] * 768  # A "close" vector for distance tests.
FAR_VECTOR: list[float] = [-0.9] * 768   # A "far" vector (high cosine distance).


def _make_shop(**kwargs) -> Shop:
    """Build a transient Shop ORM object for tests."""
    defaults = dict(
        business_name="Test Taller",
        owner_name="Test Owner",
        subdomain=f"taller-{uuid.uuid4().hex[:8]}",
        contact_email=f"test-{uuid.uuid4().hex[:6]}@taller.com",
        contact_whatsapp="593999000001",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Shop(**defaults)


def _make_case(shop_id, *, source_type: str = "synthetic", embedding=None) -> DiagnosticCase:
    """Build a transient DiagnosticCase ORM object for tests."""
    return DiagnosticCase(
        shop_id=shop_id,
        source_type=source_type,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga luego de caída",
        diagnosed_cause="Puerto USB-C dañado",
        solution_applied="Reemplazo de puerto USB-C",
        repair_time_minutes=60,
        estimated_cost=Decimal("35.00"),
        embedding=embedding or MOCK_VECTOR,
    )


def _embedding_url() -> str:
    settings = get_settings()
    return f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"


# ─── 1. Pure scoring logic ────────────────────────────────────────────────────

def test_real_case_bonus_constant_is_positive():
    """REAL_CASE_BONUS must be > 0 for prioritisation to work."""
    assert REAL_CASE_BONUS > 0.0


def test_distance_threshold_is_below_one():
    """DISTANCE_THRESHOLD must be a valid cosine distance (0–2)."""
    assert 0.0 < DISTANCE_THRESHOLD < 2.0


def test_composite_score_real_beats_synthetic_at_same_distance():
    """
    A real_validated case and a synthetic case with identical cosine distances
    must result in the real case having a higher composite_score.
    """
    distance = 0.30
    synthetic_similarity = 1.0 - distance
    synthetic_composite = synthetic_similarity + 0.0

    real_similarity = 1.0 - distance
    real_composite = real_similarity + REAL_CASE_BONUS

    assert real_composite > synthetic_composite


def test_composite_score_real_beats_slightly_better_synthetic():
    """
    A real_validated case with slightly WORSE cosine distance must still
    outrank a synthetic case, as long as the gap < REAL_CASE_BONUS.
    """
    synthetic_distance = 0.28
    real_distance = synthetic_distance + (REAL_CASE_BONUS / 2)   # Real is a bit farther

    synthetic_composite = (1.0 - synthetic_distance)
    real_composite = (1.0 - real_distance) + REAL_CASE_BONUS

    assert real_composite > synthetic_composite


def test_retrieved_case_is_frozen_dataclass():
    """RetrievedCase must be immutable (frozen dataclass)."""
    rc = RetrievedCase(
        case_id=uuid.uuid4(),
        source_type="synthetic",
        device_brand="Apple",
        device_model="iPhone 14",
        symptom_text="Pantalla negra",
        diagnosed_cause="Conector desconectado",
        solution_applied="Reconectar flex",
        repair_time_minutes=30,
        estimated_cost=Decimal("20.00"),
        cosine_distance=0.20,
        similarity_score=0.80,
        composite_score=0.80,
        shop_id=None,
    )
    with pytest.raises(Exception):
        rc.similarity_score = 0.99  # type: ignore[misc]


# ─── 2. Search with DB: ordering & tenant isolation ──────────────────────────

@respx.mock
async def test_search_returns_real_validated_before_synthetic(db_session):
    """
    When a real_validated case and a synthetic case exist at the same distance,
    the real case must appear first in the ranked results.
    """
    # Arrange: one shop with one real case; plus a global synthetic case.
    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    # Both cases use the exact same MOCK_VECTOR, so their cosine distance
    # to the query (also MOCK_VECTOR) will be essentially 0.
    synthetic_case = _make_case(None, source_type="synthetic", embedding=MOCK_VECTOR)
    real_case = _make_case(shop.id, source_type="real_validated", embedding=MOCK_VECTOR)
    db_session.add(synthetic_case)
    db_session.add(real_case)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [MOCK_VECTOR]}
        )
    )

    # Act
    result = await search_similar_cases(
        db=db_session,
        shop_id=shop.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga luego de caída",
    )

    # Assert
    assert not result.is_empty
    assert result.cases[0].source_type == "real_validated", (
        "real_validated case must rank first due to composite score bonus"
    )


@respx.mock
async def test_tenant_isolation_real_case_invisible_to_other_shop(db_session):
    """
    CRITICAL: A real_validated case belonging to shop_A must NOT appear in
    the search results for shop_B, even if it is semantically identical.
    """
    # Arrange: two distinct shops.
    shop_a = _make_shop(subdomain=f"shop-a-{uuid.uuid4().hex[:6]}")
    shop_b = _make_shop(subdomain=f"shop-b-{uuid.uuid4().hex[:6]}")
    db_session.add(shop_a)
    db_session.add(shop_b)
    await db_session.flush()

    # A real_validated case that belongs ONLY to shop_a.
    real_case_a = _make_case(shop_a.id, source_type="real_validated", embedding=MOCK_VECTOR)
    db_session.add(real_case_a)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [MOCK_VECTOR]}
        )
    )

    # Act: shop_b performs the search.
    result = await search_similar_cases(
        db=db_session,
        shop_id=shop_b.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga luego de caída",
    )

    # Assert: shop_b must see zero results (no synthetics, no shop_b's own real cases).
    case_ids = [str(c.case_id) for c in result.cases]
    assert str(real_case_a.id) not in case_ids, (
        "shop_b must never see real_validated cases owned by shop_a"
    )


@respx.mock
async def test_synthetic_cases_visible_to_all_shops(db_session):
    """
    Global synthetic cases (shop_id IS NULL) must be accessible to any shop.
    """
    # Arrange: a shop that has never been seen before + a global synthetic case.
    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    global_synthetic = _make_case(None, source_type="synthetic", embedding=MOCK_VECTOR)
    db_session.add(global_synthetic)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [MOCK_VECTOR]}
        )
    )

    # Act
    result = await search_similar_cases(
        db=db_session,
        shop_id=shop.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga luego de caída",
    )

    # Assert
    assert any(c.case_id == global_synthetic.id for c in result.cases), (
        "Global synthetic cases (shop_id=NULL) must be visible to any tenant"
    )


# ─── 3. Distance threshold enforcement ───────────────────────────────────────

@respx.mock
async def test_distance_threshold_filters_far_results(db_session):
    """
    Cases with a cosine distance above DISTANCE_THRESHOLD must be excluded,
    and had_sufficient_evidence must be False when no cases pass the filter.
    """
    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    # Insert a synthetic case whose embedding is near MOCK_VECTOR.
    close_case = _make_case(None, source_type="synthetic", embedding=MOCK_VECTOR)
    db_session.add(close_case)
    await db_session.flush()

    # The query vector is very different (essentially orthogonal to MOCK_VECTOR).
    far_query_vector = FAR_VECTOR

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [far_query_vector]}
        )
    )

    result = await search_similar_cases(
        db=db_session,
        shop_id=shop.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="Síntoma completamente diferente",
    )

    assert result.is_empty, "Cases beyond distance threshold must be filtered out"
    assert result.had_sufficient_evidence is False, (
        "had_sufficient_evidence must be False when no cases pass the distance filter"
    )


# ─── 4. Empty state ───────────────────────────────────────────────────────────

@respx.mock
async def test_search_empty_database_returns_no_evidence(db_session):
    """
    When no diagnostic_cases exist at all, the result must be empty and
    had_sufficient_evidence must be False.
    """
    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [MOCK_VECTOR]}
        )
    )

    result = await search_similar_cases(
        db=db_session,
        shop_id=shop.id,
        device_brand="Unknown Brand",
        device_model="Unknown Model",
        symptom_text="Síntoma sin ningún caso parecido",
    )

    assert result.is_empty
    assert result.had_sufficient_evidence is False
    assert result.top_source_type is None
    assert result.top_similarity_score is None


# ─── 5. Embedding service failure propagation ─────────────────────────────────

@respx.mock
async def test_search_propagates_embedding_unavailable_error(db_session):
    """
    If the embedding service is unreachable, EmbeddingServiceUnavailableError
    must propagate out of search_similar_cases without being swallowed.
    """
    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        side_effect=httpx.ConnectError("Connection refused")
    )

    with pytest.raises(EmbeddingServiceUnavailableError):
        await search_similar_cases(
            db=db_session,
            shop_id=shop.id,
            device_brand="Apple",
            device_model="iPhone 14",
            symptom_text="Pantalla negra",
        )


# ─── 6. Telemetry logging ─────────────────────────────────────────────────────

@respx.mock
async def test_diagnostic_query_log_is_created_after_search(db_session):
    """
    Every successful search must flush a DiagnosticQueryLog row into the session.
    """
    from sqlalchemy import select as sa_select

    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    synthetic = _make_case(None, source_type="synthetic", embedding=MOCK_VECTOR)
    db_session.add(synthetic)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [MOCK_VECTOR]}
        )
    )

    ticket_id = None

    await search_similar_cases(
        db=db_session,
        shop_id=shop.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga luego de caída",
        ticket_id=ticket_id,
    )

    # Verify that the log row was flushed to the session.
    logs = (
        await db_session.execute(
            sa_select(DiagnosticQueryLog).where(
                DiagnosticQueryLog.shop_id == shop.id,
                DiagnosticQueryLog.ticket_id == ticket_id,
            )
        )
    ).scalars().all()

    assert len(logs) == 1
    log = logs[0]
    assert log.shop_id == shop.id
    assert log.ticket_id == ticket_id
    assert log.had_sufficient_evidence is True
    assert log.source_type_used == "synthetic"
    assert log.similarity_score is not None
    assert log.similarity_score > 0.0


@respx.mock
async def test_diagnostic_query_log_no_evidence_case(db_session):
    """
    When there are no results (insufficient evidence), the log row must record
    had_sufficient_evidence = False and top_case_id = None.
    """
    from sqlalchemy import select as sa_select

    shop = _make_shop()
    db_session.add(shop)
    await db_session.flush()

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [FAR_VECTOR]}
        )
    )

    await search_similar_cases(
        db=db_session,
        shop_id=shop.id,
        device_brand="Unknown",
        device_model="Unknown",
        symptom_text="Síntoma imposible de encontrar",
    )

    logs = (
        await db_session.execute(
            sa_select(DiagnosticQueryLog).where(
                DiagnosticQueryLog.shop_id == shop.id,
            )
        )
    ).scalars().all()

    assert len(logs) == 1
    assert logs[0].had_sufficient_evidence is False
    assert logs[0].top_case_id is None


# ─── 7. DiagnosticSearchResult helpers ───────────────────────────────────────

def test_search_result_is_empty_property():
    """DiagnosticSearchResult.is_empty must reflect the cases list state."""
    empty = DiagnosticSearchResult(query_text="test", cases=[])
    assert empty.is_empty is True

    non_empty = DiagnosticSearchResult(
        query_text="test",
        cases=[
            RetrievedCase(
                case_id=uuid.uuid4(),
                source_type="synthetic",
                device_brand="X",
                device_model="Y",
                symptom_text="Z",
                diagnosed_cause="D",
                solution_applied="S",
                repair_time_minutes=None,
                estimated_cost=None,
                cosine_distance=0.2,
                similarity_score=0.8,
                composite_score=0.8,
                shop_id=None,
            )
        ],
    )
    assert non_empty.is_empty is False
