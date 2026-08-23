const dateFormatter = new Intl.DateTimeFormat("es-EC", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const onlyDateFormatter = new Intl.DateTimeFormat("es-EC", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatDate(iso) {
  if (!iso) return "-";
  return dateFormatter.format(new Date(iso));
}

export function formatOnlyDate(iso) {
  if (!iso) return "-";
  return onlyDateFormatter.format(new Date(iso));
}

/**
 * Returns human-friendly relative age for ticket scanning.
 * @param {string|Date} iso - Timestamp ISO
 * @returns {string} - "Hoy", "Ayer", "Hace 3 días", "Hace 2 sem", etc.
 */
export function formatRelativeAge(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (isNaN(date.getTime())) return "-";
  const now = new Date();

  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return "Recién";
  if (diffHours < 24 && date.toDateString() === now.toDateString()) return "Hoy";
  
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return "Ayer";

  if (diffDays < 7) {
    const days = Math.max(1, diffDays);
    return `Hace ${days} día${days > 1 ? "s" : ""}`;
  }
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `Hace ${weeks} sem${weeks > 1 ? "s" : ""}`;
  }
  return formatOnlyDate(iso);
}

export const SLA_THRESHOLDS_HOURS = {
  EN_ESPERA_INGRESO: 48,
  EN_REVISION: 24,
  EN_REPARACION: 48,
  ESPERANDO_APROBACION: null,  // Pausado (espera de cliente)
  ESPERANDO_REPUESTO: null,    // Pausado (espera de proveedor)
  LISTO_PARA_RETIRAR: null,    // Listo para retiro
  NO_APROBADO: null,           // Terminal
  ENTREGADO: null,             // Terminal legacy
};

/**
 * Determines if a ticket is stale/overdue based on dynamic SLA thresholds per status.
 * @param {string|Date} iso - Timestamp ISO (updated_at or created_at)
 * @param {string} status - Current ticket status
 * @param {Object|null} customThresholds - Optional tenant-specific SLA threshold map
 * @returns {boolean}
 */
export function isTicketStale(iso, status, customThresholds = null) {
  if (!iso || !status) return false;
  const threshold = customThresholds?.[status] ?? SLA_THRESHOLDS_HOURS[status];
  if (threshold === null || threshold === undefined) {
    return false;
  }
  const date = new Date(iso);
  if (isNaN(date.getTime())) return false;
  const now = new Date();
  const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
  return diffHours >= threshold;
}

