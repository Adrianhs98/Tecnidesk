import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import LoginPage from "./pages/LoginPage";
import { ThemeProvider } from "./context/ThemeContext";
import { describe, it, expect } from "vitest";

/**
 * Smoke test through the real App entry graph (BrowserRouter, QueryClient,
 * ThemeProvider, Suspense/lazy). HomePage renders static copy and performs NO
 * network/fetch on load, so the assertion below is deterministic.
 *
 * NEVER depend on network responses in this suite: the app must render its
 * stable static copy without touching the backend.
 */
describe("App smoke test", () => {
  it("renders the stable HomePage copy at /", async () => {
    render(<App />);
    // Static HomePage label at route "/" — no fetch involved.
    expect(await screen.findByText("Codigo de rastreo")).toBeInTheDocument();
  });

  /**
   * Fallback: if rendering the FULL <App /> tree becomes flaky under jsdom
   * (e.g. Suspense/lazy instability), render the leaf LoginPage inside a
   * MemoryRouter at /login instead (LoginPage uses useNavigate, so it needs
   * router context; it also renders ThemeToggle, so ThemeProvider is required)
   * and assert its static copy "Panel de Control".
   */
  it("renders LoginPage static copy via MemoryRouter fallback", () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={["/login"]}>
          <LoginPage />
        </MemoryRouter>
      </ThemeProvider>
    );
    expect(screen.getByRole("heading", { name: "Panel de Control" })).toBeInTheDocument();
  });
});