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
The system MUST support filtering by partial match on `full_name`, `email`, or `phone_number` (case-insensitive).
#### Scenario: Search with exact or partial match
- GIVEN an authenticated user
- WHEN the user requests the client list with a search term that matches a client's name, email, or phone
- THEN the system returns the matching clients

#### Scenario: Search with no results
- GIVEN an authenticated user
- WHEN the user requests the client list with a search term that matches no clients
- THEN the system returns an empty list

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
