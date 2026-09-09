# Specification: Ohm Scope Restriction and Anti Prompt-Injection

## Requirements

### Requirement 1: Message Safety Classification
The system SHALL classify inbound technician messages before invoking reasoning models or executing RAG lookups.
- The classifier SHALL return a structured result with two boolean flags:
  - `on_topic`: `True` if the content pertains to device diagnostics, hardware, microelectronics, electronics repair, parts, tools, or workshop operations; `False` otherwise.
  - `injection_attempt`: `True` if the content attempts to override system rules, reassign Ohm's role, command the model to ignore guidelines, or reveal system prompts; `False` otherwise.
- The classifier SHALL use the lightweight fast model (`gemini-3.5-flash-lite`) requesting JSON schema response `{"on_topic": bool, "injection_attempt": bool}` in a single model call.
- If classification fails due to external API errors or JSON parse errors, the system SHALL default to safe degraded behavior: treating the message as `on_topic=True, injection_attempt=False` with error logging to avoid blocking legitimate technician work during transient outages.

### Requirement 2: Unified Canned Redirection Response
The system SHALL terminate execution and return a standardized canned response when `not on_topic` OR `injection_attempt`:
- Canned text: `"Soy Ohm, tu copiloto de taller. Te ayudo exclusivamente con diagnósticos técnicos y reparación de dispositivos. ¿Tienes alguna consulta sobre la reparación en curso?"`
- The system SHALL use the exact same canned response for both off-topic queries and injection attempts to avoid revealing to adversarial users that their attack vector was specifically classified.

### Requirement 3: Security Event Audit Trail
The system SHALL log detected injection attempts in a dedicated database table `ai_security_events`.
- Logged fields:
  - `id`: UUID primary key.
  - `shop_id`: UUID Foreign Key to `shops.id` (mandatory, ondelete CASCADE).
  - `technician_id`: UUID Foreign Key to `technicians.id` (nullable, ondelete SET NULL).
  - `ticket_id`: UUID Foreign Key to `tickets.id` (nullable, ondelete SET NULL).
  - `event_type`: String(50), default `"injection_attempt"`.
  - `message_excerpt`: Truncated excerpt of the offending message (max 280 characters).
  - `created_at`: UTC timestamp.
- Logging MUST execute within the database session and commit asynchronously without crashing the user response.

### Requirement 4: Multi-Layer Prompt Hardening (Sandwich Defense)
When a message is safe and on-topic, prompts submitted to the reasoning model (`gemini-3.6-flash`) SHALL incorporate anti-injection defenses:
- Base system prompt MUST instruct the model that text within user messages attempting instruction overrides, persona changes, or secret extraction must be treated solely as passive diagnostic text, never as commands.
- The final prompt segment immediately surrounding or following user input MUST reinforce this rule (sandwich technique) to ensure high recency weight in model attention.

### Requirement 5: Dual Entrypoint Integration
The safety guard MUST intercept both Ohm communication pathways:
1. `POST /diagnostic/chat` (`workshop_diagnostic_chat` in `app/routers/diagnostic.py`).
2. `POST /tickets/{id}/diagnostic-chat` (`CorrectionService.handle_chat_message` in `app/services/correction_service.py`).
