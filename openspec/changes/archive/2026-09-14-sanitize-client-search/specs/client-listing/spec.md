# Client Listing Specification (Delta)

## MODIFIED Requirements

### Requirement: Client Search
The system MUST support filtering by partial match on `full_name`, `email`, or `phone_number` (case-insensitive), while stripping leading/trailing whitespace, normalizing whitespace-only queries to unconstrained searches, and escaping SQL wildcard characters (`%`, `_`). The system MUST reject search terms exceeding 100 characters with a 422 Validation Error.

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
