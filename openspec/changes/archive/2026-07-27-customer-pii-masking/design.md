# Design: Customer PII Privacy

## Architecture
- Update `src/utils/privacy.js`: modify `maskPhone(phone)` to slice only the first 2 characters (`str.slice(0, 2)`) and fill the remainder with `"x".repeat(Math.max(2, str.length - 2))`.
- In `AdminTicketCard.jsx`:
  - Import `Eye` and `EyeOff` from `lucide-react`.
  - Add local component state: `const [showPii, setShowPii] = useState(false);`.
  - In the modal body customer details section, render masked values when `!showPii` and raw values when `showPii`.
  - Add a small toggle button next to the "Datos del Cliente" header calling `setShowPii(!showPii)`.

## Decisions
- **Local State in Card Component**: By keeping `showPii` in `AdminTicketCard`'s local React state, closing the modal or changing cards automatically resets visibility to `false`. This prevents accidental shoulder surfing from leaving data revealed permanently.
