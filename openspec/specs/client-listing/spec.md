# Client Listing Specification
## Purpose
Define the behavior for fetching and searching a paginated list of customers belonging to a shop.

## Requirements
### Requirement: Authenticated Client Listing
The system MUST return a paginated list of customers belonging to the authenticated user's shop.
#### Scenario: Retrieve paginated customers
- GIVEN an authenticated user belonging to a shop
- WHEN the user requests the client list
- THEN the system returns a paginated response of clients scoped to the user's shop

#### Scenario: Unauthenticated request
- GIVEN an unauthenticated request
- WHEN the request is made to the client listing
- THEN the system returns a 401 Unauthorized error

### Requirement: Client Search
The system MUST support filtering by partial match on `full_name`, `email`, or `phone_number` (case-insensitive), while stripping leading/trailing whitespace, normalizing whitespace-only queries to unconstrained searches, and escaping SQL wildcard characters (`%`, `_`). The system MUST reject search terms exceeding 100 characters with a 422 Validation Error.

#### Scenario: Search with exact or partial match
- GIVEN an authenticated user
- WHEN the user requests the client list with a search term that matches a client's name, email, or phone
- THEN the system returns the matching clients

#### Scenario: Search with no results
- GIVEN an authenticated user
- WHEN the user requests the client list with a search term that matches no clients
- THEN the system returns an empty list

#### Scenario: Search with whitespace-only string returns all clients
- GIVEN an authenticated user for a shop with registered clients
- WHEN the user sends a search query composed solely of whitespace (e.g. `"   "`)
- THEN the system treats it as an unconstrained search and returns all clients for the shop

#### Scenario: Search with leading and trailing whitespace trims search term
- GIVEN an authenticated user for a shop with a client named "Carlos Santana"
- WHEN the user sends a search query with padding `"  Carlos  "`
- THEN the system strips the surrounding whitespace and returns the matching client

#### Scenario: Search with literal wildcard characters escapes them safely
- GIVEN an authenticated user for a shop with a client named "Special%User" and another "Special_User"
- WHEN the user searches specifically for `"Special%"`
- THEN the system escapes the `%` character and returns only clients containing the literal `%`

#### Scenario: Search query exceeding 100 characters is rejected
- GIVEN an authenticated user
- WHEN the user sends a search query exceeding 100 characters
- THEN the system returns a 422 Validation Error

### Requirement: Pagination Bounds
The system MUST enforce pagination bounds: `skip` MUST be >= 0, `limit` MUST be between 1 and 100.
#### Scenario: Valid pagination parameters
- GIVEN an authenticated user
- WHEN the user requests the client list with valid `skip` and `limit`
- THEN the system returns the corresponding subset of clients

#### Scenario: Invalid pagination parameters
- GIVEN an authenticated user
- WHEN the user requests the client list with `limit` > 100 or `skip` < 0
- THEN the system returns a 422 Validation Error
