# Specification: Backend Search Query Sanitization

## Capability: backend-search-sanitization
Ensures query search parameters passed to ticket, inventory, and client listing endpoints and services are sanitized by trimming whitespace and normalizing empty or whitespace-only inputs to `None`.

### Requirement: Ticket Search Parameter Sanitization
The system MUST strip leading and trailing whitespace from the `search` parameter in `ticket_service.list_tickets`. If the parameter is empty or contains only whitespace, it MUST be treated as `None` (unfiltered search).

#### Scenario: Whitespace-only search returns all tickets without filtering
- **Given** tickets exist in the shop database
- **When** `list_tickets` is invoked with `search = "   "`
- **Then** no search filter is applied
- **And** all tickets belonging to the shop (within pagination bounds) are returned

#### Scenario: Padded search term trims whitespace and matches tickets
- **Given** a ticket exists with `device_brand = "Samsung"` and `device_model = "Galaxy A54"`
- **When** `list_tickets` is invoked with `search = "  Samsung  "`
- **Then** the search term is trimmed to `"Samsung"`
- **And** the ticket is matched and returned

#### Scenario: Trimmed UUID search matches exact ticket ID
- **Given** a ticket exists with a specific `id`
- **When** `list_tickets` is invoked with `search = f"  {ticket.id}  "`
- **Then** the search term is trimmed and successfully parsed as a UUID
- **And** the exact ticket is matched and returned

---

### Requirement: Inventory Search Parameter Sanitization
The system MUST strip leading and trailing whitespace from `search` and `sku` parameters in `list_inventory`. If either parameter is empty or contains only whitespace, it MUST be normalized to `None`.

#### Scenario: Whitespace-only search returns all inventory items
- **Given** active inventory items exist in the shop
- **When** `list_inventory` is invoked with `search = "   "` and `sku = "   "`
- **Then** no search or SKU filter is applied
- **And** all active inventory items are returned

#### Scenario: Padded search term trims whitespace and matches inventory item
- **Given** an inventory item exists with `item_name = "Display Samsung A12"`
- **When** `list_inventory` is invoked with `search = "  Display Samsung  "`
- **Then** the search term is trimmed to `"Display Samsung"`
- **And** the item is matched and returned

---

### Requirement: Client Search Parameter Sanitization
The system MUST strip leading and trailing whitespace from the `search` parameter in `ClientService.get_clients` and `GET /clients`. If the parameter is empty or contains only whitespace, it MUST be normalized to `None`.

#### Scenario: Whitespace-only search returns all clients
- **Given** registered customers exist for the shop
- **When** `ClientService.get_clients` or `GET /clients` is invoked with `search = "   "`
- **Then** no search filter is applied
- **And** all customers for the shop are returned

#### Scenario: Padded search term trims whitespace and matches client
- **Given** a customer exists with `full_name = "Carlos Santana"`, `email = "carlos@example.com"`, `phone_number = "0991234567"`
- **When** `ClientService.get_clients` is invoked with `search = "  carlos  "`
- **Then** the search term is trimmed to `"carlos"`
- **And** the customer is matched and returned
