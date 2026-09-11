import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, BarChart3, Clock, Layers } from "lucide-react";
import ThemeToggle from "../components/shared/ThemeToggle";
import CycleTimeAnalyticsView from "../features/analytics/CycleTimeAnalyticsView";
import BusinessInsightsView from "../features/analytics/BusinessInsightsView";
import "../features/analytics/analytics.css";

/**
 * ARCHITECTURAL DECISION (ADR-001): Route-based Feature Gating
 *
 * This page provides a dedicated route (`/admin/metricas`) for workshop operational analytics.
 * 
 * Future Monetization / Feature Gating:
 * - If this feature is designated as a paid add-on or restricted by tier in the future,
 *   wrap this route in App.jsx with a declarative Route Guard:
 *   `<ProtectedRoute allowedRoles={['admin']}><PlanGuard requiredFeature="cycle_analytics"><AdminAnalyticsPage /></PlanGuard></ProtectedRoute>`
 * - This decouples the executive analytics paywall/upgrade flow completely from AdminDashboard.jsx.
 */
export default function AdminAnalyticsPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("cycle_times");

  useEffect(() => {
    const previousTitle = document.title;
    document.title = "Métricas y Rendimiento — TecniDesk";
    try {
      window.scrollTo(0, 0);
    } catch {
      // jsdom environment fallback
    }

    return () => {
      document.title = previousTitle;
    };
  }, []);

  const handleLogout = () => {
    window.dispatchEvent(new Event("auth:logout"));
    navigate("/login");
  };

  return (
    <div className="analytics-page-root">
      {/* Top Navbar adhering to the Workbench Nav-Pill pattern */}
      <div className="workbench-layout" style={{ minHeight: "auto", paddingBottom: 0 }}>
        <header className="nav-pill" role="banner">
          <div className="nav-pill-brand">
            <img
              src="/logo.png"
              alt="Logo"
              onError={(e) => {
                e.target.style.display = "none";
              }}
              width={24}
              height={24}
              className="workbench-logo"
            />
            <div className="admin-logo-dot" />
            <div>
              <span className="admin-title">{sessionStorage.getItem("td_shop") || "TecniDesk Admin"}</span>
            </div>
          </div>

          <div className="nav-pill-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => navigate("/admin")}
              aria-label="Volver al panel principal del taller"
            >
              <ArrowLeft size={16} className="inline-icon" /> Volver al Taller
            </button>
            <ThemeToggle />
            <button type="button" className="btn-danger" onClick={handleLogout}>
              Cerrar Sesion
            </button>
          </div>
        </header>
      </div>

      {/* Main Container */}
      <main className="analytics-page-content">
        <div className="analytics-page-header">
          <div className="analytics-page-title-row">
            <div className="analytics-page-title-group">
              <div className="modal-header-icon-badge">
                {activeTab === "cycle_times" ? (
                  <Clock size={20} className="accent-icon" />
                ) : (
                  <BarChart3 size={20} className="accent-icon" />
                )}
              </div>
              <div>
                <h1 className="analytics-page-title">
                  {activeTab === "cycle_times"
                    ? "Métricas de Tiempos y Ciclo Operativo"
                    : "Métricas de Negocio, Flota y Clientes"}
                </h1>
                <p className="analytics-page-subtitle">
                  {activeTab === "cycle_times"
                    ? "Lead Time promedio, tiempos netos en banco técnico y detección de cuellos de botella en el taller."
                    : "Rankings de marcas, repuestos de mayor rotación, fidelidad de clientes, técnicos y margen bruto."}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Sub-Tabs Selector */}
        <div className="analytics-tab-nav" role="tablist" aria-label="Categorías de análisis">
          <button
            type="button"
            role="tab"
            id="tab-cycle-times"
            aria-selected={activeTab === "cycle_times"}
            aria-controls="panel-cycle-times"
            className={`analytics-tab-btn ${activeTab === "cycle_times" ? "is-active" : ""}`}
            onClick={() => setActiveTab("cycle_times")}
          >
            <Clock size={16} />
            <span>Tiempos de Ciclo y SLA</span>
          </button>
          <button
            type="button"
            role="tab"
            id="tab-business-insights"
            aria-selected={activeTab === "business_insights"}
            aria-controls="panel-business-insights"
            className={`analytics-tab-btn ${activeTab === "business_insights" ? "is-active" : ""}`}
            onClick={() => setActiveTab("business_insights")}
          >
            <Layers size={16} />
            <span>Flota, Repuestos y Clientes</span>
          </button>
        </div>

        {/* Active Tab Panel */}
        <div
          role="tabpanel"
          id={activeTab === "cycle_times" ? "panel-cycle-times" : "panel-business-insights"}
          aria-labelledby={activeTab === "cycle_times" ? "tab-cycle-times" : "tab-business-insights"}
        >
          {activeTab === "cycle_times" ? (
            <CycleTimeAnalyticsView />
          ) : (
            <BusinessInsightsView />
          )}
        </div>
      </main>
    </div>
  );
}
