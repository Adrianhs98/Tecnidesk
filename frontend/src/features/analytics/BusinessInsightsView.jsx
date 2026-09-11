import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Smartphone,
  CheckCircle,
  Package,
  Users,
  Wrench,
  DollarSign,
  AlertOctagon,
  RotateCcw,
  AlertTriangle,
  Info,
  TrendingUp,
  Percent,
} from "lucide-react";
import { fetchBusinessInsights } from "../../api/ticketAnalytics";
import { formatCurrency } from "../../utils/currency";
import { maskPhone, maskEmail } from "../../utils/privacy";
import "./analytics.css";

const PERIOD_OPTIONS = [
  { days: 7, label: "7 días" },
  { days: 30, label: "30 días" },
  { days: 90, label: "90 días" },
];

export default function BusinessInsightsView() {
  const [selectedDays, setSelectedDays] = useState(30);

  const {
    data: insights,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["businessInsights", selectedDays],
    queryFn: () => fetchBusinessInsights(selectedDays),
    staleTime: 1000 * 60 * 2,
  });

  return (
    <div className="analytics-view-card">
      {/* Toolbar */}
      <div className="analytics-toolbar">
        <div className="analytics-period-selector" role="group" aria-label="Seleccionar período de análisis">
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

      {/* Loading State */}
      {isLoading && (
        <div className="analytics-loading-state">
          <div className="spinner" />
          <p>Calculando estadísticas de flota, repuestos y clientes...</p>
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="analytics-error-state">
          <AlertTriangle size={36} color="var(--danger, #ef4444)" />
          <p className="error-text">{error?.message || "Error al cargar las métricas del taller."}</p>
          <button type="button" className="btn-secondary" onClick={() => refetch()}>
            Reintentar
          </button>
        </div>
      )}

      {/* Success View */}
      {!isLoading && !isError && insights && (
        <>
          {/* Executive Overview KPI Grid */}
          <div className="analytics-kpi-grid">
            {/* Margen Bruto */}
            <div className="analytics-kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-card-title">Margen Bruto Estimado</span>
                <DollarSign size={18} className="kpi-icon highlight" />
              </div>
              <div className="kpi-card-value success">
                {formatCurrency(insights.gross_margin.estimated_gross_profit)}
              </div>
              <div className="kpi-card-hint">
                Rentabilidad: {insights.gross_margin.margin_percentage.toFixed(1)}% del total facturado
              </div>
            </div>

            {/* Facturación Total */}
            <div className="analytics-kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-card-title">Facturación en Período</span>
                <TrendingUp size={18} className="kpi-icon accent" />
              </div>
              <div className="kpi-card-value">
                {formatCurrency(insights.gross_margin.total_revenue)}
              </div>
              <div className="kpi-card-hint">
                Mano de obra: {insights.gross_margin.labor_percentage.toFixed(0)}% | Repuestos: {insights.gross_margin.parts_percentage.toFixed(0)}%
              </div>
            </div>

            {/* Recurrencia Clientes */}
            <div className="analytics-kpi-card">
              <div className="kpi-card-header">
                <span className="kpi-card-title">Tasa de Fidelidad</span>
                <Users size={18} className="kpi-icon accent" />
              </div>
              <div className="kpi-card-value">
                {insights.customer_recurrence.recurrence_rate.toFixed(1)}%
              </div>
              <div className="kpi-card-hint">
                {insights.customer_recurrence.recurring_customers_count} clientes con 2+ equipos (de {insights.customer_recurrence.total_customers})
              </div>
            </div>

            {/* Alertas de Stock */}
            <div className={`analytics-kpi-card ${insights.critical_stock_alerts.length > 0 ? "has-bottleneck" : ""}`}>
              <div className="kpi-card-header">
                <span className="kpi-card-title">Alertas de Repuestos</span>
                <AlertOctagon size={18} className="kpi-icon warning" />
              </div>
              <div className="kpi-card-value bottleneck-val">
                {insights.critical_stock_alerts.length} piezas críticas
              </div>
              <div className="kpi-card-hint">
                {insights.critical_stock_alerts.length > 0
                  ? "Piezas de alta rotación bajo stock mínimo"
                  : "Inventario en niveles óptimos"}
              </div>
            </div>
          </div>

          {/* 2-Column Responsive Layout for Detailed Insights */}
          <div className="insights-sections-grid">
            {/* KPI 1: Ranking de Marcas y Modelos */}
            <div className="analytics-section">
              <div className="analytics-section-header">
                <div className="section-title-with-icon">
                  <Smartphone size={18} className="accent-icon" />
                  <h3 className="section-title">Volumen de Ingreso por Marca y Modelo</h3>
                </div>
                <span className="section-subtitle">Distribución de equipos admitidos en el taller</span>
              </div>

              {insights.brand_intake_ranking.length === 0 ? (
                <div className="analytics-empty-message">
                  <Info size={24} className="empty-icon" />
                  <p>Sin ingresos registrados en este período.</p>
                </div>
              ) : (
                <div className="insights-list-container">
                  {insights.brand_intake_ranking.map((brandItem) => (
                    <div key={brandItem.brand} className="insights-item-card">
                      <div className="insights-item-header">
                        <span className="insights-item-name">{brandItem.brand}</span>
                        <span className="insights-item-stat">
                          {brandItem.total_tickets} equipos ({brandItem.percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="insights-progress-track">
                        <div
                          className="insights-progress-fill brand-fill"
                          style={{ width: `${Math.max(brandItem.percentage, 4)}%` }}
                        />
                      </div>
                      {brandItem.top_models && brandItem.top_models.length > 0 && (
                        <div className="insights-tag-group">
                          {brandItem.top_models.map((m) => (
                            <span key={m.model} className="insights-sub-tag">
                              {m.model} <strong>({m.count})</strong>
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* KPI 2: Tasa de Reparación Confirmada por Marca */}
            <div className="analytics-section">
              <div className="analytics-section-header">
                <div className="section-title-with-icon">
                  <CheckCircle size={18} className="success-icon" />
                  <h3 className="section-title">Tasa de Reparación Confirmada por Marca</h3>
                </div>
                <span className="section-subtitle">
                  Porcentaje de reparaciones aprobadas vs no aprobadas (excluye descartados)
                </span>
              </div>

              {insights.brand_repair_rates.length === 0 ? (
                <div className="analytics-empty-message">
                  <Info size={24} className="empty-icon" />
                  <p>Sin diagnósticos registrados en este período.</p>
                </div>
              ) : (
                <div className="insights-list-container">
                  {insights.brand_repair_rates.map((rateItem) => (
                    <div key={rateItem.brand} className="insights-item-card">
                      <div className="insights-item-header">
                        <span className="insights-item-name">{rateItem.brand}</span>
                        <span className={`insights-item-badge ${rateItem.repair_rate >= 75 ? "badge-success" : rateItem.repair_rate >= 50 ? "badge-warning" : "badge-danger"}`}>
                          {rateItem.repair_rate.toFixed(1)}% efectividad
                        </span>
                      </div>
                      <div className="insights-progress-track">
                        <div
                          className="insights-progress-fill"
                          style={{
                            width: `${Math.max(rateItem.repair_rate, 4)}%`,
                            backgroundColor:
                              rateItem.repair_rate >= 75
                                ? "var(--success, #22c55e)"
                                : rateItem.repair_rate >= 50
                                ? "var(--warning, #f59e0b)"
                                : "var(--danger, #ef4444)",
                          }}
                        />
                      </div>
                      <div className="insights-subtext-row">
                        <span>Reparados: <strong>{rateItem.confirmed_repairs}</strong></span>
                        <span>No aprobados: <strong>{rateItem.rejected_repairs}</strong></span>
                        <span>Total evaluados: <strong>{rateItem.total_tickets}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* KPI 3: Repuestos con Más Rotación */}
            <div className="analytics-section">
              <div className="analytics-section-header">
                <div className="section-title-with-icon">
                  <Package size={18} className="accent-icon" />
                  <h3 className="section-title">Repuestos con Mayor Rotación</h3>
                </div>
                <span className="section-subtitle">Componentes y piezas más consumidos en reparaciones</span>
              </div>

              {insights.top_parts_rotation.length === 0 ? (
                <div className="analytics-empty-message">
                  <Info size={24} className="empty-icon" />
                  <p>No se han registrado repuestos utilizados en este período.</p>
                </div>
              ) : (
                <div className="insights-table-wrapper">
                  <table className="insights-table">
                    <thead>
                      <tr>
                        <th>Repuesto / Pieza</th>
                        <th className="text-right">Unidades</th>
                        <th className="text-right">Ingresos</th>
                        <th className="text-right">Stock Actual</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insights.top_parts_rotation.map((part, idx) => (
                        <tr key={`${part.item_name}-${idx}`}>
                          <td className="font-medium">{part.item_name}</td>
                          <td className="text-right">
                            <span className="units-badge">{part.units_used} un.</span>
                          </td>
                          <td className="text-right">{formatCurrency(part.total_revenue)}</td>
                          <td className="text-right">
                            {part.current_stock !== null ? (
                              <span className={`stock-tag ${part.is_low_stock ? "stock-tag-alert" : "stock-tag-ok"}`}>
                                {part.current_stock} disp.
                              </span>
                            ) : (
                              <span className="stock-tag stock-tag-muted">Sin catálogo</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* KPI 7: Alerta de Repuestos Críticos de Alta Rotación */}
            <div className="analytics-section">
              <div className="analytics-section-header">
                <div className="section-title-with-icon">
                  <AlertOctagon size={18} className="danger-icon" />
                  <h3 className="section-title">Alerta de Repuestos Críticos</h3>
                </div>
                <span className="section-subtitle">Stock igual o menor al umbral mínimo de seguridad</span>
              </div>

              {insights.critical_stock_alerts.length === 0 ? (
                <div className="analytics-empty-message">
                  <CheckCircle size={24} className="success-icon" />
                  <p>Todos los repuestos monitoreados tienen stock suficiente.</p>
                </div>
              ) : (
                <div className="insights-table-wrapper">
                  <table className="insights-table">
                    <thead>
                      <tr>
                        <th>Repuesto</th>
                        <th className="text-right">Consumo Reciente</th>
                        <th className="text-right">Stock / Mínimo</th>
                        <th className="text-right">Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insights.critical_stock_alerts.map((alert) => (
                        <tr key={alert.inventory_id}>
                          <td className="font-medium">
                            {alert.item_name}
                            {alert.sku && <span className="sku-sublabel"> ({alert.sku})</span>}
                          </td>
                          <td className="text-right">{alert.units_used_in_period} un.</td>
                          <td className="text-right">
                            <strong>{alert.current_stock}</strong> / {alert.low_stock_alert}
                          </td>
                          <td className="text-right">
                            <span className={`alert-pill ${alert.alert_level === "CRITICO" ? "pill-critical" : "pill-low"}`}>
                              {alert.alert_level === "CRITICO" ? "Agotado" : "Stock Bajo"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* KPI 4: Clientes Frecuentes / Recurrentes */}
            <div className="analytics-section">
              <div className="analytics-section-header">
                <div className="section-title-with-icon">
                  <Users size={18} className="accent-icon" />
                  <h3 className="section-title">Clientes Frecuentes (2+ Órdenes)</h3>
                </div>
                <span className="section-subtitle">Identificación de clientes leales con historial recurrente</span>
              </div>

              {insights.customer_recurrence.top_recurring_customers.length === 0 ? (
                <div className="analytics-empty-message">
                  <Info size={24} className="empty-icon" />
                  <p>Aún no hay clientes con 2 o más equipos registrados en el taller.</p>
                </div>
              ) : (
                <div className="insights-table-wrapper">
                  <table className="insights-table">
                    <thead>
                      <tr>
                        <th>Cliente</th>
                        <th>Teléfono</th>
                        <th>Correo</th>
                        <th className="text-right">Órdenes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insights.customer_recurrence.top_recurring_customers.map((c) => (
                        <tr key={c.customer_id}>
                          <td className="font-medium">{c.full_name}</td>
                          <td className="text-secondary">{maskPhone(c.phone_number)}</td>
                          <td className="text-secondary">{maskEmail(c.email)}</td>
                          <td className="text-right">
                            <span className="orders-badge">{c.ticket_count} equipos</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* KPI 5: Rendimiento de Técnicos */}
            <div className="analytics-section">
              <div className="analytics-section-header">
                <div className="section-title-with-icon">
                  <Wrench size={18} className="accent-icon" />
                  <h3 className="section-title">Rendimiento Operativo de Técnicos</h3>
                </div>
                <span className="section-subtitle">Tickets resueltos vs tickets activos en banco</span>
              </div>

              {insights.technician_performance.length === 0 ? (
                <div className="analytics-empty-message">
                  <Info size={24} className="empty-icon" />
                  <p>No hay técnicos activos asignados en el taller.</p>
                </div>
              ) : (
                <div className="insights-table-wrapper">
                  <table className="insights-table">
                    <thead>
                      <tr>
                        <th>Técnico</th>
                        <th className="text-right">En Banco</th>
                        <th className="text-right">Resueltos</th>
                        <th className="text-right">Total Asignados</th>
                        <th className="text-right">Efectividad</th>
                      </tr>
                    </thead>
                    <tbody>
                      {insights.technician_performance.map((tech) => (
                        <tr key={tech.technician_id}>
                          <td className="font-medium">{tech.technician_name}</td>
                          <td className="text-right">
                            <span className="active-badge">{tech.active_in_bench_count}</span>
                          </td>
                          <td className="text-right">
                            <span className="resolved-badge">{tech.resolved_count}</span>
                          </td>
                          <td className="text-right">{tech.total_assigned}</td>
                          <td className="text-right font-medium">
                            {tech.completion_rate.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* KPI 6: Margen Bruto y Estructura de Ingresos (Full Width Card) */}
          <div className="analytics-section full-width-section">
            <div className="analytics-section-header">
              <div className="section-title-with-icon">
                <Percent size={18} className="accent-icon" />
                <h3 className="section-title">Estructura Financiera: Mano de Obra vs Repuestos</h3>
              </div>
              <span className="section-subtitle">
                Comparativa de costos de adquisición vs precios de facturación al cliente
              </span>
            </div>

            <div className="margin-breakdown-card">
              <div className="margin-stats-row">
                <div className="margin-stat-block">
                  <span className="stat-block-label">Mano de Obra Facturada</span>
                  <span className="stat-block-value accent">
                    {formatCurrency(insights.gross_margin.labor_revenue)}
                  </span>
                  <span className="stat-block-sub">{insights.gross_margin.labor_percentage.toFixed(1)}% de las ventas</span>
                </div>

                <div className="margin-stat-block">
                  <span className="stat-block-label">Ventas en Repuestos</span>
                  <span className="stat-block-value">
                    {formatCurrency(insights.gross_margin.parts_revenue)}
                  </span>
                  <span className="stat-block-sub">{insights.gross_margin.parts_percentage.toFixed(1)}% de las ventas</span>
                </div>

                <div className="margin-stat-block">
                  <span className="stat-block-label">Costo de Repuestos</span>
                  <span className="stat-block-value warning">
                    {formatCurrency(insights.gross_margin.parts_cost)}
                  </span>
                  <span className="stat-block-sub">Costo de adquisición</span>
                </div>

                <div className="margin-stat-block highlight-block">
                  <span className="stat-block-label">Margen Bruto Total</span>
                  <span className="stat-block-value success">
                    {formatCurrency(insights.gross_margin.estimated_gross_profit)}
                  </span>
                  <span className="stat-block-sub">{insights.gross_margin.margin_percentage.toFixed(1)}% rentabilidad neta</span>
                </div>
              </div>

              {/* Segmented Progress Bar */}
              <div className="segmented-bar-container">
                <div className="segmented-bar-labels">
                  <span>Mano de Obra ({insights.gross_margin.labor_percentage.toFixed(0)}%)</span>
                  <span>Margen Repuestos</span>
                  <span>Costo Repuestos</span>
                </div>
                <div className="segmented-bar-track">
                  <div
                    className="segmented-segment labor-segment"
                    style={{ width: `${Math.max(insights.gross_margin.labor_percentage, 2)}%` }}
                    title={`Mano de obra: ${formatCurrency(insights.gross_margin.labor_revenue)}`}
                  />
                  <div
                    className="segmented-segment parts-margin-segment"
                    style={{
                      width: `${Math.max(
                        insights.gross_margin.total_revenue > 0
                          ? (insights.gross_margin.parts_margin / insights.gross_margin.total_revenue) * 100
                          : 0,
                        0
                      )}%`,
                    }}
                    title={`Margen repuestos: ${formatCurrency(insights.gross_margin.parts_margin)}`}
                  />
                  <div
                    className="segmented-segment parts-cost-segment"
                    style={{
                      width: `${Math.max(
                        insights.gross_margin.total_revenue > 0
                          ? (insights.gross_margin.parts_cost / insights.gross_margin.total_revenue) * 100
                          : 0,
                        0
                      )}%`,
                    }}
                    title={`Costo repuestos: ${formatCurrency(insights.gross_margin.parts_cost)}`}
                  />
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
