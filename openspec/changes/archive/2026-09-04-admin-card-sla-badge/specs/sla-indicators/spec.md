# Spec: SLA Indicators & Exception Badges

## Capability: sla-indicators
Consistent, accessible visual cues for tickets that exceed SLA thresholds in the admin card view.

### Requirement: Overdue Ticket Visual Indication
When a ticket's elapsed time exceeds the defined SLA threshold for its status, the card container MUST reflect the stale state.

#### Scenario: Card marked as stale when SLA exceeded
- **Given** an active ticket whose duration exceeds the SLA threshold
- **When** the `<AdminTicketCard />` is rendered
- **Then** the outer `.ticket-card` element has the CSS class `"is-stale"`
- **And** a badge with text `"Vencido"` and `data-testid="sla-stale-badge"` is rendered
- **And** the badge has the title `"Tiempo límite de atención superado (SLA vencido)"`

#### Scenario: Healthy ticket within SLA
- **Given** a recently created ticket well within its SLA threshold
- **When** the `<AdminTicketCard />` is rendered
- **Then** the outer `.ticket-card` does NOT have the class `"is-stale"`
- **And** no `"Vencido"` badge is rendered

### Requirement: Signal De-duplication
The technician signal row MUST render the unassigned state exactly once.

#### Scenario: Unassigned technician display
- **Given** a ticket with `technician: null`
- **When** the `<AdminTicketCard />` is rendered
- **Then** the text `"Sin técnico"` appears exactly once across the card surface
