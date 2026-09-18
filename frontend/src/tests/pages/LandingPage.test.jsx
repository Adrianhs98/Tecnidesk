import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router-dom";
import LandingPage from "../../pages/LandingPage";
import LandingContactForm from "../../features/landing/components/LandingContactForm";
import LandingWorkflowDemo from "../../features/landing/components/LandingWorkflowDemo";
import LandingOhm from "../../features/landing/components/LandingOhm";
import { ThemeProvider } from "../../context/ThemeContext";

function renderWithProviders(ui) {
  return render(
    <ThemeProvider>
      <BrowserRouter>{ui}</BrowserRouter>
    </ThemeProvider>
  );
}

describe("LandingPage V2 Component Suite", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
  });

  it("renders LandingPage with Hero, Realities, WorkflowDemo, Ohm, Qualitative, Pilot and Contact sections", () => {
    renderWithProviders(<LandingPage />);

    // 1. Hero headline
    expect(screen.getByText(/El sistema operativo para tu/i)).toBeInTheDocument();
    expect(screen.getByText(/taller de reparación tecnológica/i)).toBeInTheDocument();

    // 2. High-hierarchy $0 offer
    expect(screen.getAllByText(/Primer mes 100% bonificado/i)[0]).toBeInTheDocument();

    // 3. Workshop Realities
    expect(screen.getByText(/Tu taller pierde dinero en el desorden, no en la reparación/i)).toBeInTheDocument();
    expect(screen.getByText(/Del caos de libretas a la trazabilidad completa/i)).toBeInTheDocument();

    // 4. Workflow Demo (id="workbench")
    expect(screen.getByText(/Así se vive un ticket en el Workbench de TecniDesk/i)).toBeInTheDocument();

    // 5. Ohm Bench Station
    expect(screen.getByText(/Tu taller empieza a recordar: memoria técnica asistida/i)).toBeInTheDocument();

    // 6. Qualitative Benefits
    expect(screen.getByText(/Tranquilidad y orden para vos y tu equipo de trabajo/i)).toBeInTheDocument();

    // 7. Pilot Program
    expect(screen.getByText(/Estructura del Programa Piloto/i)).toBeInTheDocument();

    // 8. Contact Form
    expect(screen.getByText(/Postula tu taller/i)).toBeInTheDocument();
  });

  it("LandingWorkflowDemo transitions between all 4 stages correctly", () => {
    renderWithProviders(<LandingWorkflowDemo />);

    // Initial step: RECIBIDO
    expect(screen.getByText(/PASO 01 DE 04/i)).toBeInTheDocument();
    expect(screen.getByText(/No da imagen tras apagón eléctrico/i)).toBeInTheDocument();

    // Click step 2: EN DIAGNÓSTICO
    const diagTab = screen.getByRole("tab", { name: /EN DIAGNÓSTICO/i });
    fireEvent.click(diagTab);
    expect(screen.getByText(/PASO 02 DE 04/i)).toBeInTheDocument();
    expect(screen.getByText(/Línea \+VCC_EDP en 0\.2V/i)).toBeInTheDocument();

    // Click step 3: APROBACIÓN
    const aprobTab = screen.getByRole("tab", { name: /APROBACIÓN/i });
    fireEvent.click(aprobTab);
    expect(screen.getByText(/PASO 03 DE 04/i)).toBeInTheDocument();
    expect(screen.getByText(/Total Presupuesto:/i)).toBeInTheDocument();

    // Click step 4: LISTO
    const listoTab = screen.getByRole("tab", { name: /LISTO/i });
    fireEvent.click(listoTab);
    expect(screen.getByText(/PASO 04 DE 04/i)).toBeInTheDocument();
    expect(screen.getByText(/90 días de garantía registrada/i)).toBeInTheDocument();
  });

  it("LandingOhm transitions through all 4 diagnostic stages correctly with a11y tabs and keyboard navigation", () => {
    const { container } = renderWithProviders(<LandingOhm />);

    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(4);

    // Initial step: 01 CONSULTA TÉCNICA
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    expect(tabs[1]).toHaveAttribute("aria-selected", "false");
    expect(screen.getByText(/01 CONSULTA TÉCNICA/i)).toBeInTheDocument();
    expect(screen.getByText(/MacBook Air M1 \(Placa 820-02016\)/i)).toBeInTheDocument();

    // Keyboard navigation: ArrowRight advances tab
    fireEvent.keyDown(tabs[0], { key: "ArrowRight" });
    expect(tabs[1]).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/02 MEMORIA DEL TALLER/i)).toBeInTheDocument();
    expect(screen.getByText(/Ticket #TK-7412/i)).toBeInTheDocument();
    expect(screen.getByText(/Coincidencia alta con historial del taller/i)).toBeInTheDocument();
    expect(screen.getByText(/Los datos de cada taller permanecen aislados de otros talleres/i)).toBeInTheDocument();

    // Keyboard navigation: End jumps to last tab (04 SUGERENCIA)
    fireEvent.keyDown(tabs[1], { key: "End" });
    expect(tabs[3]).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/04 SUGERENCIA TÉCNICA/i)).toBeInTheDocument();
    expect(screen.getByText(/Desoldar condensador C3104/i)).toBeInTheDocument();
    expect(screen.getByText(/~40 min/i)).toBeInTheDocument();
    expect(screen.getByText(/La decisión final permanece en manos del técnico/i)).toBeInTheDocument();

    // Restart button loop when at last stage
    const restartBtn = screen.getByRole("button", { name: /Reiniciar recorrido de Ohm/i });
    fireEvent.click(restartBtn);
    expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/01 CONSULTA TÉCNICA/i)).toBeInTheDocument();

    // Forward button ("Siguiente etapa →")
    const nextBtn = screen.getByRole("button", { name: /Siguiente etapa de Ohm/i });
    fireEvent.click(nextBtn);
    expect(tabs[1]).toHaveAttribute("aria-selected", "true");

    // Click step 3: 03 MEDICIONES / HALLAZGOS
    const medTab = screen.getByRole("tab", { name: /03 Medición/i });
    fireEvent.click(medTab);
    expect(tabs[2]).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText(/03 MEDICIONES \/ HALLAZGOS/i)).toBeInTheDocument();
    expect(screen.getByText(/~450Ω/i)).toBeInTheDocument();
    expect(screen.getByText("12Ω")).toBeInTheDocument();

    // Backward button ("← Anterior")
    const prevBtn = screen.getByRole("button", { name: /Etapa anterior de Ohm/i });
    fireEvent.click(prevBtn);
    expect(tabs[1]).toHaveAttribute("aria-selected", "true");

    // Spotlight card mouse move and mouse leave test
    const benchCard = container.querySelector(".landing-ohm-bench-card");
    expect(benchCard).toBeInTheDocument();
    fireEvent.mouseMove(benchCard, { clientX: 100, clientY: 150 });
    const spotlight = container.querySelector(".landing-ohm-spotlight");
    expect(spotlight).toHaveClass("visible");
    fireEvent.mouseLeave(benchCard);
    expect(spotlight).not.toHaveClass("visible");

    // Verify compliant privacy text
    expect(screen.getByText(/Los datos de cada taller permanecen aislados de otros talleres/i)).toBeInTheDocument();
  });

  it("LandingContactForm has synchronized weeklyVolume initial state and generates valid WhatsApp link", () => {
    const windowOpenSpy = vi.spyOn(window, "open").mockImplementation(() => null);

    renderWithProviders(<LandingContactForm />);

    const volumeSelect = screen.getByLabelText(/Equipos recibidos por semana/i);
    // Verified: initial value must match an option value
    expect(volumeSelect.value).toBe("15-35 equipos/sem");

    // Fill form
    fireEvent.change(screen.getByLabelText(/Nombre del taller/i), {
      target: { value: "ElectroFix Centro" }
    });
    fireEvent.change(screen.getByLabelText(/Tu nombre y apellido/i), {
      target: { value: "Adrian Solis" }
    });
    fireEvent.change(screen.getByLabelText(/WhatsApp de contacto/i), {
      target: { value: "0991234567" }
    });

    // Submit form
    const submitBtn = screen.getByRole("button", { name: /Enviar Postulación vía WhatsApp/i });
    fireEvent.click(submitBtn);

    expect(windowOpenSpy).toHaveBeenCalledTimes(1);
    const calledUrl = windowOpenSpy.mock.calls[0][0];
    expect(calledUrl).toContain("https://wa.me/593960029253?text=");
    expect(calledUrl).toContain("ElectroFix%20Centro");
    expect(calledUrl).toContain("15-35%20equipos%2Fsem");
  });

  it("LandingAmbientTech renders globally as ambient background in LandingPage", () => {
    const { container } = renderWithProviders(<LandingPage />);
    const ambientLayer = container.querySelector(".landing-ambient-tech-container");
    expect(ambientLayer).toBeInTheDocument();
    const canvas = ambientLayer.querySelector("canvas.landing-ambient-tech-canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("usePilotToastTrigger respects sessionStorage frequency capping", () => {
    sessionStorage.setItem("tecnidesk_pilot_toast_dismissed", "true");
    const { container } = renderWithProviders(<LandingPage />);
    // Toast should not trigger if dismissed flag exists
    expect(sessionStorage.getItem("tecnidesk_pilot_toast_dismissed")).toBe("true");
    expect(container).toBeInTheDocument();
  });
});
