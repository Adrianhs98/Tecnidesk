# Proposal: Sanitize WhatsApp Number in Public Endpoints

## Why
Currently, the public tracking endpoints return the shop's `contact_whatsapp` exactly as it was entered by the user (which may include spaces, hyphens, plus signs, parentheses, etc.). This makes it difficult for frontend clients to seamlessly construct direct `wa.me/` links without implementing redundant regex parsing on every client.

## What
Clean the `contact_whatsapp` string in the API layer before returning it in the public ticket response. We will strip out any non-numeric characters so the frontend receives a clean, digits-only string ready for WhatsApp links.

## Capabilities
- `whatsapp-sanitization`: Strips all non-digit characters from the shop's WhatsApp number in the public ticket tracking response.
