# Spec: Domain Migration

## Overview
Change the main production domain from `adriansaas.xyz` to `tecnidesk.lat`.

## Changes
1. **CORS Policy (`backend/app/main.py`)**:
   - Original: `r"^https://(.*\.+)?adriansaas\.xyz$"`
   - New: `r"^https://(.*\.+)?(tecnidesk\.lat|adriansaas\.xyz)$"`
   - Rationale: Supporting both temporarily ensures no disruption for users transitioning, while making `tecnidesk.lat` a fully authorized origin.
2. **Documentation (`PROJECT_STATE.md`)**:
   - Update mentions of the old domain to reflect the new `tecnidesk.lat` domain.
