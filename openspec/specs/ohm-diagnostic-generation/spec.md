# Specification: Ohm Controlled Diagnostic Generation & Application

## Capability: ohm-diagnostic-generation
Provides an isolated, verified, two-step workflow for synthesizing technical chat transcripts into customer-facing diagnostics and publishing them to tickets.

### Requirement: Diagnostic Synthesis Generation
The system MUST provide an endpoint POST /tickets/{ticket_id}/generate-diagnostic that synthesizes the ticket's internal Ohm chat history into a customer-facing draft diagnostic.

#### Scenario: Successfully generating draft diagnostic from chat history
- **Given** a ticket with status EN_REPARACION or LISTO_PARA_RETIRAR
- **And** an active open conversation with at least one message exchange
- **And** draft_diagnostic is currently null
- **When** the technician requests diagnostic generation
- **Then** the system calls the reasoning model with the synthesis prompt
- **And** saves the generated text into Ticket.draft_diagnostic
- **And** returns 200 OK with the generated text in the response body

#### Scenario: Rejecting generation when ticket status is ineligible
- **Given** a ticket with status EN_REVISION, EN_ESPERA_INGRESO, or ESPERANDO_APROBACION
- **When** the technician requests diagnostic generation
- **Then** the system returns 400 Bad Request
- **And** Ticket.draft_diagnostic remains unchanged

#### Scenario: Rejecting generation when chat history is empty
- **Given** a ticket with status EN_REPARACION
- **And** no diagnostic chat messages exist for this ticket
- **When** the technician requests diagnostic generation
- **Then** the system returns 400 Bad Request with message indicating prior conversation is required
- **And** no external AI calls are dispatched

#### Scenario: Rejecting second generation attempt when draft already exists
- **Given** a ticket where draft_diagnostic is already populated
- **When** a generation request is sent
- **Then** the system returns 409 Conflict indicating a diagnostic has already been generated

#### Scenario: Handling AI service unavailability
- **Given** a valid eligible ticket and non-empty chat history
- **When** the AI service fails after all backoff retries (e.g. 503)
- **Then** the system returns 503 Service Unavailable
- **And** Ticket.draft_diagnostic remains null, leaving the single-generation allowance unconsumed

### Requirement: Diagnostic Application to Public Tracking
The system MUST provide an endpoint POST /tickets/{ticket_id}/apply-diagnostic that copies the draft diagnostic to public diagnostic_notes with optional manual edits.

#### Scenario: Applying draft diagnostic without manual edits
- **Given** a ticket with an existing draft_diagnostic
- **When** POST /tickets/{ticket_id}/apply-diagnostic is called with {} or { edited_diagnostic: null }
- **Then** Ticket.diagnostic_notes is updated to equal Ticket.draft_diagnostic
- **And** Ticket.diagnostic_applied_at is set to the current UTC timestamp
- **And** the customer tracking portal reflects the new diagnostic notes

#### Scenario: Applying draft diagnostic with manual edits
- **Given** a ticket with an existing draft_diagnostic
- **When** POST /tickets/{ticket_id}/apply-diagnostic is called with { edited_diagnostic: "Texto corregido manualmente" }
- **Then** Ticket.diagnostic_notes is updated to "Texto corregido manualmente"
- **And** Ticket.draft_diagnostic is updated to "Texto corregido manualmente"
- **And** Ticket.diagnostic_applied_at is set to the current UTC timestamp

#### Scenario: Rejecting application when draft has not been generated
- **Given** a ticket where draft_diagnostic is null
- **When** POST /tickets/{ticket_id}/apply-diagnostic is called
- **Then** the system returns 400 Bad Request indicating no draft exists to apply

### Requirement: Frontend Decoupling & Review Interface
The technician interface MUST isolate the generation and application actions from raw assistant response bubbles.

#### Scenario: Absence of per-message apply buttons
- **Given** an active chat with Ohm in ticket context
- **When** an assistant reply is rendered
- **Then** no "Aplicar al Diagnóstico" button is displayed on individual message bubbles

#### Scenario: Displaying editable review area and applying
- **Given** a ticket in EN_REPARACION
- **When** the technician clicks "Generar con Ohm" and the call succeeds
- **Then** the generated draft is displayed in an editable review area
- **And** the "Generar con Ohm" button is disabled
- **And** the "Aplicar Diagnóstico" button is enabled
