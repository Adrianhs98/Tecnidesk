import { Navigate } from "react-router-dom";

// ProtectedRoute: solo entra si hay token activo, si no → /login
export default function ProtectedRoute({ children, allowedRoles }) {
  const token = sessionStorage.getItem("td_token");
  const userRole = sessionStorage.getItem("td_role") || "admin";

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && Array.isArray(allowedRoles) && !allowedRoles.includes(userRole)) {
    if (userRole === "technician") {
      return <Navigate to="/tech" replace />;
    }
    return <Navigate to="/admin" replace />;
  }

  return children;
}
