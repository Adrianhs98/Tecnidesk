import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AdminAnalyticsPage from '../../pages/AdminAnalyticsPage';
import * as ticketAnalyticsModule from '../../api/ticketAnalytics';
import { ThemeProvider } from '../../context/ThemeContext';

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../api/ticketAnalytics', () => ({
  fetchCycleTimeAnalytics: vi.fn(),
  fetchBusinessInsights: vi.fn(),
}));

describe('AdminAnalyticsPage Component', () => {
  let queryClient;

  const mockCycleTimeData = {
    lead_time_avg_hours: 36.4,
    cycle_time_avg_hours: 14.2,
    sla_compliance_rate: 92.5,
    bottleneck_stage: 'EN_REPARACION',
    bottleneck_stage_label: 'En Reparación',
    tickets_analyzed_count: 28,
    completed_tickets_count: 20,
    active_tickets_count: 8,
    time_window_days: 30,
    stage_durations: [
      {
        status: 'EN_ESPERA_INGRESO',
        label: 'En Espera de Ingreso',
        avg_hours: 4.0,
        percentage_of_total: 11.0,
        is_bottleneck: false,
      },
      {
        status: 'EN_REVISION',
        label: 'En Revisión',
        avg_hours: 10.0,
        percentage_of_total: 27.5,
        is_bottleneck: false,
      },
      {
        status: 'EN_REPARACION',
        label: 'En Reparación',
        avg_hours: 22.4,
        percentage_of_total: 61.5,
        is_bottleneck: true,
      },
    ],
  };

  const mockBusinessInsightsData = {
    time_window_days: 30,
    brand_intake_ranking: [
      {
        brand: 'Samsung',
        total_tickets: 15,
        percentage: 53.6,
        top_models: [
          { model: 'Galaxy A52', count: 8 },
          { model: 'Galaxy S21', count: 7 },
        ],
      },
      {
        brand: 'Apple',
        total_tickets: 10,
        percentage: 35.7,
        top_models: [{ model: 'iPhone 13', count: 10 }],
      },
    ],
    brand_repair_rates: [
      {
        brand: 'Samsung',
        total_tickets: 15,
        confirmed_repairs: 12,
        rejected_repairs: 1,
        repair_rate: 85.7,
      },
      {
        brand: 'Apple',
        total_tickets: 10,
        confirmed_repairs: 7,
        rejected_repairs: 2,
        repair_rate: 87.5,
      },
    ],
    top_parts_rotation: [
      {
        item_name: 'Pantalla OLED Samsung A52',
        units_used: 8,
        times_used: 8,
        total_revenue: 400.0,
        inventory_id: 'inv-1',
        current_stock: 2,
        is_low_stock: true,
      },
    ],
    customer_recurrence: {
      total_customers: 24,
      recurring_customers_count: 6,
      recurrence_rate: 25.0,
      top_recurring_customers: [
        {
          customer_id: 'cust-1',
          full_name: 'Carlos Mendoza',
          phone_number: '593991234567',
          email: 'carlos@example.com',
          ticket_count: 4,
        },
      ],
    },
    technician_performance: [
      {
        technician_id: 'tech-1',
        technician_name: 'Juan Perez',
        resolved_count: 14,
        active_in_bench_count: 3,
        total_assigned: 17,
        completion_rate: 82.4,
      },
    ],
    gross_margin: {
      labor_revenue: 850.0,
      parts_revenue: 1200.0,
      parts_cost: 600.0,
      parts_margin: 600.0,
      total_revenue: 2050.0,
      estimated_gross_profit: 1450.0,
      margin_percentage: 70.7,
      labor_percentage: 41.5,
      parts_percentage: 58.5,
    },
    critical_stock_alerts: [
      {
        inventory_id: 'inv-1',
        item_name: 'Pantalla OLED Samsung A52',
        sku: 'DISP-A52',
        current_stock: 1,
        low_stock_alert: 3,
        units_used_in_period: 8,
        alert_level: 'BAJO',
      },
    ],
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });
    vi.clearAllMocks();
    window.scrollTo = vi.fn();
    sessionStorage.setItem('td_shop', 'Taller Guayaquil Centro');
  });

  afterEach(() => {
    vi.restoreAllMocks();
    sessionStorage.clear();
  });

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <MemoryRouter initialEntries={['/admin/metricas']}>
            <AdminAnalyticsPage />
          </MemoryRouter>
        </ThemeProvider>
      </QueryClientProvider>
    );
  };

  it('renders page header, title, and shop branding', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockCycleTimeData);
    vi.mocked(ticketAnalyticsModule.fetchBusinessInsights).mockResolvedValue(mockBusinessInsightsData);

    renderPage();

    expect(screen.getByText('Taller Guayaquil Centro')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: /Métricas de Tiempos y Ciclo Operativo/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Volver al panel principal del taller/i })).toBeInTheDocument();
  });

  it('navigates back to /admin when clicking "Volver al Taller"', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockCycleTimeData);
    vi.mocked(ticketAnalyticsModule.fetchBusinessInsights).mockResolvedValue(mockBusinessInsightsData);

    renderPage();

    const backButton = screen.getByRole('button', { name: /Volver al panel principal del taller/i });
    fireEvent.click(backButton);

    expect(mockNavigate).toHaveBeenCalledWith('/admin');
  });

  it('handles logout button click', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockCycleTimeData);
    vi.mocked(ticketAnalyticsModule.fetchBusinessInsights).mockResolvedValue(mockBusinessInsightsData);
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent');

    renderPage();

    const logoutBtn = screen.getByRole('button', { name: /Cerrar Sesion/i });
    fireEvent.click(logoutBtn);

    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(Event));
    expect(mockNavigate).toHaveBeenCalledWith('/login');
  });

  it('renders cycle time metrics by default in the first tab', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockCycleTimeData);
    vi.mocked(ticketAnalyticsModule.fetchBusinessInsights).mockResolvedValue(mockBusinessInsightsData);

    renderPage();

    expect(await screen.findByText('36.4 h (1.5d)')).toBeInTheDocument();
    expect(screen.getByText('14.2 h')).toBeInTheDocument();
    expect(screen.getByText('92.5%')).toBeInTheDocument();
  });

  it('switches to "Flota, Repuestos y Clientes" tab and renders the 7 business KPIs', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockCycleTimeData);
    vi.mocked(ticketAnalyticsModule.fetchBusinessInsights).mockResolvedValue(mockBusinessInsightsData);

    renderPage();

    // Click on tab 2
    const businessTab = screen.getByRole('tab', { name: /Flota, Repuestos y Clientes/i });
    fireEvent.click(businessTab);

    // Title should update
    expect(screen.getByRole('heading', { level: 1, name: /Métricas de Negocio, Flota y Clientes/i })).toBeInTheDocument();

    // Verify KPI 1 (Brand Ranking)
    const samsungElements = await screen.findAllByText('Samsung');
    expect(samsungElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/15 equipos \(53.6%\)/i)).toBeInTheDocument();
    expect(screen.getByText('Galaxy A52')).toBeInTheDocument();

    // Verify KPI 2 (Confirmed Repair Rate)
    expect(screen.getByText('85.7% efectividad')).toBeInTheDocument();

    // Verify KPI 3 (High-Rotation Parts)
    expect(screen.getAllByText('Pantalla OLED Samsung A52').length).toBeGreaterThan(0);
    expect(screen.getAllByText('8 un.').length).toBeGreaterThan(0);

    // Verify KPI 4 (Recurring Customers with PII masking)
    expect(screen.getByText('Carlos Mendoza')).toBeInTheDocument();
    expect(screen.getByText('4 equipos')).toBeInTheDocument();
    // Verify phone is masked: starts with 59xxxxxxxxxx
    expect(screen.getByText(/^59x+$/)).toBeInTheDocument();

    // Verify KPI 5 (Technician Performance)
    expect(screen.getByText('Juan Perez')).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByText('82.4%')).toBeInTheDocument();

    // Verify KPI 6 (Gross Margin & Revenue)
    expect(screen.getAllByText('$1450.00').length).toBeGreaterThan(0);
    expect(screen.getAllByText('$2050.00').length).toBeGreaterThan(0);
    expect(screen.getByText(/70.7% rentabilidad neta/i)).toBeInTheDocument();

    // Verify KPI 7 (Critical Stock Alert)
    expect(screen.getByText('Stock Bajo')).toBeInTheDocument();
  });

  it('switches period in business insights tab and refetches', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockCycleTimeData);
    vi.mocked(ticketAnalyticsModule.fetchBusinessInsights).mockResolvedValue(mockBusinessInsightsData);

    renderPage();

    const businessTab = screen.getByRole('tab', { name: /Flota, Repuestos y Clientes/i });
    fireEvent.click(businessTab);

    const samsungEls = await screen.findAllByText('Samsung');
    expect(samsungEls.length).toBeGreaterThan(0);

    const btn90d = screen.getByRole('button', { name: '90 días' });
    fireEvent.click(btn90d);

    await waitFor(() => {
      expect(ticketAnalyticsModule.fetchBusinessInsights).toHaveBeenCalledWith(90);
    });
  });
});
