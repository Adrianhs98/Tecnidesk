# Spec: StatusBadge Component (Technician Integration)

## Capability: status-badge
Render consistent, accessible ticket status badges with theme-aware colors, borders, and icons defined in `DESIGN.md`.

### Requirement: Technician Portal Integration
The `<TechnicianTicketCard />` component MUST render the unified `<StatusBadge />` instead of legacy unstyled pill elements.

#### Scenario: Render status badge in TechnicianTicketCard
- **Given** a ticket with status `"EN_REVISION"` rendered in `TechnicianTicketCard`
- **When** the card header is rendered
- **Then** a `.ticket-badge` element is present containing `"En revision"` and `"REV"`
- **And** no obsolete `.tech-status-pill` element is rendered in the DOM
