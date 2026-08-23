import { useEffect, useState, useCallback, useRef, useMemo, Suspense, lazy, useTransition } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Info, Users, List, LayoutGrid, Sliders, BarChart3 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { authFetch } from "../../api/authFetch";
import { API_BASE } from "../../api/config";
import { fetchSlaConfig } from "../../api/shop";
import AdminTicketCard from "./components/AdminTicketCard";
import KanbanBoard from "./components/KanbanBoard";
import ThemeToggle from "../../components/shared/ThemeToggle";

const TicketSuccessModal = lazy(() => import("../../components/shared/TicketSuccessModal"));
const NewTicketModal = lazy(() => import("./components/NewTicketModal"));
const InventoryModal = lazy(() => import("./components/InventoryModal"));
const TechniciansModal = lazy(() => import("./components/TechniciansModal"));
const SlaSettingsModal = lazy(() => import("./components/SlaSettingsModal"));
const CycleTimeAnalyticsModal = lazy(() => import("./components/CycleTimeAnalyticsModal"));

// Estados que NO cuentan como "activos en taller"
const ESTADOS_INACTIVOS = ["LISTO_PARA_RETIRAR", "NO_APROBADO"];

export default function AdminDashboard() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [page, setPage] = useState(0);
  const [limit, setLimit] = useState(15);
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState("");
  const [kpiFilter, setKpiFilter] = useState(null); // null | 'activos' | 'listos' | 'espera'

  const { data, isLoading: loading, isError, error: queryError, refetch: fetchData } = useQuery({
    queryKey: ['dashboardData', page, limit, searchQuery, dateFilter, kpiFilter],
    queryFn: async () => {
      const skip = page * limit;
      let url = `${API_BASE}/tickets?skip=${skip}&limit=${limit}`;
      if (searchQuery) {
        url += `&search=${encodeURIComponent(searchQuery.trim())}`;
      }
      if (dateFilter) {
        url += `&date_range=${encodeURIComponent(dateFilter)}`;
      }

      // Map KPI filter to backend parameters
      if (kpiFilter === 'listos') {
        url += `&ticket_status=LISTO_PARA_RETIRAR`;
      } else if (kpiFilter === 'espera') {
        url += `&ticket_status=EN_ESPERA_INGRESO`;
      } else if (kpiFilter === 'activos') {
        url += `&filter_group=activos`;
      }
      
      const ticketsRes = await authFetch(url);
      if (!ticketsRes.ok) {
        const error = new Error(ticketsRes.statusText || "Error al cargar tickets");
        error.status = ticketsRes.status;
        throw error;
      }
      const ticketsData = await ticketsRes.json();

      let statsData = { total: 0, activos: 0, listos: 0, espera: 0 };
      try {
        const statsRes = await authFetch(`${API_BASE}/tickets/stats`);
        if (statsRes.ok) {
          statsData = await statsRes.json();
        }
      } catch (err) {
        console.warn("Las estadísticas fallaron, procediendo de forma controlada:", err);
      }

      return {
        tickets: ticketsData.items || [],
        totalItems: ticketsData.total || 0,
        stats: statsData,
      };
    }
  });

  const tickets = data?.tickets || [];
  const totalItems = data?.totalItems || 0;
  const stats = data?.stats || { total: 0, activos: 0, listos: 0, espera: 0 };
  
  let errorMsg = null;
  if (isError) {
    if (queryError?.status === 401) {
      errorMsg = "Tu sesión ha expirado. Por favor, inicia sesión nuevamente.";
    } else if (queryError?.status === 402) {
      errorMsg = "Tu suscripción al servicio ha expirado. Contacta a soporte para reactivar tu cuenta.";
    } else if (queryError?.status === 403) {
      errorMsg = "No tienes permisos suficientes para acceder a esta área.";
    } else if (queryError?.status >= 500) {
      errorMsg = "El servidor experimentó un error interno. Por favor, intenta de nuevo más tarde.";
    } else {
      errorMsg = "No se pudo cargar la información. Verifica tu conexión a internet.";
    }
  }

  const { data: slaConfigData } = useQuery({
    queryKey: ['shopSlaConfig'],
    queryFn: fetchSlaConfig,
    staleTime: 1000 * 60 * 10,
  });
  const slaThresholds = slaConfigData?.effective_thresholds || null;

  const [showModal, setShowModal] = useState(false);
  const [showSlaSettings, setShowSlaSettings] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [createdTicket, setCreatedTicket] = useState(null);
  const [isPending, startTransition] = useTransition();
  const [exactDate, setExactDate] = useState("");
  const [showInventory, setShowInventory] = useState(false);
  const [showTechnicians, setShowTechnicians] = useState(false);
  const [viewMode, setViewMode] = useState(() => {
    try {
      return localStorage.getItem("tecnidesk_workbench_view") || "list";
    } catch {
      return "list";
    }
  });

  const handleViewModeChange = (mode) => {
    setViewMode(mode);
    try {
      localStorage.setItem("tecnidesk_workbench_view", mode);
    } catch {
      // ignore
    }
  };

  const handleLogout = () => {
    window.dispatchEvent(new Event("auth:logout"));
    navigate("/login");
  };

  const handleKpiClick = (targetFilter) => {
    startTransition(() => {
      setKpiFilter(prev => (prev === targetFilter ? null : targetFilter));
      setPage(0);
    });
  };

  // Optimistic update al CREAR: +1 total, +1 activos, +1 espera (estado inicial)
  const handleTicketCreated = (newTicket) => {
    setShowModal(false);
    queryClient.setQueryData(['dashboardData', page, limit, searchQuery, dateFilter, kpiFilter], (old) => {
      if (!old) return old;
      return {
        ...old,
        tickets: [newTicket, ...old.tickets],
        stats: {
          ...old.stats,
          total: old.stats.total + 1,
          activos: old.stats.activos + 1,
          espera: old.stats.espera + 1,
        }
      };
    });
    setCreatedTicket(newTicket);
  };

  // Optimistic update al CAMBIAR ESTADO: recalcula deltas sin re-fetch
  const handleStatusChange = useCallback((updated) => {
    queryClient.setQueryData(['dashboardData', page, limit, searchQuery, dateFilter, kpiFilter], (oldData) => {
      if (!oldData) return oldData;

      const oldTicket = oldData.tickets.find((t) => t.id === updated.id);
      if (!oldTicket) return oldData;

      const newTickets = oldData.tickets.map((t) => (t.id === updated.id ? { ...t, ...updated } : t));

      const oldStatus = oldTicket.status;
      const newStatus = updated.status;

      const deltaActivos =
        (!ESTADOS_INACTIVOS.includes(newStatus) ? 1 : 0) -
        (!ESTADOS_INACTIVOS.includes(oldStatus) ? 1 : 0);
      const deltaListos =
        (newStatus === "LISTO_PARA_RETIRAR" ? 1 : 0) -
        (oldStatus === "LISTO_PARA_RETIRAR" ? 1 : 0);
      const deltaEspera =
        (newStatus === "EN_ESPERA_INGRESO" ? 1 : 0) -
        (oldStatus === "EN_ESPERA_INGRESO" ? 1 : 0);

      return {
        ...oldData,
        tickets: newTickets,
        stats: {
          ...oldData.stats,
          activos: Math.max(0, oldData.stats.activos + deltaActivos),
          listos: Math.max(0, oldData.stats.listos + deltaListos),
          espera: Math.max(0, oldData.stats.espera + deltaEspera),
        }
      };
    });
  }, [queryClient, page, limit, searchQuery, dateFilter, kpiFilter]);

  const hasActiveFilters = Boolean(searchQuery.trim() || exactDate || kpiFilter);
  const filteredTickets = tickets;

  return (
    <div className="workbench-layout">
      <div className="nav-pill">
        <div className="nav-pill-brand">
          <img src="/logo.png" alt="Logo" onError={(e) => { e.target.style.display = "none"; }} width={24} height={24} className="workbench-logo" />
          <div className="admin-logo-dot" />
          <div>
            <span className="admin-title">{sessionStorage.getItem("td_shop") || "TecniDesk Admin"}</span>
          </div>
        </div>
        <div className="nav-pill-actions">
          <button className="btn-secondary" onClick={() => setShowAnalyticsModal(true)}>
            <BarChart3 size={16} className="inline-icon" /> Métricas y Tiempos
          </button>
          <button className="btn-secondary" onClick={() => setShowSlaSettings(true)}>
            <Sliders size={16} className="inline-icon" /> Configurar SLAs
          </button>
          <button className="btn-secondary" onClick={() => setShowTechnicians(true)}>
            <Users size={16} className="inline-icon" /> Técnicos
          </button>
          <button className="btn-secondary" onClick={() => setShowInventory(true)}>
            📦 Inventario
          </button>
          <ThemeToggle />
          <button className="btn-new-ticket" onClick={() => setShowModal(true)}>
            Ingresar Equipo
          </button>
          <button className="btn-danger" onClick={handleLogout}>
            Cerrar Sesion
          </button>
        </div>
      </div>

      <div className="workbench-canvas">
        <div className="admin-stats-row">
          <button 
            type="button"
            className={`admin-stat-card ${kpiFilter === null ? 'is-active' : ''}`}
            onClick={() => handleKpiClick(null)}
            aria-label="Ver todos los equipos"
          >
            <div className="admin-stat-label">Total equipos</div>
            <div className="admin-stat-value accent">{stats.total}</div>
          </button>

          <button 
            type="button"
            className={`admin-stat-card ${kpiFilter === 'activos' ? 'is-active' : ''}`}
            onClick={() => handleKpiClick('activos')}
            aria-label="Filtrar equipos en taller"
          >
            <div className="admin-stat-label">En taller</div>
            <div className="admin-stat-value">{stats.activos}</div>
          </button>

          <button 
            type="button"
            className={`admin-stat-card ${kpiFilter === 'listos' ? 'is-active' : ''}`}
            onClick={() => handleKpiClick('listos')}
            aria-label="Filtrar equipos listos para retirar"
          >
            <div className="admin-stat-label">Listos</div>
            <div className="admin-stat-value success">{stats.listos}</div>
          </button>

          <button 
            type="button"
            className={`admin-stat-card ${kpiFilter === 'espera' ? 'is-active' : ''}`}
            onClick={() => handleKpiClick('espera')}
            aria-label="Filtrar equipos en espera"
          >
            <div className="admin-stat-label">En espera</div>
            <div className="admin-stat-value warning">{stats.espera}</div>
          </button>
        </div>

        <div className="workbench-toolbar">
          <div className="workbench-toolbar-search">
            <input 
              className="form-input search-input" 
              type="text" 
              placeholder="Buscar por nombre, marca o codigo..." 
              value={searchInput} 
              onChange={(e) => {
                setSearchInput(e.target.value);
                startTransition(() => setSearchQuery(e.target.value));
              }} 
            />
          </div>
          <div className="workbench-toolbar-filters">
            <div className="view-mode-toggle" role="group" aria-label="Modo de vista">
              <button
                type="button"
                className={`view-mode-btn ${viewMode === "list" ? "is-active" : ""}`}
                onClick={() => handleViewModeChange("list")}
                aria-label="Vista Lista"
                title="Vista Lista"
              >
                <List size={14} />
                <span>Lista</span>
              </button>
              <button
                type="button"
                className={`view-mode-btn ${viewMode === "kanban" ? "is-active" : ""}`}
                onClick={() => handleViewModeChange("kanban")}
                aria-label="Vista Tablero Kanban"
                title="Vista Tablero Kanban"
              >
                <LayoutGrid size={14} />
                <span>Tablero</span>
              </button>
            </div>

            <input 
              type="date" 
              className="form-input" 
              value={exactDate} 
              onChange={(e) => {
                const val = e.target.value;
                startTransition(() => {
                  setExactDate(val);
                  setDateFilter(val ? `${val},${val}` : "");
                  setPage(0);
                });
              }} 
              title="Filtrar por dia exacto" 
            />
            {exactDate && (
              <button 
                className="btn-secondary" 
                onClick={() => startTransition(() => {
                  setExactDate("");
                  setDateFilter("");
                  setPage(0);
                })} 
                title="Limpiar fecha exacta"
              >
                Limpiar fecha
              </button>
            )}
            <button 
              className="btn-secondary" 
              onClick={fetchData} 
              disabled={loading}
            >
              Actualizar
            </button>
          </div>
        </div>

        {hasActiveFilters && (
          <div className="workbench-active-filters">
            <span className="workbench-active-filters-title">Filtros activos</span>
            {kpiFilter && (
              <span className="workbench-filter-pill">
                Filtro: {kpiFilter === 'activos' ? 'En taller' : kpiFilter === 'listos' ? 'Listos' : 'En espera'}
              </span>
            )}
            {searchQuery.trim() && (
              <span className="workbench-filter-pill">
                Busqueda: {searchQuery.trim()}
              </span>
            )}
            {exactDate && (
              <span className="workbench-filter-pill">
                Fecha: {exactDate}
              </span>
            )}
            <button
              className="btn-secondary workbench-clear-btn"
              onClick={() => {
                setSearchInput("");
                startTransition(() => {
                  setSearchQuery("");
                  setDateFilter("");
                  setExactDate("");
                  setKpiFilter(null);
                  setPage(0);
                });
              }}
            >
              Limpiar filtros
            </button>
          </div>
        )}

        {errorMsg && (
          <div className="admin-error-bar">
            <span>ERROR</span> {errorMsg}
            <button className="btn-secondary" style={{ marginLeft: "auto", padding: "6px 12px", fontSize: 12 }} onClick={fetchData}>
              Reintentar
            </button>
          </div>
        )}

        {loading && !errorMsg && (
          <div className="admin-loading">
            <div className="spinner" />
            Cargando equipos...
          </div>
        )}

        {!loading && !errorMsg && tickets.length === 0 && (
          <div className="admin-empty">
            <div className="admin-empty-icon"><Info size={40} color="var(--accent)" /></div>
            <div className="admin-empty-title">No hay equipos registrados aun</div>
            <div className="admin-empty-sub">Ingresa el primer equipo para comenzar a gestionar tu taller.</div>
            <button className="btn-new-ticket" onClick={() => setShowModal(true)}>
              Ingresar primer equipo
            </button>
          </div>
        )}

        {!loading && !errorMsg && tickets.length > 0 && filteredTickets.length === 0 && (
          <div className="admin-empty">
            <div className="admin-empty-icon"><Info size={40} color="var(--accent)" /></div>
            <div className="admin-empty-title">No se encontraron equipos</div>
            <div className="admin-empty-sub">
              Ajusta la busqueda o limpia los filtros para volver a ver resultados.
            </div>
            <button
              className="btn-secondary"
              onClick={() => {
                setSearchInput("");
                startTransition(() => {
                  setSearchQuery("");
                  setDateFilter("");
                  setExactDate("");
                  setKpiFilter(null);
                  setPage(0);
                });
              }}
            >
              Limpiar filtros
            </button>
          </div>
        )}

        {!loading && filteredTickets.length > 0 && (
          <div className="workbench-content">
            {viewMode === "kanban" ? (
              <KanbanBoard tickets={filteredTickets} onStatusChange={handleStatusChange} slaThresholds={slaThresholds} />
            ) : (
              <div className="tickets-grid">
                {filteredTickets.map((ticket) => (
                  <AdminTicketCard key={ticket.id} ticket={ticket} onStatusChange={handleStatusChange} slaThresholds={slaThresholds} />
                ))}
              </div>
            )}
            <div className="workbench-pagination">
              <button 
                className="btn-secondary" 
                disabled={page === 0} 
                onClick={() => setPage(p => p - 1)}
              >
                Anterior
              </button>
              <span className="workbench-pagination-text">
                Página {page + 1} de {Math.max(1, Math.ceil(totalItems / limit))} ({totalItems} totales)
              </span>
              <select
                className="form-input"
                style={{ width: "auto", display: "inline-block", margin: "0 10px" }}
                value={limit}
                onChange={(e) => {
                  setLimit(Number(e.target.value));
                  setPage(0);
                }}
                title="Límite por página"
              >
                <option value={10}>10 / pág</option>
                <option value={15}>15 / pág</option>
                <option value={20}>20 / pág</option>
                <option value={50}>50 / pág</option>
              </select>
              <button 
                className="btn-secondary" 
                disabled={(page + 1) * limit >= totalItems} 
                onClick={() => setPage(p => p + 1)}
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>

      <Suspense fallback={<div className="modal-overlay"><div className="spinner" /></div>}>
        {showModal && <NewTicketModal onClose={() => setShowModal(false)} onCreated={handleTicketCreated} />}
        {showAnalyticsModal && <CycleTimeAnalyticsModal onClose={() => setShowAnalyticsModal(false)} />}
        {showSlaSettings && <SlaSettingsModal onClose={() => setShowSlaSettings(false)} />}
        {showInventory && <InventoryModal onClose={() => setShowInventory(false)} />}
        {showTechnicians && <TechniciansModal onClose={() => setShowTechnicians(false)} />}
        {createdTicket && <TicketSuccessModal ticket={createdTicket} onClose={() => setCreatedTicket(null)} />}
      </Suspense>
    </div>
  );
}
