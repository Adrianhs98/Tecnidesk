# Proposal: Mask Customer PII on Dashboard Cards and Detail Modal

## Goal
Visually mask sensitive customer information (phone number and email address) on both the initial ticket card grid and inside the ticket detail modal by default, providing an interactive reveal toggle (eye button) in the modal for authorized technicians.

## Motivation
Workshop admin screens are frequently visible to waiting customers or visitors. Displaying raw PII at a glance creates a privacy and security risk. Masking them by default everywhere, while allowing technicians to reveal them on demand with a click when contacting a client, provides maximum privacy with zero friction.

## Capabilities
- `privacy`: Customer PII masking formatting rules and interactive reveal toggle in admin views.
