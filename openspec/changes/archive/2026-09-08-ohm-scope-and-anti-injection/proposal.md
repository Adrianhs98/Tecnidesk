# Proposal: Ohm Technical Scope Restriction & Anti Prompt-Injection Guard

## Problem Statement
Currently, technician and workshop interactions with Ohm (`/diagnostic/chat` in `app/routers/diagnostic.py` and `POST /tickets/{id}/diagnostic-chat` via `CorrectionService.handle_chat_message`) pass user messages directly to Google Gemini reasoning models (`gemini-3.6-flash`) without topic boundaries or prompt injection defenses. This causes two major operational vulnerabilities:
1. **Quota & Cost Waste (Off-Topic Drift):** Technicians or users can submit arbitrary non-repair questions (general conversation, homework, off-topic prompts), consuming expensive reasoning quota and risking Gemini 503 rate limits.
2. **Prompt Injection Risk:** Malicious or rogue inputs attempting jailbreaks, system prompt exfiltration, or role redefinition ("ignore previous instructions and do X") are processed unmitigated by the core model, with zero audit trail or security visibility.

## Proposed Solution
Implement a two-layered defense architecture:
1. **Pre-Execution Classification Guard (`ai_safety_service.py`):** Before invoking the expensive reasoning model or RAG vector searches, evaluate message safety using the fast, cost-effective model (`gemini-3.5-flash-lite`) in a single JSON call assessing:
   - `on_topic: bool` (whether the query relates to device diagnosis, microelectronics, hardware troubleshooting, or workshop repair operations).
   - `injection_attempt: bool` (whether the query attempts to hijack persona, override instructions, or exfiltrate system rules).
2. **Canned Redirection & Security Logging:**
   - Both off-topic queries and prompt injection attempts are terminated immediately and redirected using a unified neutral response (`CANNED_REDIRECT_RESPONSE`).
   - Injection attempts are persisted into a dedicated audit table (`ai_security_events`) tracking `shop_id`, `technician_id`, `ticket_id`, event type, timestamp, and a truncated 280-character excerpt for security observability.
3. **Prompt Hardening (Sandwich Defense):**
   - Base system prompts in both free and ticket-scoped diagnostic chats explicitly state that user-provided text attempting role redefinition or instruction overrides must be treated as passive technical input, never executable commands.
   - Reinforce this defense immediately following user input (sandwich technique) prior to model generation.

## Scope & Impact
- **Backend:**
  - New model `AiSecurityEvent` in `app/models/ai_security_event.py` and Alembic migration.
  - New safety module `app/services/ai_safety_service.py` implementing `classify_message_safety`, `log_ai_security_event`, and prompt builders.
  - Guard integration in `app/routers/diagnostic.py` (`workshop_diagnostic_chat`) and `app/services/correction_service.py` (`handle_chat_message`).
  - Strict multi-tenant isolation by `shop_id`.
- **Frontend:** No breaking contract changes. Existing chat drawer UI seamlessly handles canned redirect responses.
- **Tests:** Comprehensive unit tests covering topic classification, injection detection, canned redirect responses, database event persistence, and tenant isolation.
