import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CycleTimeAnalyticsModal from '../../features/admin/components/CycleTimeAnalyticsModal';
import * as ticketAnalyticsModule from '../../api/ticketAnalytics';

vi.mock('../../api/ticketAnalytics', () => ({
  fetchCycleTimeAnalytics: vi.fn(),
}));

describe('CycleTimeAnalyticsModal Component', () => {
  let queryClient;

  const mockAnalyticsData = {
    lead_time_avg_hours: 48.5,
    cycle_time_avg_hours: 12.0,
    sla_compliance_rate: 85.0,
    bottleneck_stage: 'EN_REVISION',
    bottleneck_stage_label: 'En Revisión',
    tickets_analyzed_count: 15,
    completed_tickets_count: 10,
    active_tickets_count: 5,
    time_window_days: 30,
    stage_durations: [
      {
        status: 'EN_ESPERA_INGRESO',
        label: 'En Espera de Ingreso',
        avg_hours: 8.0,
        percentage_of_total: 16.5,
        is_bottleneck: false,
      },
      {
        status: 'EN_REVISION',
        label: 'En Revisión',
        avg_hours: 24.5,
        percentage_of_total: 50.5,
        is_bottleneck: true,
      },
      {
        status: 'ESPERANDO_APROBACION',
        label: 'Esperando Aprobación',
        avg_hours: 4.0,
        percentage_of_total: 8.2,
        is_bottleneck: false,
      },
      {
        status: 'ESPERANDO_REPUESTO',
        label: 'Esperando Repuesto',
        avg_hours: 0.0,
        percentage_of_total: 0.0,
        is_bottleneck: false,
      },
      {
        status: 'EN_REPARACION',
        label: 'En Reparación',
        avg_hours: 12.0,
        percentage_of_total: 24.8,
        is_bottleneck: false,
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
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderModal = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <CycleTimeAnalyticsModal onClose={vi.fn()} {...props} />
      </QueryClientProvider>
    );
  };

  it('renders modal header, title, and period buttons', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockAnalyticsData);

    renderModal();

    expect(screen.getByText('Métricas de Tiempos y Ciclo')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '7 días' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '30 días' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '90 días' })).toBeInTheDocument();
  });

  it('renders KPI metrics and summary counts correctly', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockAnalyticsData);

    renderModal();

    await waitFor(() => {
      expect(screen.getByText(/Lead Time Promedio/i)).toBeInTheDocument();
    });

    expect(screen.getByText('48.5 h (2.0d)')).toBeInTheDocument();
    expect(screen.getAllByText('12.0 h').length).toBe(2);
    expect(screen.getByText('85.0%')).toBeInTheDocument();
    expect(screen.getAllByText('En Revisión').length).toBe(2);

    // Summary counts
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('highlights bottleneck stage in stage breakdown list', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockAnalyticsData);

    renderModal();

    await waitFor(() => {
      expect(screen.getByText('Cuello de botella')).toBeInTheDocument();
    });

    expect(screen.getByText('24.5 h')).toBeInTheDocument();
    expect(screen.getByText('(50.5%)')).toBeInTheDocument();
  });

  it('switches period and refetches with selected days', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockAnalyticsData);

    renderModal();

    await waitFor(() => {
      expect(screen.getByText(/Lead Time Promedio/i)).toBeInTheDocument();
    });

    const btn7d = screen.getByRole('button', { name: '7 días' });
    fireEvent.click(btn7d);

    await waitFor(() => {
      expect(ticketAnalyticsModule.fetchCycleTimeAnalytics).toHaveBeenCalledWith(7);
    });
  });

  it('renders empty state when no tickets exist in time window', async () => {
    const emptyData = {
      lead_time_avg_hours: 0.0,
      cycle_time_avg_hours: 0.0,
      sla_compliance_rate: 100.0,
      bottleneck_stage: null,
      bottleneck_stage_label: null,
      tickets_analyzed_count: 0,
      completed_tickets_count: 0,
      active_tickets_count: 0,
      time_window_days: 30,
      stage_durations: [],
    };

    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(emptyData);

    renderModal();

    await waitFor(() => {
      expect(screen.getByText(/Sin datos en el período seleccionado/i)).toBeInTheDocument();
    });
  });

  it('calls onClose when clicking close button or pressing Escape', async () => {
    vi.mocked(ticketAnalyticsModule.fetchCycleTimeAnalytics).mockResolvedValue(mockAnalyticsData);
    const onClose = vi.fn();

    renderModal({ onClose });

    const closeBtn = screen.getByLabelText('Cerrar modal');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
