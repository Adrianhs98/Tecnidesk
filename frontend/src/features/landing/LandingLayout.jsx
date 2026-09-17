import { Link } from "react-router-dom";
import LogoBadge from "../../components/shared/LogoBadge";
import ThemeToggle from "../../components/shared/ThemeToggle";
import LandingAmbientTech from "./components/LandingAmbientTech";

export default function LandingLayout({ children }) {
  return (
    <div className="landing-page-root" id="top">
      {/* ─── Global Ambient Tech Neural Network ─────────────────────────── */}
      <LandingAmbientTech />

      {/* ─── Sticky Glass Navbar ────────────────────────────────────────── */}
      <header className="landing-navbar">
        <div className="landing-container">
          <div className="landing-nav-inner">
            <a
              href="#top"
              className="landing-nav-logo-link"
              aria-label="TecniDesk Inicio"
              onClick={(e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              <LogoBadge businessName="TecniDesk" subtitle="Piloto 2026" />
            </a>

            <nav className="landing-nav-links">
              <a href="#solucion" className="landing-nav-link">El Taller Real</a>
              <a href="#workbench" className="landing-nav-link">Workbench Demo</a>
              <a href="#ohm" className="landing-nav-link">Ohm Copiloto</a>
              <a href="#piloto" className="landing-nav-link">Programa Piloto</a>
            </nav>

            <div className="landing-nav-actions">
              <ThemeToggle />
              <a href="#postular" className="landing-btn landing-btn-primary landing-btn-sm">
                Postular Taller
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* ─── Main Content ──────────────────────────────────────────────── */}
      <main className="landing-main">
        {children}
      </main>

      {/* ─── Footer ────────────────────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="landing-container">
          <div className="landing-footer-grid">
            <div className="landing-footer-brand">
              <LogoBadge businessName="TecniDesk" subtitle="Software para Talleres" />
              <p>
                Diseñado para elevar la rentabilidad, velocidad y orden operativo de talleres de tecnología en Ecuador.
              </p>
            </div>

            <div className="landing-footer-links">
              <a href="#solucion" className="landing-footer-link">Beneficios</a>
              <a href="#ohm" className="landing-footer-link">Copiloto Ohm</a>
              <a href="#piloto" className="landing-footer-link">Plan Piloto</a>
              <Link to="/login" className="landing-footer-link">Acceso Talleres</Link>
              <Link to="/" className="landing-footer-link">Rastreo de Clientes</Link>
            </div>
          </div>

          <div style={{
            marginTop: "2.5rem",
            paddingTop: "1.5rem",
            borderTop: "1px solid var(--border-subtle)",
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: "0.8125rem",
            color: "var(--text-tertiary)",
            gap: "1rem"
          }}>
            <div>
              &copy; {new Date().getFullYear()} TecniDesk. Convocatoria piloto para Guayaquil y Santa Elena.
            </div>
            <div>
              Arquitectura multi-tenant segura con cifrado de PINs
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
