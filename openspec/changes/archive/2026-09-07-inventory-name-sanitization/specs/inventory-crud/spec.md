# Specification Delta: Inventory CRUD

## Capability: inventory-crud
Extends inventory creation and updating requirements with strict whitespace sanitization and non-empty character validation for `item_name`.

### Requirement: Item Name Sanitization (Create)
The system MUST strip leading and trailing whitespace from `item_name` upon creation, and MUST reject names with fewer than 2 non-whitespace characters.

#### Scenario: Stripping leading and trailing whitespace on creation
- **Given** an inventory creation payload with `item_name = "  Batería iPhone 13  "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `item_name` is stored cleanly as `"Batería iPhone 13"`

#### Scenario: Rejection of whitespace-only item name on creation
- **Given** an inventory creation payload with `item_name = "   "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error
- **And** indicates that `item_name` must contain at least 2 non-whitespace characters

#### Scenario: Rejection of single-character item name on creation
- **Given** an inventory creation payload with `item_name = "a "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error
- **And** indicates that `item_name` must contain at least 2 non-whitespace characters

### Requirement: Item Name Sanitization (Update)
The system MUST strip leading and trailing whitespace from `item_name` upon update if provided, and MUST reject names with fewer than 2 non-whitespace characters while allowing `None` for partial updates.

#### Scenario: Stripping leading and trailing whitespace on update
- **Given** an inventory update payload with `item_name = "  Pin de Carga Type-C  "`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `item_name` is cleaned to `"Pin de Carga Type-C"`

#### Scenario: Rejection of whitespace-only item name on update
- **Given** an inventory update payload with `item_name = "    "`
- **When** the schema validation is applied
- **Then** the validation fails with a validation error

#### Scenario: Allowing None for partial updates
- **Given** an inventory update payload with `item_name = None` and `selling_price = 15.00`
- **When** the schema validation is applied
- **Then** the validation succeeds
- **And** `item_name` remains `None`
