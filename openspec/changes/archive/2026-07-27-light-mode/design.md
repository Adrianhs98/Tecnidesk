# Design: Theme Customization

## Architecture
- Introduce `ThemeContext` in React to manage and expose theme state.
- Set `data-theme` attribute on the root `<html>` element.
- Define CSS variables for dark and light modes under `:root` and `[data-theme="light"]`.

## Decisions
- **OKLCH Colors**: Use OKLCH color spaces for cohesive lightness and chroma changes.
- **LocalStorage**: Simple client-side persistence for preferences.
