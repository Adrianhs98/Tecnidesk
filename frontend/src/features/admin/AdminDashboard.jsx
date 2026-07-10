import { useEffect, useState, useCallback, useRef } from "react";
import { Info } from "lucide-react";
import { useNavigate } from "react-router-dom";
import TicketSuccessModal from "../../components/shared/TicketSuccessModal";
import { authFetch } from "../../api/authFetch";
import { API_BASE } from "../../api/config";
import NewTicketModal from "./components/NewTicketModal";
import AdminTicketCard from "./components/AdminTicketCard";

// Estados que NO cuentan como "activos en taller"
const ESTADOS_INACTIVOS = ["LISTO_PARA_RETIRAR", "NO_APROBADO"];

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ total: 0, activos: 0, listos: 0, espera: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [createdTicket, setCreatedTicket] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFilter, setDateFilter] = useState("all");
  const [exactDate, setExactDate] = useState("");

  // Ref para acceder al estado actual de tickets dentro de callbacks sin dependencias
  const ticketsRef = useRef(tickets);
  useEffect(() => { ticketsRef.current = tickets; }, [tickets]);

  // Carga paralela: tickets + stats en un solo viaje de red (zero waterfall)
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ticketsRes, statsRes] = await Promise.all([
        authFetch(`${API_BASE}/tickets`),
        authFetch(`${API_BASE}/tickets/stats`),
      ]);
      if (!ticketsRes.ok) throw new Error(`Error ${ticketsRes.status}`);
      if (!statsRes.ok) throw new Error(`Error stats ${statsRes.status}`);

      const ticketsData = await ticketsRes.json();
      const statsData = await statsRes.json();

      setTickets(Array.isArray(ticketsData) ? ticketsData : ticketsData.tickets ?? []);
      setStats(statsData);
    } catch (err) {
      setError("No se pudo cargar la lista de equipos. " + (err.message || ""));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleLogout = () => {
    sessionStorage.clear();
    navigate("/login");
  };

  // Optimistic update al CREAR: +1 total, +1 activos, +1 espera (estado inicial)
  const handleTicketCreated = (newTicket) => {
    setShowModal(false);
    setTickets((prev) => [newTicket, ...prev]);
    setStats((prev) => ({
      ...prev,
      total: prev.total + 1,
      activos: prev.activos + 1,
      espera: prev.espera + 1,
    }));
    setCreatedTicket(newTicket);
  };

  // Optimistic update al CAMBIAR ESTADO: recalcula deltas sin re-fetch
  const handleStatusChange = (updated) => {
    const old = ticketsRef.current.find((t) => t.id === updated.id);

    setTickets((prev) =>
      prev.map((t) => (t.id === updated.id ? { ...t, ...updated } : t))
    );

    if (old) {
      const oldStatus = old.status;
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

      setStats((prev) => ({
        ...prev,
        activos: Math.max(0, prev.activos + deltaActivos),
        listos: Math.max(0, prev.listos + deltaListos),
        espera: Math.max(0, prev.espera + deltaEspera),
      }));
    }
  };

  const startOf = (dateValue) => {
    const result = new Date(dateValue);
    result.setHours(0, 0, 0, 0);
    return result;
  };

  const parseLocalDateInput = (value) => {
    if (!value) return null;
    const [year, month, day] = value.split("-").map(Number);
    return new Date(year, month - 1, day);
  };

  const hasActiveFilters = Boolean(searchQuery.trim() || dateFilter !== "all" || exactDate);

  const query = searchQuery.toLowerCase().trim();
  const now = new Date();
  const filteredTickets = tickets.filter((t) => {
    if (query) {
      const name = (t.customer?.full_name || t._frontendName || t.client_email || "").toLowerCase();
      const brand = (t.device_brand || "").toLowerCase();
      const model = (t.device_model || "").toLowerCase();
      const token = (t.tracking_token || "").toLowerCase();
      const phone = (t.customer?.phone_number || t._frontendPhone || "").toLowerCase();
      const email = (t.client_email || t.customer?.email || "").toLowerCase();
      if (!name.includes(query) && !brand.includes(query) && !model.includes(query) && !token.includes(query) && !phone.includes(query) && !email.includes(query)) return false;
    }

    if (dateFilter !== "all" && t.created_at) {
      const created = new Date(t.created_at);
      if (dateFilter === "today" && created < startOf(now)) return false;
      if (dateFilter === "yesterday") {
        const yStart = startOf(now);
        yStart.setDate(yStart.getDate() - 1);
        const yEnd = startOf(now);
        if (created < yStart || created >= yEnd) return false;
      }
      if (dateFilter === "week") {
        const wStart = startOf(now);
        wStart.setDate(wStart.getDate() - wStart.getDay());
        if (created < wStart) return false;
      }
      if (dateFilter === "month") {
        const mStart = new Date(now.getFullYear(), now.getMonth(), 1);
        if (created < mStart) return false;
      }
    }

    if (exactDate && t.created_at) {
      const created = new Date(t.created_at);
      const selected = parseLocalDateInput(exactDate);
      if (created.getFullYear() !== selected.getFullYear() || created.getMonth() !== selected.getMonth() || created.getDate() !== selected.getDate()) return false;
    }

    return true;
  });

  return (
    <div className="admin-layout">
      <div className="admin-topbar">
        <div className="admin-topbar-left">
          <img src="/logo.png" alt="Logo del taller" onError={(e) => { e.target.style.display = "none"; }} style={{ width: 28, height: 28, objectFit: "contain", borderRadius: 6, flexShrink: 0 }} />
          <div className="admin-logo-dot" />
          <div>
            <span className="admin-title">TecniDesk Admin</span>
            <span className="admin-subtitle"> | Panel de Control</span>
          </div>
        </div>
        <div className="admin-topbar-right">
          <button className="btn-new-ticket" onClick={() => setShowModal(true)}>Ingresar Equipo</button>
          <button className="btn-danger" onClick={handleLogout}>Cerrar Sesion</button>
        </div>
      </div>

      <div className="admin-body">
        <div className="admin-stats-row">
          <div className="admin-stat-card" style={{ position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 4, background: "var(--border)" }} />
            <div className="admin-stat-label">Total equipos</div>
            <div className="admin-stat-value accent">{stats.total}</div>
          </div>
          <div className="admin-stat-card" style={{ position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 4, background: "var(--info)" }} />
            <div className="admin-stat-label">En taller</div>
            <div className="admin-stat-value">{stats.activos}</div>
          </div>
          <div className="admin-stat-card" style={{ position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 4, background: "var(--success)" }} />
            <div className="admin-stat-label">Listos</div>
            <div className="admin-stat-value success">{stats.listos}</div>
          </div>
          <div className="admin-stat-card" style={{ position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, left: 0, width: "100%", height: 4, background: "var(--danger)" }} />
            <div className="admin-stat-label">En espera</div>
            <div className="admin-stat-value warning">{stats.espera}</div>
          </div>
        </div>

        <div className="admin-section-header">
          <div>
            <div className="admin-section-title">Equipos en el Taller</div>
            <div className="admin-section-sub">{loading ? "Cargando..." : `${filteredTickets.length} equipo${filteredTickets.length !== 1 ? "s" : ""} mostrado${filteredTickets.length !== 1 ? "s" : ""}`}</div>
          </div>
        </div>

        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap", alignItems: "center" }}>
          <input className="form-input" type="text" placeholder="Buscar por nombre, marca o codigo..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} style={{ flex: 1, minWidth: 180, fontSize: 13, padding: "11px 16px" }} />
          <select className="status-select" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} style={{ minWidth: 148, fontSize: 13, padding: "11px 14px" }}>
            <option value="all">Todos los tiempos</option>
            <option value="today">Hoy</option>
            <option value="yesterday">Ayer</option>
            <option value="week">Esta semana</option>
            <option value="month">Este mes</option>
          </select>
          <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
            <input type="date" className="form-input" value={exactDate} onChange={(e) => setExactDate(e.target.value)} style={{ minWidth: 148, fontSize: 13, padding: "11px 14px", colorScheme: "dark" }} title="Filtrar por dia exacto" />
          </div>
          {exactDate && (
            <button className="btn-secondary" onClick={() => setExactDate("")} style={{ fontSize: 12, padding: "11px 10px", whiteSpace: "nowrap" }} title="Limpiar fecha exacta">
              Limpiar fecha
            </button>
          )}
          <button className="btn-secondary" onClick={fetchData} disabled={loading}>Actualizar</button>
        </div>

        {hasActiveFilters && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              flexWrap: "wrap",
              marginBottom: 16,
              padding: "12px 14px",
              background: "rgba(201,167,106,0.08)",
              border: "1px solid rgba(201,167,106,0.18)",
              borderRadius: 12,
              color: "var(--text2)",
              fontSize: 12,
            }}
          >
            <span style={{ fontWeight: 600, color: "var(--accent)" }}>Filtros activos</span>
            {searchQuery.trim() && (
              <span style={{ padding: "4px 8px", borderRadius: 999, background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
                Busqueda: {searchQuery.trim()}
              </span>
            )}
            {dateFilter !== "all" && (
              <span style={{ padding: "4px 8px", borderRadius: 999, background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
                Rango: {dateFilter}
              </span>
            )}
            {exactDate && (
              <span style={{ padding: "4px 8px", borderRadius: 999, background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)" }}>
                Fecha: {exactDate}
              </span>
            )}
            <button
              className="btn-secondary"
              onClick={() => {
                setSearchQuery("");
                setDateFilter("all");
                setExactDate("");
              }}
              style={{ marginLeft: "auto", padding: "6px 12px", fontSize: 12 }}
            >
              Limpiar filtros
            </button>
          </div>
        )}

        {error && (
          <div className="admin-error-bar">
            <span>ERROR</span> {error}
            <button className="btn-secondary" style={{ marginLeft: "auto", padding: "6px 12px", fontSize: 12 }} onClick={fetchData}>
              Reintentar
            </button>
          </div>
        )}

        {loading && (
          <div className="admin-loading">
            <div className="spinner" />
            Cargando equipos...
          </div>
        )}

        {!loading && !error && tickets.length === 0 && (
          <div className="admin-empty">
            <div className="admin-empty-icon"><Info size={40} color="var(--accent)" /></div>
            <div className="admin-empty-title">No hay equipos registrados aun</div>
            <div className="admin-empty-sub" style={{ marginBottom: 20 }}>Ingresa el primer equipo para comenzar a gestionar tu taller.</div>
            <button className="btn-new-ticket" onClick={() => setShowModal(true)} style={{ width: "auto", margin: "0 auto" }}>
              Ingresar primer equipo
            </button>
          </div>
        )}

        {!loading && !error && tickets.length > 0 && filteredTickets.length === 0 && (
          <div className="admin-empty">
            <div className="admin-empty-icon"><Info size={40} color="var(--accent)" /></div>
            <div className="admin-empty-title">No se encontraron equipos</div>
            <div className="admin-empty-sub" style={{ marginBottom: 20 }}>
              Ajusta la busqueda o limpia los filtros para volver a ver resultados.
            </div>
            <button
              className="btn-secondary"
              onClick={() => {
                setSearchQuery("");
                setDateFilter("all");
                setExactDate("");
              }}
              style={{ width: "auto", margin: "0 auto" }}
            >
              Limpiar filtros
            </button>
          </div>
        )}

        {!loading && filteredTickets.length > 0 && (
          <div className="tickets-grid">
            {filteredTickets.map((ticket) => (
              <AdminTicketCard key={ticket.id} ticket={ticket} onStatusChange={handleStatusChange} />
            ))}
          </div>
        )}
      </div>

      {showModal && <NewTicketModal onClose={() => setShowModal(false)} onCreated={handleTicketCreated} />}
      {createdTicket && <TicketSuccessModal ticket={createdTicket} onClose={() => setCreatedTicket(null)} />}
    </div>
  );
}
