# Spec: Platform Admin — Shop Activation

## Requirements

### Requirement: Reject requests without the platform key
The system must reject any call to `POST /tickets/admin/activate-shop` that does
not include the `X-Superadmin-Key` header.

#### Scenario: Missing header returns 401
- **Given** the endpoint `POST /tickets/admin/activate-shop` receives a request
- **When** the `X-Superadmin-Key` header is absent
- **Then** the response status must be `HTTP 401 Unauthorized`
- **And** the response body must include a `detail` field explaining the missing credential

---

### Requirement: Reject requests with an incorrect platform key
The system must reject calls that include the `X-Superadmin-Key` header but with
a value that does not match the configured `SUPERADMIN_API_KEY` environment variable.

#### Scenario: Wrong key returns 403
- **Given** the endpoint `POST /tickets/admin/activate-shop` receives a request
- **When** the `X-Superadmin-Key` header is present but its value does not match `SUPERADMIN_API_KEY`
- **Then** the response status must be `HTTP 403 Forbidden`
- **And** the response body must include a `detail` field

---

### Requirement: Accept and execute activation with the correct platform key
The system must activate the target shop's subscription when the correct
`X-Superadmin-Key` is provided, regardless of whether the caller has a valid
tenant JWT.

#### Scenario: Correct key activates shop
- **Given** a shop with an existing subscription record in the database
- **When** `POST /tickets/admin/activate-shop` is called with the correct `X-Superadmin-Key`
  and a valid `shop_id` and `days` in the body
- **Then** the response status must be `HTTP 200 OK`
- **And** the subscription `status` must be set to `active`
- **And** the subscription `ends_at` must be extended by the requested number of days from now

#### Scenario: Correct key without tenant JWT is accepted
- **Given** a valid `SUPERADMIN_API_KEY` is configured
- **When** `POST /tickets/admin/activate-shop` is called with the correct key
  but **no** `Authorization: Bearer` header
- **Then** the response status must be `HTTP 200 OK`
- **And** the activation must proceed normally

---

### Requirement: Tenant JWT alone is not sufficient to activate a shop
The system must not allow a valid tenant JWT — with no platform key — to reach
the activation logic.

#### Scenario: Valid JWT without platform key is rejected
- **Given** a valid, non-expired tenant JWT for an `admin`-role user
- **When** `POST /tickets/admin/activate-shop` is called with that JWT
  but without the `X-Superadmin-Key` header
- **Then** the response status must be `HTTP 401 Unauthorized`

---

### Requirement: Key comparison must not leak timing information
The system must compare the provided key against the configured secret using a
constant-time algorithm to prevent timing-based key enumeration.

#### Scenario: Comparison uses secrets.compare_digest
- **Given** the `superadmin_key_guard` dependency is invoked
- **When** it compares the provided key against `settings.superadmin_api_key`
- **Then** the comparison must use `secrets.compare_digest` (not `==` or `!=`)
