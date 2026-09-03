# Capability: Health Endpoint

## Feature: Health Check Metrics

### Scenario: Successfully retrieve health status with version and uptime
Given the TecniDesk API is running
When a GET request is made to `/health`
Then the response status code MUST be 200
And the JSON payload MUST contain `"status": "ok"`
And the JSON payload MUST contain `"service": "TecniDesk API"`
And the JSON payload MUST contain `"version"` as a string matching `"1.0.0"`
And the JSON payload MUST contain `"uptime_seconds"` as a non-negative float
And the JSON payload MUST contain `"timestamp"` in valid ISO-8601 UTC format
