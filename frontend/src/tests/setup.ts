import "@testing-library/jest-dom/vitest";

// jsdom does not implement window.matchMedia. ThemeContext's getInitialTheme()
// calls it at mount time, so provide a deterministic stub for the test env.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
