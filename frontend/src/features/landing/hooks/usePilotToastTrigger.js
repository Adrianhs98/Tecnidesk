import { useEffect, useRef } from "react";
import { sileo } from "sileo";

/**
 * usePilotToastTrigger
 * Hook con gatillo híbrido de intención para el toast del Programa Piloto:
 * 1. Dwell Time >= 12s
 * 2. AND (Scroll Progress >= 65% OR Workbench superado)
 * 3. Previene disparo si el usuario está interactuando con campos de formulario (focus activo).
 * 4. Previene disparo si el formulario de postulación ya fue enviado.
 * 5. Frecuencia controlada por sessionStorage (anti-spam: 1 sola vez por sesión).
 * 6. Evita duplicaciones al entrar/salir de la zona mediante hasTriggeredRef.
 */
export function usePilotToastTrigger({
  minDwellSeconds = 12,
  minProgress = 0.65,
  targetSectionId = "postular",
} = {}) {
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Si ya fue mostrado o descartado en esta sesión, no hacer nada
    if (sessionStorage.getItem("tecnidesk_pilot_toast_dismissed") === "true") {
      return;
    }

    let isDwellMet = false;
    let dwellTimer = null;

    // 1. Temporizador de permanencia (Dwell Time >= 12s)
    dwellTimer = setTimeout(() => {
      isDwellMet = true;
      evaluateAndTrigger();
    }, minDwellSeconds * 1000);

    const isUserTyping = () => {
      const el = document.activeElement;
      if (!el) return false;
      const tag = el.tagName ? el.tagName.toLowerCase() : "";
      return (
        tag === "input" ||
        tag === "textarea" ||
        tag === "select" ||
        el.isContentEditable
      );
    };

    const isFormCompleted = () => {
      return sessionStorage.getItem("tecnidesk_pilot_form_submitted") === "true";
    };

    const isScrollProgressMet = () => {
      const scrollY = window.scrollY || window.pageYOffset || 0;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (docHeight <= 0) return false;
      const progress = scrollY / docHeight;
      return progress >= minProgress;
    };

    const isWorkbenchSuperado = () => {
      const wb = document.getElementById("workbench");
      if (!wb) return false;
      const rect = wb.getBoundingClientRect();
      // El Workbench se considera superado cuando su borde inferior ya pasó el tercio superior de la pantalla
      return rect.bottom < window.innerHeight * 0.4;
    };

    const evaluateAndTrigger = () => {
      // Guardas de seguridad
      if (hasTriggeredRef.current) return;
      if (!isDwellMet) return;
      if (sessionStorage.getItem("tecnidesk_pilot_toast_dismissed") === "true") return;
      if (isFormCompleted()) return;
      if (isUserTyping()) return;

      // Condición de intención: Scroll >= 65% O Workbench superado
      const intentMet = isScrollProgressMet() || isWorkbenchSuperado();

      if (intentMet) {
        hasTriggeredRef.current = true;
        sessionStorage.setItem("tecnidesk_pilot_toast_dismissed", "true");

        const toastId = sileo.action({
          title: "Programa Piloto TecniDesk",
          description: "Primer mes sin costo + onboarding personalizado.",
          button: {
            title: "Postular al piloto →",
            onClick: () => {
              sileo.dismiss(toastId);
              const target =
                document.getElementById(targetSectionId) ||
                document.getElementById("piloto");
              if (target) {
                target.scrollIntoView({ behavior: "smooth" });
              }
            },
          },
          duration: 9000,
          autopilot: { expand: 250, collapse: 8500 },
          styles: {
            button: "landing-sileo-cta-button",
          },
        });
      }
    };

    // Escuchar scroll para evaluar cuando el usuario avance tras cumplir el tiempo
    const handleScroll = () => {
      if (!hasTriggeredRef.current && isDwellMet) {
        evaluateAndTrigger();
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => {
      if (dwellTimer) clearTimeout(dwellTimer);
      window.removeEventListener("scroll", handleScroll);
    };
  }, [minDwellSeconds, minProgress, targetSectionId]);
}
