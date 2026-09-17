import { Toaster, sileo } from "sileo";
import { useTheme } from "../../../context/ThemeContext";

if (typeof window !== "undefined") {
  window.sileo = sileo;
}

/**
 * LandingToastProvider
 * Monta el Toaster de Sileo con la configuración de diseño de TecniDesk:
 * - Posicionamiento en esquina inferior (bottom-right en desktop, adaptado por CSS en móvil).
 * - Sincronizado con el ThemeContext (modo claro por defecto en landing, o modo oscuro).
 * - Offsets calculados para respetar márgenes visuales y no solapar controles flotantes.
 */
export default function LandingToastProvider() {
  const { theme } = useTheme();
  const currentTheme = theme === "light" ? "light" : "dark";
  const fill = currentTheme === "light" ? "#FFFFFF" : "#1B1F27";

  return (
    <Toaster
      position="top-right"
      offset={{ top: 88, right: 24 }}
      theme={currentTheme}
      options={{
        roundness: 12,
        fill,
      }}
    />
  );
}
