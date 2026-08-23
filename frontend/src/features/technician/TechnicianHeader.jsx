import { useNavigate } from "react-router-dom";
import { Wrench, LogOut, ShieldCheck } from "lucide-react";
import ThemeToggle from "../../components/shared/ThemeToggle";

export default function TechnicianHeader({ isReadOnly = false }) {
  const navigate = useNavigate();
  const techName = sessionStorage.getItem("td_user_name") || "Técnico";
  const shopName = sessionStorage.getItem("td_shop") || "TecniDesk Taller";
  const userRole = sessionStorage.getItem("td_role") || "technician";
  const showSupervisorBadge = isReadOnly || userRole === "admin";

  const handleLogout = () => {
    window.dispatchEvent(new Event("auth:logout"));
    navigate("/login");
  };

  return (
    <header className="nav-pill technician-nav-pill" role="banner">
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
        <div className="technician-brand-info">
          <span className="admin-title">{shopName}</span>
          <div className="technician-user-badge-wrap">
            {showSupervisorBadge ? (
              <span className="badge-supervisor" data-testid="supervisor-role-badge">
                <ShieldCheck size={12} className="supervisor-badge-icon" />
                Modo Supervisor (Solo Lectura)
              </span>
            ) : (
              <span className="badge-tech" data-testid="tech-role-badge">
                <Wrench size={12} className="tech-badge-icon" />
                Técnico
              </span>
            )}
            <span className="technician-user-name" title={techName}>
              {techName}
            </span>
          </div>
        </div>
      </div>

      <div className="nav-pill-actions">
        <ThemeToggle />
        <button
          type="button"
          className="btn-danger"
          onClick={handleLogout}
          aria-label="Cerrar sesión"
        >
          <LogOut size={15} className="inline-icon" />
          <span>Cerrar Sesión</span>
        </button>
      </div>
    </header>
  );
}
