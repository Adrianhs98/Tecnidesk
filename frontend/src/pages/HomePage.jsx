import { useState } from "react";
import { useNavigate } from "react-router-dom";
import LogoBadge from "../components/shared/LogoBadge";

export default function HomePage() {
  const [token, setToken] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = token.trim();
    if (trimmed) navigate(`/tracking/${trimmed}`);
  };

  return (
    <div className="portal">
      <div className="header">
        <LogoBadge />
        <h1>
          Que esta pasando con
          <br />
          <span>tu equipo?</span>
        </h1>
        <p>
          Ingresa el codigo de rastreo que recibiste por correo
          <br />
          para ver el estado en tiempo real de tu reparacion.
        </p>
      </div>

      <div className="search-card">
        <label className="search-label">Codigo de rastreo</label>
        <form className="search-row" onSubmit={handleSubmit}>
          <input
            className="search-input"
            type="text"
            placeholder="Pega aqui el codigo de tu ticket"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            spellCheck={false}
            autoComplete="off"
          />
          <button className="search-btn" type="submit" disabled={!token.trim()}>
            Consultar
          </button>
        </form>
      </div>

      <div className="powered">
        Impulsado por <span>TecniDesk</span>
      </div>
    </div>
  );
}
