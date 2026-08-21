# Verification Report: fix-activate-shop-idor

**Date**: 2026-07-29  
**Status**: PASSED  

---

## Compliance Matrix

| Spec Requirement | Scenario | Verdict | Evidence |
|---|---|---|---|
| Reject requests without platform key | Missing header returns 401 | COMPLIANT | `test_activate_shop_endpoint_missing_key_returns_401` PASSED |
| Reject requests with incorrect platform key | Wrong key returns 403 | COMPLIANT | `test_activate_shop_endpoint_invalid_key_returns_403` PASSED |
| Accept activation with correct platform key | Correct key activates shop | COMPLIANT | `test_superadmin_key_guard_valid_key` PASSED |
| Accept activation without tenant JWT | Correct key without tenant JWT | COMPLIANT | `superadmin_key_guard` does not depend on Bearer token |
| Reject valid tenant JWT without platform key | Valid JWT without platform key | COMPLIANT | Endpoint signature requires `superadmin_key_guard` |
| Prevent timing leaks in key comparison | Comparison uses secrets.compare_digest | COMPLIANT | Verified in `app/core/dependencies.py` line 208 |

---

## Test Execution Results

```text
tests\unit\test_activate_shop_guard.py ..... [100%]
5 passed in 0.04s
```
