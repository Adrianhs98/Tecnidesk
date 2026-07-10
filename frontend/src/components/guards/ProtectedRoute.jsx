import { Navigate } from "react-router-dom";

// ProtectedRoute: solo entra si hay token activo, si no → /login
export default function ProtectedRoute({ children }) {
  const token = sessionStorage.getItem("td_token");
  return token ? children : <Navigate to="/login" replace />;
}
