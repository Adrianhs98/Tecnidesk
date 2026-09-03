export const STATUS_CONFIG = {
  EN_ESPERA_INGRESO: { label: "Recibido", color: "#0369a1", bg: "#f0f9ff", border: "#bae6fd", step: 0, icon: "REC" },
  EN_REVISION: { label: "En revision", color: "#b45309", bg: "#fffbeb", border: "#fde68a", step: 1, icon: "REV" },
  ESPERANDO_APROBACION: { label: "Esperando aprobacion", color: "#d97706", bg: "#fffbeb", border: "#fde68a", step: 2, icon: "APR" },
  ESPERANDO_REPUESTO: { label: "Esperando repuesto", color: "#6d28d9", bg: "#f5f3ff", border: "#ddd6fe", step: 3, icon: "REP" },
  EN_REPARACION: { label: "En reparacion", color: "#047857", bg: "#ecfdf5", border: "#a7f3d0", step: 3, icon: "FIX" },
  LISTO_PARA_RETIRAR: { label: "Listo", color: "#047857", bg: "#ecfdf5", border: "#a7f3d0", step: 4, icon: "OK" },
  NO_APROBADO: { label: "No aprobado", color: "#475569", bg: "#f8fafc", border: "#e2e8f0", step: -1, icon: "NO" },
};

export const STEPS = [
  { key: "EN_ESPERA_INGRESO", label: "Recibido" },
  { key: "EN_REVISION", label: "Revision" },
  { key: "ESPERANDO_APROBACION", label: "Aprobacion" },
  { key: "EN_REPARACION", label: "Reparacion" },
  { key: "LISTO_PARA_RETIRAR", label: "Listo" },
];

export const ADMIN_STATUSES = [
  { value: "EN_ESPERA_INGRESO", label: "Recibido" },
  { value: "EN_REVISION", label: "En revision" },
  { value: "ESPERANDO_APROBACION", label: "Esperando aprobacion" },
  { value: "ESPERANDO_REPUESTO", label: "Esperando repuesto" },
  { value: "EN_REPARACION", label: "En reparacion" },
  { value: "LISTO_PARA_RETIRAR", label: "Listo para retirar" },
  { value: "NO_APROBADO", label: "No aprobado" },
];
