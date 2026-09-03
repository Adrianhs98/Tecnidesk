import '@testing-library/jest-dom/vitest';

// jsdom does not implement window.localStorage in a way tests can rely on;
// provide a deterministic in-memory mock.
const storage: Record<string, string> = {};
const localStorageMock = {
  getItem: (key: string) => (key in storage ? storage[key] : null),
  setItem: (key: string, value: string) => {
    storage[key] = String(value);
  },
  removeItem: (key: string) => {
    delete storage[key];
  },
  clear: () => {
    Object.keys(storage).forEach((k) => delete storage[k]);
  },
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});
if (typeof globalThis !== 'undefined') {
  (globalThis as any).localStorage = localStorageMock;
}

// jsdom does not implement window.matchMedia. ThemeContext's getInitialTheme()
// calls it at mount time, so provide a deterministic stub for the test env.
Object.defineProperty(window, 'matchMedia', {
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
