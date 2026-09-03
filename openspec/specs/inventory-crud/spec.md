# Inventory CRUD Specification
## Purpose
Define the basic operations (list, create, update, soft-delete, restock) for shop inventory items.

## Requirements
### Requirement: List Inventory
The system MUST return a paginated list of inventory items, filterable by name and SKU, returning active-only items by default.
#### Scenario: List active items
- GIVEN an authenticated user
- WHEN the user requests the inventory list
- THEN the system returns a paginated list of active inventory items for the shop

### Requirement: Create Inventory Item
The system MUST persist a new item scoped to the shop.
#### Scenario: Create successful
- GIVEN an authenticated user and valid item data
- WHEN the user creates an inventory item
- THEN the system persists the item and returns the created record

### Requirement: Update Inventory Item
The system MUST apply partial updates and MUST return 404 if the item is not found in the shop.
#### Scenario: Update existing item
- GIVEN an authenticated user and an existing item ID
- WHEN the user updates the item with new fields
- THEN the system applies the changes and returns the updated item

#### Scenario: Update non-existent item
- GIVEN an authenticated user and a non-existent item ID
- WHEN the user updates the item
- THEN the system returns a 404 Not Found error

### Requirement: Soft Delete
The system MUST mark the item as inactive (`is_active=False`) and MUST return 404 if not found.
#### Scenario: Delete existing item
- GIVEN an authenticated user and an existing item ID
- WHEN the user deletes the item
- THEN the system marks the item as inactive

#### Scenario: Delete non-existent item
- GIVEN an authenticated user and a non-existent item ID
- WHEN the user deletes the item
- THEN the system returns a 404 Not Found error

### Requirement: Restock
The system MUST increment the stock quantity and MUST return 404 if the item is not found.
#### Scenario: Restock existing item
- GIVEN an authenticated user, an existing item ID, and a positive quantity
- WHEN the user restocks the item
- THEN the system increments the item's stock by the given quantity

#### Scenario: Restock non-existent item
- GIVEN an authenticated user and a non-existent item ID
- WHEN the user restocks the item
- THEN the system returns a 404 Not Found error
