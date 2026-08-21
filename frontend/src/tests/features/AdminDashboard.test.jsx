import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '../../context/ThemeContext';
import AdminDashboard from '../../features/admin/AdminDashboard';
import * as authFetchModule from '../../api/authFetch';

vi.mock('../../api/authFetch', () => ({
  authFetch: vi.fn(),
}));

describe('AdminDashboard Component', () => {
  let queryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });

    vi.mocked(authFetchModule.authFetch).mockImplementation(async (url) => {
      if (url.includes('/tickets/stats')) {
        return {
          ok: true,
          json: async () => ({
            total: 25,
            activos: 18,
            listos: 5,
            espera: 2,
          }),
        };
      }

      if (url.includes('/tickets')) {
        return {
          ok: true,
          json: async () => ({
            items: [
              {
                id: 't-1',
                tracking_token: 'TRK-001',
                device_brand: 'Apple',
                device_model: 'iPhone 12',
                status: 'EN_REVISION',
                created_at: '2026-08-20T10:00:00.000Z',
                customer: { full_name: 'Ana Gomez', phone_number: '0981112233', email: 'ana@test.com' },
                technician: { id: 'tech-1', full_name: 'Tech Alpha' },
              },
            ],
            total: 1,
          }),
        };
      }

      return {
        ok: true,
        json: async () => [],
      };
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderDashboard = () => {
    return render(
      <MemoryRouter>
        <ThemeProvider>
          <QueryClientProvider client={queryClient}>
            <AdminDashboard />
          </QueryClientProvider>
        </ThemeProvider>
      </MemoryRouter>
    );
  };

  it('renders KPI blocks as interactive buttons with stats counts', async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('Total equipos')).toBeInTheDocument();
      expect(screen.getByText('En taller')).toBeInTheDocument();
      expect(screen.getByText('Listos')).toBeInTheDocument();
      expect(screen.getByText('En espera')).toBeInTheDocument();
    });

    const totalBtn = screen.getByRole('button', { name: /Ver todos los equipos/i });
    expect(totalBtn).toHaveClass('is-active');
  });

  it('filters by "activos" (filter_group=activos) when clicking "En taller" KPI', async () => {
    renderDashboard();

    const tallerBtn = await screen.findByRole('button', { name: /Filtrar equipos en taller/i });
    fireEvent.click(tallerBtn);

    await waitFor(() => {
      expect(tallerBtn).toHaveClass('is-active');
      const calls = vi.mocked(authFetchModule.authFetch).mock.calls;
      const filteredCall = calls.find(([url]) => url.includes('filter_group=activos'));
      expect(filteredCall).toBeTruthy();
    });
  });

  it('filters by "listos" (ticket_status=LISTO_PARA_RETIRAR) when clicking "Listos" KPI', async () => {
    renderDashboard();

    const listosBtn = await screen.findByRole('button', { name: /Filtrar equipos listos para retirar/i });
    fireEvent.click(listosBtn);

    await waitFor(() => {
      expect(listosBtn).toHaveClass('is-active');
      const calls = vi.mocked(authFetchModule.authFetch).mock.calls;
      const filteredCall = calls.find(([url]) => url.includes('ticket_status=LISTO_PARA_RETIRAR'));
      expect(filteredCall).toBeTruthy();
    });
  });

  it('filters by "espera" (ticket_status=EN_ESPERA_INGRESO) when clicking "En espera" KPI', async () => {
    renderDashboard();

    const esperaBtn = await screen.findByRole('button', { name: /Filtrar equipos en espera/i });
    fireEvent.click(esperaBtn);

    await waitFor(() => {
      expect(esperaBtn).toHaveClass('is-active');
      const calls = vi.mocked(authFetchModule.authFetch).mock.calls;
      const filteredCall = calls.find(([url]) => url.includes('ticket_status=EN_ESPERA_INGRESO'));
      expect(filteredCall).toBeTruthy();
    });
  });

  it('clears KPI filter when clicking the already active KPI card', async () => {
    renderDashboard();

    const tallerBtn = await screen.findByRole('button', { name: /Filtrar equipos en taller/i });
    fireEvent.click(tallerBtn);

    await waitFor(() => {
      expect(tallerBtn).toHaveClass('is-active');
    });

    // Click again to toggle off
    fireEvent.click(tallerBtn);

    await waitFor(() => {
      expect(tallerBtn).not.toHaveClass('is-active');
      const totalBtn = screen.getByRole('button', { name: /Ver todos los equipos/i });
      expect(totalBtn).toHaveClass('is-active');
    });
  });

  it('clears all filters when clicking "Limpiar filtros"', async () => {
    renderDashboard();

    const listosBtn = await screen.findByRole('button', { name: /Filtrar equipos listos para retirar/i });
    fireEvent.click(listosBtn);

    await waitFor(() => {
      expect(screen.getByText(/Filtro: Listos/i)).toBeInTheDocument();
    });

    const clearBtn = screen.getByRole('button', { name: /Limpiar filtros/i });
    fireEvent.click(clearBtn);

    await waitFor(() => {
      expect(screen.queryByText(/Filtro: Listos/i)).not.toBeInTheDocument();
      expect(listosBtn).not.toHaveClass('is-active');
    });
  });
});
