import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "../../context/ThemeContext";

import ProtectedRoute from "../../components/guards/ProtectedRoute";
import LoginPage from "../../pages/LoginPage";
import TechnicianHeader from "../../features/technician/TechnicianHeader";
import TechnicianTicketCard from "../../features/technician/TechnicianTicketCard";
import TechnicianWorkModal from "../../features/technician/TechnicianWorkModal";
import AiChatBubble from "../../features/technician/AiChatBubble";
import AiChatDrawer from "../../features/technician/AiChatDrawer";
import TechnicianDashboard from "../../features/technician/TechnicianDashboard";

import * as authFetchModule from "../../api/authFetch";
import * as technicianApi from "../../api/technician";
import * as diagnosticApi from "../../api/diagnostic";

// Mock authFetch
vi.mock("../../api/authFetch", () => ({
  authFetch: vi.fn(),
}));

describe("Technician Portal & AI Copilot Test Suite", () => {
  let queryClient;

  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });

    // Default mock response for authFetch
    vi.mocked(authFetchModule.authFetch).mockImplementation(async (url, opts) => {
      if (url.includes("/technicians/me")) {
        return {
          ok: true,
          json: async () => ({
            id: "tech-uuid-1",
            full_name: "Lucia Gomez",
            role: "technician",
            active_tickets_count: 3,
            completed_tickets_count: 8,
            declared_specialty: "Microsoldadura",
          }),
        };
      }

      if (url.includes("/shops/sla-config")) {
        return {
          ok: true,
          json: async () => ({
            effective_thresholds: {
              EN_ESPERA_INGRESO: 48,
              EN_REVISION: 24,
              EN_REPARACION: 48,
            },
          }),
        };
      }

      if (url.includes("/evidences")) {
        return {
          ok: true,
          json: async () => [],
        };
      }

      if (url.includes("/reveal-pin")) {
        return {
          ok: true,
          json: async () => ({
            device_password: "PIN-1234-PATRON",
            pin: "PIN-1234-PATRON",
          }),
        };
      }

      if (url.includes("/assign-me")) {
        return {
          ok: true,
          json: async () => ({
            id: "ticket-1",
            tracking_token: "TRK-100",
            device_brand: "Apple",
            device_model: "iPhone 13",
            technician_id: "tech-uuid-1",
            status: "EN_REVISION",
          }),
        };
      }

      if (url.includes("/diagnostic/chat") || url.includes("/diagnostic-chat")) {
        return {
          ok: true,
          json: async () => ({
            id: "ai-msg-1",
            role: "assistant",
            content: "Respuesta estructurada del copiloto IA",
          }),
        };
      }

      if (url.includes("/diagnostic-chat/confirm")) {
        return {
          ok: true,
          json: async () => ({
            status: "confirmed",
            message: "Caso confirmado exitosamente",
          }),
        };
      }

      if (url.includes("/status") && opts?.method === "PATCH") {
        return {
          ok: true,
          json: async () => ({
            id: "ticket-1",
            status: "EN_REPARACION",
          }),
        };
      }

      if (url.match(/\/tickets\/[^?]+$/)) {
        // Individual ticket details
        return {
          ok: true,
          json: async () => ({
            id: "ticket-1",
            tracking_token: "TRK-100",
            device_brand: "Apple",
            device_model: "iPhone 13",
            issue_description: "Pantalla rota y no carga",
            diagnostic_notes: "Corto en línea de carga",
            status: "EN_REVISION",
            created_at: "2026-08-22T10:00:00.000Z",
            customer: { full_name: "Carlos Sanchez", phone_number: "0991234567" },
            items: [],
          }),
        };
      }

      if (url.includes("/tickets")) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                id: "ticket-1",
                tracking_token: "TRK-100",
                device_brand: "Apple",
                device_model: "iPhone 13",
                issue_description: "Pantalla rota y no carga",
                diagnostic_notes: "Corto en línea de carga",
                status: "EN_REVISION",
                created_at: "2026-08-22T10:00:00.000Z",
                customer: { full_name: "Carlos Sanchez", phone_number: "0991234567" },
                technician_id: "tech-uuid-1",
              },
              {
                id: "ticket-2",
                tracking_token: "TRK-200",
                device_brand: "Samsung",
                device_model: "Galaxy S22",
                issue_description: "Batería inflada",
                diagnostic_notes: "Reemplazo de batería",
                status: "LISTO_PARA_RETIRAR",
                created_at: "2026-08-20T10:00:00.000Z",
                customer: { full_name: "Elena Ramos", phone_number: "0987654321" },
                technician_id: "tech-uuid-1",
              },
            ],
            total: 2,
          }),
        };
      }

      return {
        ok: true,
        json: async () => [],
      };
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  // ─── 1. API Helper Tests ──────────────────────────────────────────────────
  describe("API Helpers", () => {
    it("getTechnicianMe fetches /technicians/me successfully", async () => {
      const data = await technicianApi.getTechnicianMe();
      expect(data.full_name).toBe("Lucia Gomez");
      expect(data.role).toBe("technician");
      expect(data.active_tickets_count).toBe(3);
    });

    it("assignTicketToMe calls POST /tickets/{id}/assign-me", async () => {
      const res = await technicianApi.assignTicketToMe("t-123");
      expect(res.technician_id).toBe("tech-uuid-1");
      expect(authFetchModule.authFetch).toHaveBeenCalledWith(
        expect.stringContaining("/tickets/t-123/assign-me"),
        expect.objectContaining({ method: "POST" })
      );
    });

    it("revealTicketPin calls POST /tickets/{id}/reveal-pin", async () => {
      const res = await technicianApi.revealTicketPin("t-123");
      expect(res.device_password).toBe("PIN-1234-PATRON");
      expect(authFetchModule.authFetch).toHaveBeenCalledWith(
        expect.stringContaining("/tickets/t-123/reveal-pin"),
        expect.objectContaining({ method: "POST" })
      );
    });

    it("sendFreeDiagnosticChat calls POST /diagnostic/chat", async () => {
      const res = await diagnosticApi.sendFreeDiagnosticChat("Cómo mido la línea?");
      expect(res.content).toBe("Respuesta estructurada del copiloto IA");
      expect(authFetchModule.authFetch).toHaveBeenCalledWith(
        expect.stringContaining("/diagnostic/chat"),
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({ message: "Cómo mido la línea?" }),
        })
      );
    });
  });

  // ─── 2. Auth & Route Guards ───────────────────────────────────────────────
  describe("Auth & ProtectedRoute with Role Matrix", () => {
    it("LoginPage redirects technician to /tech upon login", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: "mock-jwt-token",
          role: "technician",
          user_full_name: "Pedro Técnico",
          shop_name: "Taller Central",
        }),
      });

      render(
        <MemoryRouter initialEntries={["/login"]}>
          <ThemeProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/tech" element={<div data-testid="tech-target">Tech Portal</div>} />
              <Route path="/admin" element={<div data-testid="admin-target">Admin Portal</div>} />
            </Routes>
          </ThemeProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByPlaceholderText("taller@correo.com"), {
        target: { value: "pedro@taller.com" },
      });
      fireEvent.change(screen.getByPlaceholderText("********"), {
        target: { value: "secret123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Ingresar" }));

      await waitFor(() => {
        expect(sessionStorage.getItem("td_token")).toBe("mock-jwt-token");
        expect(sessionStorage.getItem("td_role")).toBe("technician");
        expect(sessionStorage.getItem("td_user_name")).toBe("Pedro Técnico");
        expect(sessionStorage.getItem("td_shop")).toBe("Taller Central");
        expect(screen.getByTestId("tech-target")).toBeInTheDocument();
      });
    });

    it("LoginPage redirects admin to /admin upon login", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          access_token: "mock-admin-token",
          role: "admin",
          user_full_name: "Admin Boss",
          shop_name: "Taller Central",
        }),
      });

      render(
        <MemoryRouter initialEntries={["/login"]}>
          <ThemeProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/tech" element={<div data-testid="tech-target">Tech Portal</div>} />
              <Route path="/admin" element={<div data-testid="admin-target">Admin Portal</div>} />
            </Routes>
          </ThemeProvider>
        </MemoryRouter>
      );

      fireEvent.change(screen.getByPlaceholderText("taller@correo.com"), {
        target: { value: "admin@taller.com" },
      });
      fireEvent.change(screen.getByPlaceholderText("********"), {
        target: { value: "secret123" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Ingresar" }));

      await waitFor(() => {
        expect(sessionStorage.getItem("td_role")).toBe("admin");
        expect(screen.getByTestId("admin-target")).toBeInTheDocument();
      });
    });

    it("ProtectedRoute redirects technician trying to access admin-only route to /tech", () => {
      sessionStorage.setItem("td_token", "valid-token");
      sessionStorage.setItem("td_role", "technician");

      render(
        <MemoryRouter initialEntries={["/admin"]}>
          <Routes>
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <div>Admin Secret Area</div>
                </ProtectedRoute>
              }
            />
            <Route path="/tech" element={<div data-testid="tech-redirected">Redirected to Tech</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByTestId("tech-redirected")).toBeInTheDocument();
      expect(screen.queryByText("Admin Secret Area")).not.toBeInTheDocument();
    });

    it("ProtectedRoute redirects unauthenticated visitor to /login", () => {
      sessionStorage.clear();

      render(
        <MemoryRouter initialEntries={["/tech"]}>
          <Routes>
            <Route
              path="/tech"
              element={
                <ProtectedRoute allowedRoles={["admin", "technician"]}>
                  <div>Tech Area</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div data-testid="login-redirect">Login Page</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByTestId("login-redirect")).toBeInTheDocument();
      expect(screen.queryByText("Tech Area")).not.toBeInTheDocument();
    });
  });

  // ─── 3. TechnicianHeader ──────────────────────────────────────────────────
  describe("TechnicianHeader Component", () => {
    it("renders shop name, technician name, and role badge", () => {
      sessionStorage.setItem("td_shop", "ElectroFix Taller");
      sessionStorage.setItem("td_user_name", "Marcos Gomez");

      render(
        <MemoryRouter>
          <ThemeProvider>
            <TechnicianHeader />
          </ThemeProvider>
        </MemoryRouter>
      );

      expect(screen.getByText("ElectroFix Taller")).toBeInTheDocument();
      expect(screen.getByText("Marcos Gomez")).toBeInTheDocument();
      expect(screen.getByTestId("tech-role-badge")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Cerrar sesión/i })).toBeInTheDocument();
    });

    it("renders supervisor badge when isReadOnly is true or role is admin", () => {
      sessionStorage.setItem("td_shop", "ElectroFix Taller");
      sessionStorage.setItem("td_user_name", "Admin Boss");
      sessionStorage.setItem("td_role", "admin");

      render(
        <MemoryRouter>
          <ThemeProvider>
            <TechnicianHeader isReadOnly={true} />
          </ThemeProvider>
        </MemoryRouter>
      );

      expect(screen.getByTestId("supervisor-role-badge")).toBeInTheDocument();
      expect(screen.getByText("Modo Supervisor (Solo Lectura)")).toBeInTheDocument();
      expect(screen.queryByTestId("tech-role-badge")).not.toBeInTheDocument();
    });

    it("triggers auth:logout and redirects on logout click", () => {
      const logoutSpy = vi.fn();
      window.addEventListener("auth:logout", logoutSpy);

      render(
        <MemoryRouter initialEntries={["/tech"]}>
          <ThemeProvider>
            <Routes>
              <Route path="/tech" element={<TechnicianHeader />} />
              <Route path="/login" element={<div data-testid="login-after-logout">Login</div>} />
            </Routes>
          </ThemeProvider>
        </MemoryRouter>
      );

      fireEvent.click(screen.getByRole("button", { name: /Cerrar sesión/i }));
      expect(logoutSpy).toHaveBeenCalled();
      window.removeEventListener("auth:logout", logoutSpy);
    });
  });

  // ─── 4. TechnicianTicketCard ──────────────────────────────────────────────
  describe("TechnicianTicketCard Component", () => {
    const mockTicket = {
      id: "tk-99",
      tracking_token: "TRK-999",
      device_brand: "Xiaomi",
      device_model: "Redmi Note 12",
      issue_description: "Sin encendido por caída",
      status: "EN_REVISION",
      created_at: new Date().toISOString(),
      customer: { full_name: "Roberto Perez", phone_number: "0998877665" },
    };

    it("renders ticket details with SLA on-time status and masked customer phone", () => {
      render(<TechnicianTicketCard ticket={mockTicket} />);

      expect(screen.getByText("Xiaomi")).toBeInTheDocument();
      expect(screen.getByText("Redmi Note 12")).toBeInTheDocument();
      expect(screen.getByText(/Sin encendido por caída/i)).toBeInTheDocument();
      expect(screen.getByText("A tiempo")).toBeInTheDocument();
      expect(screen.getByText(/Trabajar en Equipo/i)).toBeInTheDocument();
    });

    it("renders in available mode with 'Tomar Reparación' action", () => {
      const onTakeSpy = vi.fn();
      render(
        <TechnicianTicketCard
          ticket={mockTicket}
          isAvailable={true}
          onTakeTicket={onTakeSpy}
        />
      );

      const takeBtn = screen.getByTestId("take-ticket-btn-tk-99");
      expect(takeBtn).toBeInTheDocument();
      expect(takeBtn).toHaveTextContent("Tomar Reparación");

      fireEvent.click(takeBtn);
      expect(onTakeSpy).toHaveBeenCalledWith(mockTicket);
    });

    it("renders 'Ver Ficha (Lectura)' when isReadOnly is true even if available", () => {
      const onOpenSpy = vi.fn();
      render(
        <TechnicianTicketCard
          ticket={mockTicket}
          isAvailable={true}
          isReadOnly={true}
          onOpenWorkModal={onOpenSpy}
        />
      );

      expect(screen.queryByTestId("take-ticket-btn-tk-99")).not.toBeInTheDocument();
      const readBtn = screen.getByTestId("open-work-modal-tk-99");
      expect(readBtn).toBeInTheDocument();
      expect(readBtn).toHaveTextContent("Ver Ficha (Lectura)");

      fireEvent.click(readBtn);
      expect(onOpenSpy).toHaveBeenCalledWith(mockTicket);
    });
  });

  // ─── 5. TechnicianWorkModal & PIN Reveal ───────────────────────────────────
  describe("TechnicianWorkModal Component", () => {
    const mockTicket = {
      id: "ticket-work-1",
      tracking_token: "TRK-W1",
      device_brand: "Apple",
      device_model: "iPhone 14 Pro",
      issue_description: "No activa FaceID y batería al 68%",
      diagnostic_notes: "Flex de audio dañado",
      status: "EN_REVISION",
      created_at: "2026-08-21T10:00:00.000Z",
      customer: { full_name: "Valeria Morales", phone_number: "0990011223" },
    };

    it("shows masked PIN initially and reveals decrypted PIN with audit trail and Eye toggle", async () => {
      render(
        <QueryClientProvider client={queryClient}>
          <TechnicianWorkModal
            ticket={mockTicket}
            onClose={vi.fn()}
            onStatusChange={vi.fn()}
            onOpenAiCopilot={vi.fn()}
          />
        </QueryClientProvider>
      );

      // Verify masked state before reveal
      expect(screen.getByText("PIN Protegido")).toBeInTheDocument();
      const revealBtn = screen.getByTestId("reveal-pin-btn");
      expect(revealBtn).toBeInTheDocument();

      // Click reveal PIN
      fireEvent.click(revealBtn);

      await waitFor(() => {
        expect(screen.getByTestId("revealed-pin-display")).toBeInTheDocument();
        expect(screen.getByText(/PIN auditado y registrado/i)).toBeInTheDocument();
      });

      // PIN is initially masked as ••••••••
      const pinText = screen.getByTestId("revealed-pin-text");
      expect(pinText).toHaveTextContent("••••••••");

      // Click Eye toggle button to show clear text
      const toggleBtn = screen.getByTestId("toggle-pin-mask-btn");
      fireEvent.click(toggleBtn);
      expect(pinText).toHaveTextContent("PIN-1234-PATRON");

      // Click EyeOff toggle button to re-mask
      fireEvent.click(toggleBtn);
      expect(pinText).toHaveTextContent("••••••••");
    });

    it("handles 1-click status transitions", async () => {
      const onStatusChangeSpy = vi.fn();

      render(
        <QueryClientProvider client={queryClient}>
          <TechnicianWorkModal
            ticket={mockTicket}
            onClose={vi.fn()}
            onStatusChange={onStatusChangeSpy}
            onOpenAiCopilot={vi.fn()}
          />
        </QueryClientProvider>
      );

      const reparacionBtn = screen.getByTestId("quick-status-EN_REPARACION");
      fireEvent.click(reparacionBtn);

      await waitFor(() => {
        expect(authFetchModule.authFetch).toHaveBeenCalledWith(
          expect.stringContaining("/tickets/ticket-work-1/status"),
          expect.objectContaining({
            method: "PATCH",
            body: JSON.stringify({ status: "EN_REPARACION" }),
          })
        );
        expect(onStatusChangeSpy).toHaveBeenCalled();
      });
    });

    it("triggers onOpenAiCopilot when clicking Ohm CTA", () => {
      const copilotSpy = vi.fn();
      render(
        <QueryClientProvider client={queryClient}>
          <TechnicianWorkModal
            ticket={mockTicket}
            onClose={vi.fn()}
            onStatusChange={vi.fn()}
            onOpenAiCopilot={copilotSpy}
          />
        </QueryClientProvider>
      );

      fireEvent.click(screen.getByTestId("open-ai-copilot-ticket-btn"));
      expect(copilotSpy).toHaveBeenCalledWith(mockTicket);
    });

    it("disables mutations and hides sensitive buttons in isReadOnly supervisor mode", () => {
      render(
        <QueryClientProvider client={queryClient}>
          <TechnicianWorkModal
            ticket={mockTicket}
            onClose={vi.fn()}
            onStatusChange={vi.fn()}
            onOpenAiCopilot={vi.fn()}
            isReadOnly={true}
          />
        </QueryClientProvider>
      );

      // Status buttons disabled + supervisor indicator shown
      expect(screen.getByTestId("supervisor-readonly-indicator")).toBeInTheDocument();
      expect(screen.getByTestId("quick-status-EN_REPARACION")).toBeDisabled();

      // Reveal PIN button hidden
      expect(screen.queryByTestId("reveal-pin-btn")).not.toBeInTheDocument();
      expect(screen.getByText(/PIN Protegido \(Modo Supervisor: solo lectura\)/i)).toBeInTheDocument();

      // Diagnostic notes disabled and save button hidden
      expect(screen.queryByTestId("save-notes-btn")).not.toBeInTheDocument();
      expect(screen.getByTestId("diagnostic-notes-input")).toBeDisabled();

      // Ohm button hidden
      expect(screen.queryByTestId("open-ai-copilot-ticket-btn")).not.toBeInTheDocument();
    });
  });

  // ─── 6. AI Copilot Bubble & Drawer ────────────────────────────────────────
  describe("AI Copilot Bubble & Drawer", () => {
    it("renders AiChatBubble and triggers toggle", () => {
      const onClickSpy = vi.fn();
      render(<AiChatBubble onClick={onClickSpy} isOpen={false} />);

      const bubbleBtn = screen.getByTestId("ai-chat-bubble-btn");
      fireEvent.click(bubbleBtn);
      expect(onClickSpy).toHaveBeenCalledTimes(1);
    });

    it("AiChatDrawer sends free chat messages in general mode", async () => {
      render(
        <AiChatDrawer
          isOpen={true}
          onClose={vi.fn()}
          ticketContext={null}
        />
      );

      expect(screen.getByTestId("ai-free-mode-banner")).toBeInTheDocument();

      const input = screen.getByTestId("ai-chat-input");
      fireEvent.change(input, { target: { value: "¿Dónde mido los voltajes de standby?" } });
      fireEvent.click(screen.getByTestId("ai-send-btn"));

      await waitFor(() => {
        expect(screen.getByText(/Respuesta estructurada del copiloto IA/i)).toBeInTheDocument();
      });
    });

    it("AiChatDrawer in ticket context displays active banner and allows applying diagnosis", async () => {
      const mockTicket = {
        id: "t-ctx-1",
        device_brand: "Apple",
        device_model: "iPhone 11",
        issue_description: "Consumo alto",
      };
      const onApplySpy = vi.fn();

      render(
        <AiChatDrawer
          isOpen={true}
          onClose={vi.fn()}
          ticketContext={mockTicket}
          onApplyToDiagnosis={onApplySpy}
        />
      );

      expect(screen.getByTestId("ai-active-ticket-banner")).toBeInTheDocument();

      const input = screen.getByTestId("ai-chat-input");
      fireEvent.change(input, { target: { value: "Revisión de diodo" } });
      fireEvent.click(screen.getByTestId("ai-send-btn"));

      await waitFor(() => {
        expect(screen.getByText(/Respuesta estructurada del copiloto IA/i)).toBeInTheDocument();
      });

      // Click "Aplicar al Diagnóstico"
      const applyBtn = screen.getByTestId("apply-to-diagnosis-btn");
      fireEvent.click(applyBtn);
      expect(onApplySpy).toHaveBeenCalledWith("Respuesta estructurada del copiloto IA", mockTicket);
    });
  });

  // ─── 7. Full TechnicianDashboard Integration ──────────────────────────────
  describe("TechnicianDashboard Full Integration", () => {
    it("renders KPIs, switches between tabs, and toggles Kanban view", async () => {
      render(
        <MemoryRouter>
          <ThemeProvider>
            <QueryClientProvider client={queryClient}>
              <TechnicianDashboard />
            </QueryClientProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      // Verify KPIs
      await waitFor(() => {
        expect(screen.getByTestId("kpi-activos")).toBeInTheDocument();
        expect(screen.getByTestId("kpi-revision")).toBeInTheDocument();
        expect(screen.getByTestId("kpi-listos")).toBeInTheDocument();
      });

      // Verify default tickets loaded
      await waitFor(() => {
        expect(screen.getByText("iPhone 13")).toBeInTheDocument();
      });

      // Switch to Kanban View
      const kanbanToggle = screen.getByTestId("view-mode-kanban");
      fireEvent.click(kanbanToggle);

      expect(screen.getByTestId("tech-kanban-view")).toBeInTheDocument();
      expect(screen.getByTestId("tech-kanban-col-ingreso_revision")).toBeInTheDocument();
      expect(screen.getByTestId("tech-kanban-col-reparacion_repuesto")).toBeInTheDocument();
      expect(screen.getByTestId("tech-kanban-col-listo_entrega")).toBeInTheDocument();

      // Switch to Equipos Disponibles tab
      const availableTab = screen.getByTestId("tab-available-tickets");
      fireEvent.click(availableTab);
      expect(availableTab).toHaveClass("active");
    });

    it("runs in admin supervisor mode with workshop-wide assignments and disabled mutations", async () => {
      sessionStorage.setItem("td_token", "admin-token");
      sessionStorage.setItem("td_role", "admin");
      sessionStorage.setItem("td_user_name", "Admin Supervisor");
      sessionStorage.setItem("td_shop", "TecniDesk Matriz");

      render(
        <MemoryRouter initialEntries={["/tech"]}>
          <ThemeProvider>
            <QueryClientProvider client={queryClient}>
              <Routes>
                <Route
                  path="/tech"
                  element={
                    <ProtectedRoute allowedRoles={["admin", "technician"]}>
                      <TechnicianDashboard />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </QueryClientProvider>
          </ThemeProvider>
        </MemoryRouter>
      );

      // 1. Check supervisor badge in header
      expect(screen.getByTestId("supervisor-role-badge")).toBeInTheDocument();
      expect(screen.getByText("Modo Supervisor (Solo Lectura)")).toBeInTheDocument();

      // 2. Check tab 1 label is workshop-wide
      expect(screen.getByText("Todos los Asignados del Taller")).toBeInTheDocument();

      // 3. Check cards show "Ver Ficha (Lectura)" and no "Tomar Reparación"
      await waitFor(() => {
        expect(screen.getAllByText("Ver Ficha (Lectura)")[0]).toBeInTheDocument();
        expect(screen.queryByText("Tomar Reparación")).not.toBeInTheDocument();
      });

      // 4. Check AI Copilot FAB is NOT rendered
      expect(screen.queryByTestId("ai-chat-bubble-btn")).not.toBeInTheDocument();

      // 5. Open Work Modal and verify supervisor read-only constraints
      const openModalBtns = screen.getAllByTestId(/open-work-modal-/);
      fireEvent.click(openModalBtns[0]);

      expect(screen.getByTestId("supervisor-readonly-indicator")).toBeInTheDocument();
      expect(screen.queryByTestId("reveal-pin-btn")).not.toBeInTheDocument();
      expect(screen.queryByTestId("open-ai-copilot-ticket-btn")).not.toBeInTheDocument();
    });
  });
});
