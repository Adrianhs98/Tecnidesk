import { Suspense, lazy, useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import "./App.css";
import { ThemeProvider } from "./context/ThemeContext";
import ProtectedRoute from "./components/guards/ProtectedRoute";
import PublicRoute from "./components/guards/PublicRoute";

const AdminDashboard = lazy(() => import("./features/admin/AdminDashboard"));
const TechnicianDashboard = lazy(() => import("./features/technician/TechnicianDashboard"));
const ForgotPasswordPage = lazy(() => import("./pages/ForgotPasswordPage"));
const HomePage = lazy(() => import("./pages/HomePage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const ResetPasswordPage = lazy(() => import("./pages/ResetPasswordPage"));
const TrackingPortal = lazy(() => import("./pages/TrackingPortal"));

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5, // 5 minutos de cache
      retry: (failureCount, error) => {
        // No reintentar errores de autenticación/suscripción
        if (error?.status >= 400 && error?.status < 500) return false;
        // Reintentar red/500 máximo 2 veces
        return failureCount < 2;
      }
    },
  },
});

export default function App() {
  useEffect(() => {
    const handleLogoutEvent = () => {
      queryClient.clear();
      sessionStorage.clear();
    };
    window.addEventListener("auth:logout", handleLogoutEvent);
    return () => window.removeEventListener("auth:logout", handleLogoutEvent);
  }, []);

  return (
    <ThemeProvider>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
      <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', color: 'var(--accent)' }}><div className="spinner" /></div>}>
        <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/track/:token" element={<TrackingPortal />} />
        <Route path="/tracking/:token" element={<TrackingPortal />} />
        <Route
          path="/login"
          element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <PublicRoute>
              <ForgotPasswordPage />
            </PublicRoute>
          }
        />
        <Route
          path="/reset-password"
          element={
            <PublicRoute>
              <ResetPasswordPage />
            </PublicRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/tech"
          element={
            <ProtectedRoute allowedRoles={['admin', 'technician']}>
              <TechnicianDashboard />
            </ProtectedRoute>
          }
        />
        </Routes>
      </Suspense>
    </BrowserRouter>
    </QueryClientProvider>
    </ThemeProvider>
  );
}
