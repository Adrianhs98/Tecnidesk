"""
Integration tests for Phase 4: Human-in-the-Loop Correction Chat.

Test strategy:
  - Tests use the `db_session` fixture from conftest.py (auto-rollback).
  - Gemini API calls are mocked via monkeypatch (no real LLM calls).
  - EmbeddingService calls are mocked via respx (no real Ollama calls).
  - Tests validate the correction_service logic directly, not HTTP endpoints,
    because the project's conftest does not provide auth/JWT fixtures.

Coverage:
  1. get_or_create_conversation — creates a new conversation tied to a ticket.
  2. handle_chat_message — stores technician message, calls Gemini, stores reply.
  3. confirm_correction — creates a real_validated case with embedding, closes conversation.
  4. Coexistence — synthetic and real_validated cases live side by side for the same symptom.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from sqlalchemy import select

from app.config import get_settings
from app.models.diagnostic import (
    DiagnosticCase,
    DiagnosticConversation,
    DiagnosticMessage,
    DiagnosticQueryLog,
)
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketStatusEnum
from app.schemas.diagnostic import (
    ConfirmCorrectionIn,
    DiagnosticMessageIn,
)
from app.services.correction_service import CorrectionService


from app.models.technician import Technician

# ─── Helpers ──────────────────────────────────────────────────────────────────

MOCK_VECTOR: list[float] = [0.1] * 768


def _embedding_url() -> str:
    settings = get_settings()
    return f"{settings.local_embedding_service_url.rstrip('/')}/api/embed"


async def _seed_shop_and_ticket(db_session) -> tuple:
    """Create a shop, customer, technician, and ticket for testing."""
    shop = Shop(
        business_name="Test Taller Corrección",
        owner_name="Test Owner",
        subdomain=f"taller-corr-{uuid.uuid4().hex[:8]}",
        contact_email=f"corr-{uuid.uuid4().hex[:6]}@test.com",
        contact_whatsapp="593999000002",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    customer = Customer(
        shop_id=shop.id,
        full_name="Cliente Test",
        phone_number="593987654321",
        email="cliente@test.com",
    )
    db_session.add(customer)
    await db_session.flush()

    technician = Technician(
        shop_id=shop.id,
        full_name="Técnico Test",
    )
    db_session.add(technician)
    await db_session.flush()

    ticket = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        issue_description="No carga después de caída",
        status=TicketStatusEnum.EN_REVISION,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    return shop, ticket, technician.id


# ─── 1. Conversation creation ────────────────────────────────────────────────

async def test_get_or_create_conversation_creates_new(db_session):
    """
    When no open conversation exists for a ticket, a new one must be created.
    """
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)

    conv = await CorrectionService.get_or_create_conversation(
        db=db_session,
        shop_id=shop.id,
        technician_id=tech_id,
        ticket_id=ticket.id,
    )

    assert conv is not None
    assert conv.ticket_id == ticket.id
    assert conv.shop_id == shop.id
    assert conv.status == "open"


async def test_get_or_create_conversation_returns_existing(db_session):
    """
    Calling get_or_create_conversation twice for the same ticket must return
    the same conversation (idempotent).
    """
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)

    conv1 = await CorrectionService.get_or_create_conversation(
        db=db_session, shop_id=shop.id, technician_id=tech_id, ticket_id=ticket.id,
    )
    conv2 = await CorrectionService.get_or_create_conversation(
        db=db_session, shop_id=shop.id, technician_id=tech_id, ticket_id=ticket.id,
    )

    assert conv1.id == conv2.id


# ─── 2. Chat message handling ────────────────────────────────────────────────

async def test_handle_chat_message_stores_and_replies(db_session, monkeypatch):
    """
    handle_chat_message must:
      1. Store the technician's message in the DB.
      2. Call Gemini (mocked) and store the assistant reply.
      3. Return a DiagnosticMessageResponse with role='assistant'.
    """
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)

    # Mock Gemini client
    class MockResponse:
        text = "I understand. The charging IC could indeed be the issue. Let me adjust the diagnosis."

    class MockModels:
        def generate_content(self, *args, **kwargs):
            return MockResponse()

    class MockClient:
        def __init__(self, *args, **kwargs):
            self.models = MockModels()

    monkeypatch.setattr("app.services.correction_service.genai.Client", MockClient)

    message_in = DiagnosticMessageIn(message="No es la batería, es el IC de carga U2.")

    response = await CorrectionService.handle_chat_message(
        db=db_session,
        shop_id=shop.id,
        technician_id=tech_id,
        ticket_id=ticket.id,
        message_in=message_in,
    )

    assert response.role == "assistant"
    assert "charging IC" in response.content

    # Verify both messages were stored in the DB
    msgs = (
        await db_session.execute(
            select(DiagnosticMessage).where(
                DiagnosticMessage.conversation_id == response.id
                # conversation_id might not match response.id; let's query by conv
            )
        )
    )
    # Better: find the conversation and check its messages
    conv_result = await db_session.execute(
        select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket.id,
            DiagnosticConversation.status == "open",
        )
    )
    conv = conv_result.scalar_one()

    msg_result = await db_session.execute(
        select(DiagnosticMessage).where(
            DiagnosticMessage.conversation_id == conv.id
        ).order_by(DiagnosticMessage.created_at.asc())
    )
    messages = msg_result.scalars().all()

    assert len(messages) == 2
    assert messages[0].role == "technician"
    assert messages[0].content == "No es la batería, es el IC de carga U2."
    assert messages[1].role == "assistant"


# ─── 3. Confirm correction — creates real_validated case ─────────────────────

@respx.mock
async def test_confirm_correction_creates_real_validated_case(db_session, monkeypatch):
    """
    confirm_correction must:
      1. Generate an embedding for the new validated solution.
      2. Create a DiagnosticCase with source_type='real_validated'.
      3. Set derived_from_case_id pointing to the original synthetic case.
      4. Close the conversation (status='confirmed').
    """
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)

    # Seed a synthetic case to be the "original" case
    synthetic_case = DiagnosticCase(
        shop_id=None,
        source_type="synthetic",
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga después de caída",
        diagnosed_cause="Puerto USB-C dañado",
        solution_applied="Reemplazo de puerto USB-C",
        repair_time_minutes=60,
        estimated_cost=Decimal("35.00"),
        embedding=MOCK_VECTOR,
    )
    db_session.add(synthetic_case)
    await db_session.flush()

    # Seed a query log pointing to that synthetic case
    query_log = DiagnosticQueryLog(
        shop_id=shop.id,
        ticket_id=ticket.id,
        query_text="Samsung Galaxy A54 5G no carga",
        top_case_id=synthetic_case.id,
        source_type_used="synthetic",
        similarity_score=0.85,
        had_sufficient_evidence=True,
    )
    db_session.add(query_log)
    await db_session.flush()

    # Create an open conversation linked to the synthetic case
    conv = await CorrectionService.get_or_create_conversation(
        db=db_session, shop_id=shop.id, technician_id=tech_id, ticket_id=ticket.id,
    )
    assert conv.diagnostic_case_id == synthetic_case.id

    # Mock embedding service for the new case
    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(
            200, json={"embeddings": [MOCK_VECTOR]}
        )
    )

    confirm_in = ConfirmCorrectionIn(
        diagnosed_cause="IC de carga U2 dañado por impacto",
        solution_applied="Reemplazo de IC U2 con reballing, verificado 5V 1A",
        estimated_cost=85.0,
        repair_time_minutes=90,
    )

    result = await CorrectionService.confirm_correction(
        db=db_session,
        shop_id=shop.id,
        technician_id=tech_id,
        ticket_id=ticket.id,
        confirm_in=confirm_in,
    )

    # Verify the new case
    assert result.source_type == "real_validated"
    assert result.diagnosed_cause == "IC de carga U2 dañado por impacto"
    assert result.device_brand == "Samsung"

    # Verify DB state: the case exists with correct linkage
    case_result = await db_session.execute(
        select(DiagnosticCase).where(DiagnosticCase.id == result.id)
    )
    new_case = case_result.scalar_one()
    assert new_case.source_type == "real_validated"
    assert new_case.shop_id == shop.id
    assert new_case.derived_from_case_id == synthetic_case.id

    # Verify conversation was closed
    await db_session.refresh(conv)
    assert conv.status == "confirmed"


# ─── 4. Coexistence of synthetic and real_validated cases ─────────────────────

@respx.mock
async def test_synthetic_and_real_cases_coexist(db_session, monkeypatch):
    """
    After confirmation, both the original synthetic case (shop_id=NULL) and the
    new real_validated case (shop_id=shop.id) must coexist in the database.
    The real case must NOT overwrite or delete the synthetic one.
    """
    shop, ticket, tech_id = await _seed_shop_and_ticket(db_session)

    # Seed synthetic
    synthetic = DiagnosticCase(
        shop_id=None,
        source_type="synthetic",
        device_brand="Samsung",
        device_model="Galaxy A54 5G",
        symptom_text="No carga después de caída",
        diagnosed_cause="Puerto USB-C dañado",
        solution_applied="Reemplazo de puerto USB-C",
        repair_time_minutes=60,
        estimated_cost=Decimal("35.00"),
        embedding=MOCK_VECTOR,
    )
    db_session.add(synthetic)
    await db_session.flush()

    # Seed query log
    log = DiagnosticQueryLog(
        shop_id=shop.id, ticket_id=ticket.id,
        query_text="test", top_case_id=synthetic.id,
        source_type_used="synthetic", similarity_score=0.9,
        had_sufficient_evidence=True,
    )
    db_session.add(log)
    await db_session.flush()

    # Create conversation + confirm
    await CorrectionService.get_or_create_conversation(
        db=db_session, shop_id=shop.id, technician_id=tech_id, ticket_id=ticket.id,
    )

    respx.post(_embedding_url()).mock(
        return_value=httpx.Response(200, json={"embeddings": [MOCK_VECTOR]})
    )

    await CorrectionService.confirm_correction(
        db=db_session, shop_id=shop.id, technician_id=tech_id, ticket_id=ticket.id,
        confirm_in=ConfirmCorrectionIn(
            diagnosed_cause="IC U2 dañado",
            solution_applied="Reballing IC U2",
        ),
    )

    # Both cases must exist
    all_cases = (
        await db_session.execute(
            select(DiagnosticCase).where(
                DiagnosticCase.device_brand == "Samsung",
                DiagnosticCase.device_model == "Galaxy A54 5G",
            )
        )
    ).scalars().all()

    source_types = {c.source_type for c in all_cases}
    assert "synthetic" in source_types, "Original synthetic case must still exist"
    assert "real_validated" in source_types, "New real_validated case must exist"
    assert len(all_cases) >= 2, "Both cases must coexist"
