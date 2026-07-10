export const STATUS_CONFIG = {
  EN_ESPERA_INGRESO: { label: "Recibido", color: "#C9A76A", step: 0, icon: "REC" },
  EN_REVISION: { label: "En revision", color: "#B89251", step: 1, icon: "REV" },
  ESPERANDO_APROBACION: { label: "Esperando aprobacion", color: "#CC8F5A", step: 2, icon: "APR" },
  ESPERANDO_REPUESTO: { label: "Esperando repuesto", color: "#6F9FCC", step: 3, icon: "REP" },
  EN_REPARACION: { label: "En reparacion", color: "#6F9FCC", step: 3, icon: "FIX" },
  LISTO_PARA_RETIRAR: { label: "Listo", color: "#4E9F7D", step: 4, icon: "OK" },
  NO_APROBADO: { label: "No aprobado", color: "#9D5C52", step: -1, icon: "NO" },
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
