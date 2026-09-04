import React from 'react';
import { ClipboardList } from 'lucide-react';
import { STATUS_CONFIG } from '../../utils/constants';

/**
 * Unified StatusBadge component conforming to Airtable DESIGN.md tokens.
 */
export default function StatusBadge({ status, showIcon = true, className = "", style = {} }) {
  const cfg = STATUS_CONFIG[status] || {
    label: status || "Desconocido",
    color: "var(--color-ink-muted, #4b5563)",
    bg: "var(--color-surface-hover, #f3f4f6)",
    border: "var(--color-hairline, #dddddd)",
    icon: "📋",
  };

  const badgeStyle = {
    backgroundColor: cfg.bg || `${cfg.color}18`,
    color: cfg.color,
    borderColor: cfg.border || `${cfg.color}40`,
    flexShrink: 0,
    ...style,
  };

  return (
    <span
      className={`ticket-badge ${className}`.trim()}
      data-status={status?.toLowerCase()}
      style={badgeStyle}
    >
      {showIcon && (
        cfg.icon === "📋" ? (
          <ClipboardList size={14} style={{ marginRight: 6 }} aria-hidden="true" />
        ) : (
          <span style={{ marginRight: 6, fontSize: 10, fontFamily: "monospace" }} aria-hidden="true">
            {cfg.icon}
          </span>
        )
      )}
      {cfg.label}
    </span>
  );
}
