# Spec: Frontend Currency Formatting

## Requirements

### Requirement: Standardize currency output format
The utility must format valid numeric values (both numbers and numeric strings) into a 2-decimal USD string.

#### Scenario: Valid integer formatting
- **Given** an integer input (e.g., 15)
- **When** the value is formatted for currency
- **Then** the output should be "$15.00"

#### Scenario: Valid float formatting
- **Given** a floating point input (e.g., 12.3)
- **When** the value is formatted for currency
- **Then** the output should be "$12.30"

#### Scenario: String numeric input
- **Given** a string containing a valid number (e.g., "45.99")
- **When** the value is formatted for currency
- **Then** the output should be "$45.99"

### Requirement: Handle invalid or missing inputs safely
The utility must not throw errors when given invalid or missing inputs. It should return a safe fallback value.

#### Scenario: Null or undefined input
- **Given** a null or undefined input
- **When** the value is formatted for currency
- **Then** the output should be the safe fallback "$0.00"

#### Scenario: Invalid string or NaN input
- **Given** a non-numeric string (e.g., "abc") or NaN
- **When** the value is formatted for currency
- **Then** the output should be the safe fallback "$0.00"
