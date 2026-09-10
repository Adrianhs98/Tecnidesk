import { useEffect } from "react";
import { useTheme } from "../context/ThemeContext";
import LandingLayout from "../features/landing/LandingLayout";
import LandingHero from "../features/landing/components/LandingHero";
import LandingPainRelief from "../features/landing/components/LandingPainRelief";
import LandingOhm from "../features/landing/components/LandingOhm";
import LandingFeatures from "../features/landing/components/LandingFeatures";
import LandingPilotProgram from "../features/landing/components/LandingPilotProgram";
import LandingContactForm from "../features/landing/components/LandingContactForm";
import "../features/landing/landing.css";

export default function LandingPage() {
  const { theme, setTheme } = useTheme();

  useEffect(() => {
    // 1. Forzar modo claro por defecto al abrir la landing page (Scope punto 3)
    if (setTheme && theme !== "light") {
      setTheme("light");
    } else {
      document.documentElement.setAttribute("data-theme", "light");
      document.documentElement.style.colorScheme = "light";
    }

    // 2. Establecer título descriptivo para la landing
    const previousTitle = document.title;
    document.title = "TecniDesk — Programa Piloto para Talleres | Guayaquil y Santa Elena";

    // Scroll to top upon navigation
    window.scrollTo(0, 0);

    return () => {
      document.title = previousTitle;
    };
  }, []);

  return (
    <LandingLayout>
      <LandingHero />
      <LandingPainRelief />
      <LandingOhm />
      <LandingFeatures />
      <LandingPilotProgram />
      <LandingContactForm />
    </LandingLayout>
  );
}
