import { useState, useMemo, useTransition } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Wrench,
  Search,
  LayoutGrid,
  List,
  Clock,
  CheckCircle2,
  AlertCircle,
  Inbox,
  Sparkles,
  RefreshCw,
  SlidersHorizontal,
  ChevronRight,
  Filter,
} from "lucide-react";
import { authFetch } from "../../api/authFetch";
import { API_BASE } from "../../api/config";
import { getTechnicianMe, assignTicketToMe } from "../../api/technician";
import { fetchSlaConfig } from "../../api/shop";
import TechnicianHeader from "./TechnicianHeader";
import TechnicianTicketCard from "./TechnicianTicketCard";
import TechnicianWorkModal from "./TechnicianWorkModal";
import AiChatBubble from "./AiChatBubble";
import AiChatDrawer from "./AiChatDrawer";

// 3-Column Kanban Board setup for Technician Workflow
const TECH_KANBAN_COLUMNS = [
  {
    id: "ingreso_revision",
    title: "Ingreso & Revisión",
    statuses: ["EN_ESPERA_INGRESO", "EN_REVISION", "RECIBIDO"],
    accentColor: "#B89251",
  },
  {
    id: "reparacion_repuesto",
    title: "En Reparación & Repuesto",
    statuses: ["EN_REPARACION", "ESPERANDO_REPUESTO", "ESPERANDO_APROBACION"],
    accentColor: "#6F9FCC",
  },
  {
    id: "listo_entrega",
    title: "Listo para Entrega",
    statuses: ["LISTO_PARA_RETIRAR", "NO_APROBADO"],
    accentColor: "var(--success)",
  },
];

const STATUS_FILTER_OPTIONS = [
  { value: "", label: "Todos los Estados" },
  { value: "EN_ESPERA_INGRESO", label: "Ingresado / En Espera" },
  { value: "EN_REVISION", label: "En Revisión" },
  { value: "EN_REPARACION", label: "En Reparación" },
  { value: "ESPERANDO_REPUESTO", label: "Esperando Repuesto" },
  { value: "LISTO_PARA_RETIRAR", label: "Listo para Retirar" },
];

export default function TechnicianDashboard() {
  const queryClient = useQueryClient();
  const [, startTransition] = useTransition();

  const userRole = sessionStorage.getItem("td_role") || "technician";
  const isReadOnly = userRole === "admin";

  // Navigation tab: 'my_tickets' vs 'available_tickets'
  const [activeTab, setActiveTab] = useState("my_tickets");

  // Search & Filter
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [kpiFilter, setKpiFilter] = useState(null); // null | 'activos' | 'revision' | 'listos'

  // View mode: 'list' | 'kanban'
  const [viewMode, setViewMode] = useState(() => {
    try {
      return localStorage.getItem("tecnidesk_tech_view") || "list";
    } catch {
      return "list";
    }
  });

  // Modals & Drawers state
  const [selectedTicketForWork, setSelectedTicketForWork] = useState(null);
  const [selectedTicketForAi, setSelectedTicketForAi] = useState(null);
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const [takingTicketId, setTakingTicketId] = useState(null);

  // 1. Fetch Technician Profile
  const { data: meData } = useQuery({
    queryKey: ["technicianMe"],
    queryFn: getTechnicianMe,
    staleTime: 1000 * 60 * 5,
    enabled: !isReadOnly,
  });

  // 2. Fetch SLA Configuration
  const { data: slaConfigData } = useQuery({
    queryKey: ["shopSlaConfig"],
    queryFn: fetchSlaConfig,
    staleTime: 1000 * 60 * 10,
  });
  const slaThresholds = slaConfigData?.effective_thresholds || null;

  // 3. Fetch Tickets Query
  const {
    data: ticketsResponse,
    isLoading: loadingTickets,
    isRefetching,
    refetch: refetchTickets,
  } = useQuery({
    queryKey: ["technicianTickets", activeTab, searchQuery, statusFilter, meData?.id, isReadOnly],
    queryFn: async () => {
      let url = `${API_BASE}/tickets?limit=50`;

      if (activeTab === "my_tickets") {
        if (!isReadOnly && meData?.id) {
          url += `&technician_id=${meData.id}`;
        }
      } else if (activeTab === "available_tickets") {
        url += `&unassigned_only=true`;
      }

      if (searchQuery.trim()) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      if (statusFilter) {
        url += `&ticket_status=${encodeURIComponent(statusFilter)}`;
      }

      const res = await authFetch(url);
      if (!res.ok) throw new Error("Error al obtener lista de tickets");
      return res.json();
    },
    enabled: isReadOnly || activeTab === "available_tickets" || Boolean(meData?.id) || meData === null,
  });

  const rawTickets = ticketsResponse?.items || [];

  // Filter tickets by KPI selection if active
  const displayedTickets = useMemo(() => {
    if (!kpiFilter) return rawTickets;
    if (kpiFilter === "activos") {
      return rawTickets.filter(
        (t) => t.status !== "LISTO_PARA_RETIRAR" && t.status !== "NO_APROBADO"
      );
    }
    if (kpiFilter === "revision") {
      return rawTickets.filter(
        (t) => t.status === "EN_REVISION" || t.status === "EN_ESPERA_INGRESO"
      );
    }
    if (kpiFilter === "listos") {
      return rawTickets.filter((t) => t.status === "LISTO_PARA_RETIRAR");
    }
    return rawTickets;
  }, [rawTickets, kpiFilter]);

  // Operational KPIs calculations
  const kpis = useMemo(() => {
    const list = rawTickets;
    const activos = list.filter(
      (t) => t.status !== "LISTO_PARA_RETIRAR" && t.status !== "NO_APROBADO"
    ).length;
    const revision = list.filter(
      (t) => t.status === "EN_REVISION" || t.status === "EN_ESPERA_INGRESO"
    ).length;
    const listos = list.filter((t) => t.status === "LISTO_PARA_RETIRAR").length;
    return {
      activos:
        !isReadOnly && meData?.active_tickets_count !== undefined && activeTab === "my_tickets"
          ? meData.active_tickets_count
          : activos,
      revision,
      listos:
        !isReadOnly && meData?.completed_tickets_count !== undefined && activeTab === "my_tickets"
          ? meData.completed_tickets_count
          : listos,
    };
  }, [rawTickets, meData, activeTab, isReadOnly]);

  // Group tickets into 3 Kanban columns
  const kanbanGroups = useMemo(() => {
    const groups = {};
    TECH_KANBAN_COLUMNS.forEach((col) => {
      groups[col.id] = [];
    });

    displayedTickets.forEach((ticket) => {
      const targetCol = TECH_KANBAN_COLUMNS.find((col) => col.statuses.includes(ticket.status));
      if (targetCol) {
        groups[targetCol.id].push(ticket);
      } else {
        // Fallback column
        groups["ingreso_revision"].push(ticket);
      }
    });

    return groups;
  }, [displayedTickets]);

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    try {
      localStorage.setItem("tecnidesk_tech_view", mode);
    } catch {
      // ignore
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    startTransition(() => {
      setSearchQuery(searchInput);
    });
  };

  const handleKpiClick = (targetKpi) => {
    setKpiFilter((prev) => (prev === targetKpi ? null : targetKpi));
  };

  // Assign ticket to current technician (1-click from available tab)
  const handleTakeTicket = async (ticket) => {
    setTakingTicketId(ticket.id);
    try {
      const updated = await assignTicketToMe(ticket.id);
      await queryClient.invalidateQueries({ queryKey: ["technicianTickets"] });
      await queryClient.invalidateQueries({ queryKey: ["technicianMe"] });
      setActiveTab("my_tickets");
      setSelectedTicketForWork(updated);
    } catch (err) {
      alert(err.message || "Error al auto-asignar el equipo");
    } finally {
      setTakingTicketId(null);
    }
  };

  // Open AI Drawer contextualized
  const handleOpenAiForTicket = (ticket) => {
    setSelectedTicketForAi(ticket);
    setIsAiDrawerOpen(true);
  };

  // Handle ticket updated in modal
  const handleTicketUpdated = (updated) => {
    queryClient.setQueryData(
      ["technicianTickets", activeTab, searchQuery, statusFilter, meData?.id, isReadOnly],
      (oldData) => {
        if (!oldData) return oldData;
        const items = oldData.items || [];
        const newItems = items.map((t) => (t.id === updated.id ? { ...t, ...updated } : t));
        return { ...oldData, items: newItems };
      }
    );
    if (selectedTicketForWork?.id === updated.id) {
      setSelectedTicketForWork(updated);
    }
    if (selectedTicketForAi?.id === updated.id) {
      setSelectedTicketForAi(updated);
    }
  };

  // Apply AI Copilot advice to active ticket
  const handleApplyAiAdvice = async (adviceText, ticket) => {
    try {
      const newNotes = ticket.diagnostic_notes
        ? `${ticket.diagnostic_notes}\n\n[Ohm]:\n${adviceText}`
        : `[Ohm]:\n${adviceText}`;

      const res = await authFetch(`${API_BASE}/tickets/${ticket.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diagnostic_notes: newNotes }),
      });

      if (res.ok) {
        const updated = await res.json();
        handleTicketUpdated(updated);
      }
    } catch (err) {
      console.error("Error applying AI advice:", err);
    }
  };

  return (
    <div className="workbench-layout technician-portal-root">
      {/* Top Header */}
      <TechnicianHeader isReadOnly={isReadOnly} />

      <main className="workbench-canvas technician-canvas">
        {/* KPI Summary Cards */}
        <section className="tech-kpi-row" aria-label="Métricas Rápidas Operativas">
          <button
            type="button"
            className={`tech-kpi-card ${kpiFilter === "activos" ? "is-active" : ""}`}
            onClick={() => handleKpiClick("activos")}
            aria-label="Filtrar por Mis Activos"
            data-testid="kpi-activos"
          >
            <div className="tech-kpi-info">
              <span className="tech-kpi-title">Mis Activos</span>
              <span className="tech-kpi-val accent">{kpis.activos}</span>
            </div>
            <Wrench size={22} className="tech-kpi-icon accent" />
          </button>

          <button
            type="button"
            className={`tech-kpi-card ${kpiFilter === "revision" ? "is-active" : ""}`}
            onClick={() => handleKpiClick("revision")}
            aria-label="Filtrar por En Revisión"
            data-testid="kpi-revision"
          >
            <div className="tech-kpi-info">
              <span className="tech-kpi-title">En Revisión</span>
              <span className="tech-kpi-val warning">{kpis.revision}</span>
            </div>
            <Clock size={22} className="tech-kpi-icon warning" />
          </button>

          <button
            type="button"
            className={`tech-kpi-card ${kpiFilter === "listos" ? "is-active" : ""}`}
            onClick={() => handleKpiClick("listos")}
            aria-label="Filtrar por Listos para Retiro"
            data-testid="kpi-listos"
          >
            <div className="tech-kpi-info">
              <span className="tech-kpi-title">Listos para Retiro</span>
              <span className="tech-kpi-val success">{kpis.listos}</span>
            </div>
            <CheckCircle2 size={22} className="tech-kpi-icon success" />
          </button>
        </section>

        {/* Action & Filter Toolbar */}
        <section className="tech-toolbar-card">
          {/* Tab Selector */}
          <div className="tech-tabs-nav" role="tablist" aria-label="Pestañas de Equipos">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "my_tickets"}
              className={`tech-tab-btn ${activeTab === "my_tickets" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("my_tickets");
                setKpiFilter(null);
              }}
              data-testid="tab-my-tickets"
            >
              <Wrench size={16} />
              <span>{isReadOnly ? "Todos los Asignados del Taller" : "Mis Asignaciones"}</span>
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "available_tickets"}
              className={`tech-tab-btn ${activeTab === "available_tickets" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("available_tickets");
                setKpiFilter(null);
              }}
              data-testid="tab-available-tickets"
            >
              <Inbox size={16} />
              <span>Equipos Disponibles</span>
            </button>
          </div>

          {/* Search, Filter & View Mode Controls */}
          <div className="tech-controls-row">
            <form onSubmit={handleSearchSubmit} className="tech-search-form">
              <div className="tech-search-wrapper">
                <Search size={16} className="tech-search-icon" />
                <input
                  type="text"
                  className="form-input tech-search-input"
                  placeholder="Buscar por marca, modelo, falla o #ticket..."
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  data-testid="tech-search-input"
                />
              </div>
            </form>

            <div className="tech-filter-group">
              <select
                className="form-input tech-status-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                aria-label="Filtrar por estado"
                data-testid="tech-status-filter"
              >
                {STATUS_FILTER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>

              {/* View Switcher: List vs 3-col Kanban */}
              <div className="view-mode-toggle tech-view-toggle">
                <button
                  type="button"
                  className={`view-mode-btn ${viewMode === "list" ? "is-active" : ""}`}
                  onClick={() => handleViewModeChange("list")}
                  aria-label="Vista de Lista"
                  data-testid="view-mode-list"
                >
                  <List size={16} />
                </button>
                <button
                  type="button"
                  className={`view-mode-btn ${viewMode === "kanban" ? "is-active" : ""}`}
                  onClick={() => handleViewModeChange("kanban")}
                  aria-label="Vista Tablero Kanban de 3 Columnas"
                  data-testid="view-mode-kanban"
                >
                  <LayoutGrid size={16} />
                </button>
              </div>

              <button
                type="button"
                className="btn-secondary tech-refresh-btn"
                onClick={() => refetchTickets()}
                disabled={isRefetching}
                title="Actualizar equipos"
                aria-label="Actualizar lista de equipos"
              >
                <RefreshCw size={15} className={isRefetching ? "spin-icon" : ""} />
              </button>
            </div>
          </div>
        </section>

        {/* Content Area */}
        {loadingTickets ? (
          <div className="tech-loading-state" data-testid="tech-loading-spinner">
            <div className="spinner" />
            <p>Cargando órdenes de trabajo...</p>
          </div>
        ) : displayedTickets.length === 0 ? (
          <div className="tech-empty-state" data-testid="tech-empty-state">
            <Inbox size={48} className="text-muted" />
            <h3>No se encontraron equipos</h3>
            <p>
              {activeTab === "available_tickets"
                ? "No hay órdenes pendientes de asignación en este momento."
                : "No tienes equipos asignados con los filtros seleccionados."}
            </p>
          </div>
        ) : viewMode === "list" ? (
          /* List View */
          <div className="tech-list-grid" data-testid="tech-list-view">
            {displayedTickets.map((ticket) => (
              <TechnicianTicketCard
                key={ticket.id}
                ticket={ticket}
                isAvailable={activeTab === "available_tickets"}
                isTaking={takingTicketId === ticket.id}
                onTakeTicket={handleTakeTicket}
                onOpenWorkModal={(t) => setSelectedTicketForWork(t)}
                slaThresholds={slaThresholds}
                isReadOnly={isReadOnly}
              />
            ))}
          </div>
        ) : (
          /* 3-Column Kanban Board View */
          <div className="tech-kanban-board" data-testid="tech-kanban-view">
            {TECH_KANBAN_COLUMNS.map((col) => {
              const colTickets = kanbanGroups[col.id] || [];
              return (
                <div key={col.id} className="tech-kanban-column" data-testid={`tech-kanban-col-${col.id}`}>
                  <header
                    className="tech-kanban-col-header"
                    style={{ borderTopColor: col.accentColor }}
                  >
                    <div className="tech-kanban-col-title-wrap">
                      <h4 className="tech-kanban-col-title">{col.title}</h4>
                      <span className="tech-kanban-count-badge">{colTickets.length}</span>
                    </div>
                  </header>

                  <div className="tech-kanban-cards-stack">
                    {colTickets.length === 0 ? (
                      <div className="tech-kanban-empty-slot">Sin equipos</div>
                    ) : (
                      colTickets.map((ticket) => (
                        <TechnicianTicketCard
                          key={ticket.id}
                          ticket={ticket}
                          isAvailable={activeTab === "available_tickets"}
                          isTaking={takingTicketId === ticket.id}
                          onTakeTicket={handleTakeTicket}
                          onOpenWorkModal={(t) => setSelectedTicketForWork(t)}
                          slaThresholds={slaThresholds}
                          isReadOnly={isReadOnly}
                        />
                      ))
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Floating AI Copilot FAB Bubble */}
      {!isReadOnly && (
        <AiChatBubble
          onClick={() => setIsAiDrawerOpen((prev) => !prev)}
          isOpen={isAiDrawerOpen}
          activeTicketContext={selectedTicketForAi}
        />
      )}

      {/* Slide-over AI Copilot Drawer */}
      {!isReadOnly && (
        <AiChatDrawer
          isOpen={isAiDrawerOpen}
          onClose={() => setIsAiDrawerOpen(false)}
          ticketContext={selectedTicketForAi}
          onClearTicketContext={() => setSelectedTicketForAi(null)}
          onApplyToDiagnosis={handleApplyAiAdvice}
        />
      )}

      {/* Technician Agile Work Modal */}
      {selectedTicketForWork && (
        <TechnicianWorkModal
          ticket={selectedTicketForWork}
          onClose={() => {
            setSelectedTicketForWork(null);
            setSelectedTicketForAi(null);
            setIsAiDrawerOpen(false);
          }}
          onStatusChange={(updated) => {
            handleTicketUpdated(updated);
            setSelectedTicketForWork(updated);
          }}
          onOpenAiCopilot={(t) => {
            setSelectedTicketForAi(t);
            setIsAiDrawerOpen(true);
          }}
          isReadOnly={isReadOnly}
        />
      )}
    </div>
  );
}
