import { useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import LandingLayout from "../features/landing/LandingLayout";
import LandingHero from "../features/landing/components/LandingHero";
import LandingPainRelief from "../features/landing/components/LandingPainRelief";
import LandingWorkflowDemo from "../features/landing/components/LandingWorkflowDemo";
import LandingOhm from "../features/landing/components/LandingOhm";
import LandingQualitativeResults from "../features/landing/components/LandingQualitativeResults";
import LandingPilotProgram from "../features/landing/components/LandingPilotProgram";
import LandingContactForm from "../features/landing/components/LandingContactForm";
import LandingToastProvider from "../features/landing/components/LandingToastProvider";
import { usePilotToastTrigger } from "../features/landing/hooks/usePilotToastTrigger";
import "../features/landing/landing.css";

export default function LandingPage() {
  const { theme, setTheme } = useTheme();

  // Activa el gatillo híbrido de intención para el toast del piloto
  usePilotToastTrigger();

  useEffect(() => {
    // 1. Forzar modo claro por defecto al abrir la landing page
    if (setTheme && theme !== "light") {
      setTheme("light");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      document.documentElement.style.colorScheme = "light";
    }

    // 2. Título descriptivo para la landing
    const previousTitle = document.title;
    document.title = "TecniDesk — Sistema para Talleres de Reparación Tecnológica | Piloto Guayaquil & Santa Elena";

    // Scroll al inicio al navegar
    window.scrollTo(0, 0);

    return () => {
      document.title = previousTitle;
    };
  }, []);

  return (
    <LandingLayout>
      {/* 1. Hero con propuesta y $0 primer mes */}
      <LandingHero />
      {/* 2. Problemas reales del taller & Transformación operativa */}
      <LandingPainRelief />
      {/* 3. Demostración interactiva del Workbench (id="workbench") */}
      <LandingWorkflowDemo />
      {/* 4. Ohm: Copiloto de diagnóstico de taller (id="ohm") */}
      <LandingOhm />
      {/* 5. Beneficios operativos cualitativos y acompañamiento */}
      <LandingQualitativeResults />
      {/* 6. Estructura comercial del Programa Piloto (id="piloto") */}
      <LandingPilotProgram />
      {/* 7. Formulario de postulación con WhatsApp directo (id="postular") */}
      <LandingContactForm />
      {/* 8. Notificación Toast Sileo con estética Workbench */}
      <LandingToastProvider />
    </LandingLayout>
  );
}
