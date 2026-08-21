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

/**
 * Determines if a ticket is stale/overdue (>72 hours in active status).
 * @param {string|Date} iso - Timestamp ISO
 * @param {string} status - Current ticket status
 * @returns {boolean}
 */
export function isTicketStale(iso, status) {
  if (!iso) return false;
  if (["LISTO_PARA_RETIRAR", "NO_APROBADO", "ENTREGADO"].includes(status)) {
    return false;
  }
  const date = new Date(iso);
  if (isNaN(date.getTime())) return false;
  const now = new Date();
  const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
  return diffHours >= 72;
}
