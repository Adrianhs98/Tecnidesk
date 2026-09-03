# Proposal: Fix Tracking Tests
## Intent
Fix 3 failing unit tests by correcting the URL paths to match the actual mounted routes.
## Scope
### In Scope
Update the 3 test method URLs in `test_tracking_validation.py` from `/api/v1/tracking/...` to `/tracking/...`.
### Out of Scope
No router changes. No `main.py` changes. No other test files.
## Capabilities
### New Capabilities
None.
### Modified Capabilities
None.
## Approach
Simple string replacement in 3 test assertions. The tracking router intentionally mounts at `/tracking` (no `/api/v1` prefix) for clean public URLs.
## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `backend/tests/unit/test_tracking_validation.py` | Low | Update path string in tests to match actual route. |
## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Path mistyped | Low | Standard code review. |
## Rollback Plan
`git revert` or discard the test file changes.
## Dependencies
None.
## Success Criteria
- [ ] All 3 tests pass: `test_invalid_tracking_token_returns_422`, `test_invalid_tracking_token_approve_returns_422`, `test_invalid_tracking_token_reject_returns_422`.
