import React, { useState, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { X, BarChart3, Clock, AlertTriangle, CheckCircle2, Zap, RotateCcw, Info } from "lucide-react";
import { fetchCycleTimeAnalytics } from "../../../api/ticketAnalytics";

const PERIOD_OPTIONS = [
  { days: 7, label: "7 días" },
  { days: 30, label: "30 días" },
  { days: 90, label: "90 días" },
];

const STAGE_COLOR_MAP = {
  EN_ESPERA_INGRESO: "var(--accent, #3b82f6)",
  EN_REVISION: "#eab308",
  ESPERANDO_APROBACION: "#f97316",
  ESPERANDO_REPUESTO: "#a855f7",
  EN_REPARACION: "#06b6d4",
};

export default function CycleTimeAnalyticsModal({ onClose }) {
  const [selectedDays, setSelectedDays] = useState(30);

  const { data: analytics, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["cycleTimeAnalytics", selectedDays],
    queryFn: () => fetchCycleTimeAnalytics(selectedDays),
    staleTime: 1000 * 60 * 2,
  });

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

  const formatHours = (hours) => {
    if (hours === undefined || hours === null) return "0.0 h";
    if (hours >= 24) {
      const days = (hours / 24).toFixed(1);
      return `${hours.toFixed(1)} h (${days}d)`;
    }
    return `${hours.toFixed(1)} h`;
  };

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

        {/* Period Selector */}
        <div className="analytics-toolbar">
          <div className="analytics-period-selector" role="group" aria-label="Seleccionar período">
            {PERIOD_OPTIONS.map((opt) => (
              <button
                key={opt.days}
                type="button"
                className={`period-btn ${selectedDays === opt.days ? "is-active" : ""}`}
                onClick={() => setSelectedDays(opt.days)}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn-icon-secondary"
            onClick={() => refetch()}
            title="Recargar métricas"
            aria-label="Recargar métricas"
          >
            <RotateCcw size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body analytics-modal-body">
          {isLoading && (
            <div className="analytics-loading-state">
              <div className="spinner" />
              <p>Calculando métricas del taller...</p>
            </div>
          )}

          {isError && (
            <div className="analytics-error-state">
              <AlertTriangle size={36} color="var(--danger, #ef4444)" />
              <p className="error-text">{error?.message || "Error al cargar las métricas operativas."}</p>
              <button className="btn-secondary" onClick={() => refetch()}>
                Reintentar
              </button>
            </div>
          )}

          {!isLoading && !isError && analytics && (
            <>
              {/* Counts Summary Bar */}
              <div className="analytics-counts-bar">
                <div className="count-badge">
                  <span className="count-label">Tickets analizados:</span>
                  <span className="count-value">{analytics.tickets_analyzed_count}</span>
                </div>
                <div className="count-divider" />
                <div className="count-badge">
                  <span className="count-label">Completados:</span>
                  <span className="count-value highlight-success">{analytics.completed_tickets_count}</span>
                </div>
                <div className="count-divider" />
                <div className="count-badge">
                  <span className="count-label">Activos en proceso:</span>
                  <span className="count-value highlight-accent">{analytics.active_tickets_count}</span>
                </div>
              </div>

              {/* KPI Cards Grid */}
              <div className="analytics-kpi-grid">
                {/* Lead Time */}
                <div className="analytics-kpi-card">
                  <div className="kpi-card-header">
                    <span className="kpi-card-title">Lead Time Promedio</span>
                    <Clock size={18} className="kpi-icon accent" />
                  </div>
                  <div className="kpi-card-value">{formatHours(analytics.lead_time_avg_hours)}</div>
                  <div className="kpi-card-hint">Ingreso hasta entrega / cierre</div>
                </div>

                {/* Active Cycle Time */}
                <div className="analytics-kpi-card">
                  <div className="kpi-card-header">
                    <span className="kpi-card-title">Ciclo Activo de Reparación</span>
                    <Zap size={18} className="kpi-icon highlight" />
                  </div>
                  <div className="kpi-card-value">{formatHours(analytics.cycle_time_avg_hours)}</div>
                  <div className="kpi-card-hint">Tiempo neto en banco técnico</div>
                </div>

                {/* SLA Compliance */}
                <div className="analytics-kpi-card">
                  <div className="kpi-card-header">
                    <span className="kpi-card-title">Cumplimiento SLA</span>
                    <CheckCircle2 size={18} className="kpi-icon success" />
                  </div>
                  <div className={`kpi-card-value ${analytics.sla_compliance_rate >= 80 ? "success" : "warning"}`}>
                    {analytics.sla_compliance_rate.toFixed(1)}%
                  </div>
                  <div className="kpi-card-hint">Etapas dentro de umbral objetivo</div>
                </div>

                {/* Bottleneck Stage */}
                <div className={`analytics-kpi-card ${analytics.bottleneck_stage ? "has-bottleneck" : ""}`}>
                  <div className="kpi-card-header">
                    <span className="kpi-card-title">Cuello de Botella</span>
                    <AlertTriangle size={18} className="kpi-icon warning" />
                  </div>
                  <div className="kpi-card-value bottleneck-val">
                    {analytics.bottleneck_stage_label || "Ninguno"}
                  </div>
                  <div className="kpi-card-hint">
                    {analytics.bottleneck_stage
                      ? "Etapa con mayor tiempo de permanencia"
                      : "Sin demoras críticas detectadas"}
                  </div>
                </div>
              </div>

              {/* Stage Breakdown Section */}
              <div className="analytics-section">
                <div className="analytics-section-header">
                  <h3 className="section-title">Desglose de Tiempos por Etapa</h3>
                  <span className="section-subtitle">Promedio de horas y proporción del flujo de trabajo</span>
                </div>

                {analytics.tickets_analyzed_count === 0 ? (
                  <div className="analytics-empty-message">
                    <Info size={28} className="empty-icon" />
                    <p>Sin datos en el período seleccionado. Ingresa o completa órdenes de reparación para ver el análisis de tiempos.</p>
                  </div>
                ) : (
                  <div className="stage-meters-container">
                    {analytics.stage_durations.map((stage) => {
                      const color = STAGE_COLOR_MAP[stage.status] || "var(--accent)";
                      return (
                        <div
                          key={stage.status}
                          className={`stage-meter-row ${stage.is_bottleneck ? "is-bottleneck-row" : ""}`}
                        >
                          <div className="stage-meter-header">
                            <div className="stage-label-group">
                              <span className="stage-color-dot" style={{ backgroundColor: color }} />
                              <span className="stage-label">{stage.label}</span>
                              {stage.is_bottleneck && (
                                <span className="bottleneck-badge" title="Cuello de botella principal">
                                  <AlertTriangle size={12} className="inline-icon" /> Cuello de botella
                                </span>
                              )}
                            </div>
                            <div className="stage-values-group">
                              <span className="stage-hours">{stage.avg_hours.toFixed(1)} h</span>
                              <span className="stage-percentage">({stage.percentage_of_total.toFixed(1)}%)</span>
                            </div>
                          </div>

                          <div className="stage-bar-track">
                            <div
                              className="stage-bar-fill"
                              style={{
                                width: `${Math.max(stage.percentage_of_total, stage.avg_hours > 0 ? 3 : 0)}%`,
                                backgroundColor: stage.is_bottleneck ? "var(--warning, #f59e0b)" : color,
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          )}
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
