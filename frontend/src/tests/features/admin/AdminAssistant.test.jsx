import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";

import AiChatDrawer from "../../../features/technician/AiChatDrawer";
import * as adminAssistantApi from "../../../api/adminAssistant";
import * as diagnosticApi from "../../../api/diagnostic";

vi.mock("../../../api/adminAssistant", () => ({
  sendAdminAssistantQuery: vi.fn(),
}));

vi.mock("../../../api/diagnostic", () => ({
  sendDiagnosticChat: vi.fn(),
  sendFreeDiagnosticChat: vi.fn(),
  getDiagnosticChatHistory: vi.fn(),
  confirmCorrection: vi.fn(),
}));

describe("Ohm Admin Assistant Frontend Suite", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(adminAssistantApi.sendAdminAssistantQuery).mockResolvedValue({
      reply: "Hoy se han recaudado **$340.00 USD** en reparaciones listas para retirar.",
      intent: "ganancias_del_dia",
      data: { total_revenue: 340.0, completed_count: 4 },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders admin branding, admin banner, and 3 quick chips when context='admin'", () => {
    render(
      <AiChatDrawer
        isOpen={true}
        onClose={vi.fn()}
        context="admin"
      />
    );

    // Header & Subtitle
    expect(screen.getByRole("heading", { level: 3, name: "Ohm" })).toBeInTheDocument();
    expect(
      screen.getByText("Gemini 3.5 Flash Lite • Gestión & Métricas del Taller")
    ).toBeInTheDocument();

    // Admin Context Banner
    expect(screen.getByTestId("ai-admin-mode-banner")).toBeInTheDocument();
    expect(
      screen.getByText(/Panel de Gestión • Métricas Operativas en Tiempo Real/i)
    ).toBeInTheDocument();

    // Welcome message
    expect(
      screen.getByText(/tu asistente de gestión/i)
    ).toBeInTheDocument();

    // 3 Admin Quick Chips
    expect(screen.getByTestId("admin-chip-revenue")).toHaveTextContent("💰 Ganancias de hoy");
    expect(screen.getByTestId("admin-chip-intake")).toHaveTextContent("📥 Equipos ingresados hoy");
    expect(screen.getByTestId("admin-chip-untouched")).toHaveTextContent("⏱️ Equipos sin tocar");

    // Ensure technician RAG / Diagnostic controls are hidden
    expect(screen.queryByTestId("confirm-rag-btn")).not.toBeInTheDocument();
    expect(screen.queryByTestId("ai-free-mode-banner")).not.toBeInTheDocument();
  });

  it("clicking an admin quick chip calls sendAdminAssistantQuery and displays reply", async () => {
    render(
      <AiChatDrawer
        isOpen={true}
        onClose={vi.fn()}
        context="admin"
      />
    );

    const revenueChip = screen.getByTestId("admin-chip-revenue");
    fireEvent.click(revenueChip);

    await waitFor(() => {
      expect(adminAssistantApi.sendAdminAssistantQuery).toHaveBeenCalledWith("Ganancias de hoy");
      expect(diagnosticApi.sendDiagnosticChat).not.toHaveBeenCalled();
      expect(diagnosticApi.sendFreeDiagnosticChat).not.toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Hoy se han recaudado/i)
      ).toBeInTheDocument();
    });
  });

  it("submitting free text in admin mode calls sendAdminAssistantQuery", async () => {
    vi.mocked(adminAssistantApi.sendAdminAssistantQuery).mockResolvedValueOnce({
      reply: "Hay **2** equipos activos que llevan más de 48 horas sin registrar cambios.",
      intent: "equipos_sin_tocar",
      data: { stale_count: 2 },
    });

    render(
      <AiChatDrawer
        isOpen={true}
        onClose={vi.fn()}
        context="admin"
      />
    );

    const textarea = screen.getByTestId("ai-chat-input");
    fireEvent.change(textarea, { target: { value: "¿Cuáles son los tickets estancados?" } });

    const sendBtn = screen.getByTestId("ai-send-btn");
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(adminAssistantApi.sendAdminAssistantQuery).toHaveBeenCalledWith("¿Cuáles son los tickets estancados?");
    });

    await waitFor(() => {
      expect(
        screen.getByText(/Hay/i)
      ).toBeInTheDocument();
      expect(
        screen.getByText(/sin registrar cambios/i)
      ).toBeInTheDocument();
    });
  });
});
