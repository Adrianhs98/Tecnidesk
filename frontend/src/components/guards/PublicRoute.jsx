import { Navigate } from "react-router-dom";

// PublicRoute: si ya hay sesión activa, salta directo al /admin (no-op en /login)
export default function PublicRoute({ children }) {
  const token = sessionStorage.getItem("td_token");
  return token ? <Navigate to="/admin" replace /> : children;
}
