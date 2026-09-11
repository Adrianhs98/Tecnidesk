import React, { useEffect, useCallback } from "react";
import { X, BarChart3 } from "lucide-react";
import CycleTimeAnalyticsView from "../../analytics/CycleTimeAnalyticsView";

/**
 * CycleTimeAnalyticsModal
 * Retained for backward compatibility with existing tests and modal consumers.
 * Core analytics presentation is encapsulated within CycleTimeAnalyticsView (ADR-001).
 */
export default function CycleTimeAnalyticsModal({ onClose }) {
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="modal-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="analytics-modal-title">
      <div className="modal-content cycle-analytics-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-title-group">
            <div className="modal-header-icon-badge">
              <BarChart3 size={20} className="accent-icon" />
            </div>
            <div>
              <h2 id="analytics-modal-title" className="modal-title">Métricas de Tiempos y Ciclo</h2>
              <p className="modal-subtitle">Lead Time, tiempos de ciclo en taller y detección de cuellos de botella</p>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Cerrar modal">
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body analytics-modal-body">
          <CycleTimeAnalyticsView isModal={true} />
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
