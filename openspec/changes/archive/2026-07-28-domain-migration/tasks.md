# Task List: Domain Migration to tecnidek.lat

- [x] 1. Update `backend/app/main.py`
  - Modify `_prod_regex` in CORS configuration to allow `tecnidesk.lat` (and keep `adriansaas.xyz` temporarily to avoid breaking existing users/redirections).
  - Regex suggestion: `r"^https://(.*\.+)?(tecnidesk\.lat|adriansaas\.xyz)$"`
- [x] 2. Update `PROJECT_STATE.md`
  - Update references from `adriansaas.xyz` to `tecnidesk.lat` in the documentation.
- [x] 3. Validate changes
  - Ensure backend starts correctly and regex is syntactically valid.
