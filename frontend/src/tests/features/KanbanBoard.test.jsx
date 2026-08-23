import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '../../context/ThemeContext';
import KanbanBoard, { KANBAN_COLUMNS, NEXT_STATUS_MAP } from '../../features/admin/components/KanbanBoard';
import AdminDashboard from '../../features/admin/AdminDashboard';
import * as authFetchModule from '../../api/authFetch';

vi.mock('../../api/authFetch', () => ({
  authFetch: vi.fn(),
}));

describe('KanbanBoard Component & Workflow', () => {
  let queryClient;

  const mockTickets = [
    {
      id: 't-ingreso',
      tracking_token: 'TRK-ING-01',
      device_brand: 'Apple',
      device_model: 'iPhone 11',
      status: 'EN_ESPERA_INGRESO',
      created_at: '2026-08-21T10:00:00.000Z',
      customer: { full_name: 'Juan Perez' },
      technician: null,
    },
    {
      id: 't-recibido',
      tracking_token: 'TRK-REC-02',
      device_brand: 'Samsung',
      device_model: 'Galaxy S21',
      status: 'RECIBIDO',
      created_at: '2026-08-21T11:00:00.000Z',
      customer: { full_name: 'Maria Lopez' },
      technician: { id: 'tech-1', full_name: 'Tech Alpha' },
    },
    {
      id: 't-revision',
      tracking_token: 'TRK-REV-03',
      device_brand: 'Xiaomi',
      device_model: 'Redmi Note 10',
      status: 'EN_REVISION',
      diagnostic_notes: null,
      created_at: '2026-08-21T09:00:00.000Z',
      customer: { full_name: 'Carlos Ruiz' },
      technician: { id: 'tech-1', full_name: 'Tech Alpha' },
    },
    {
      id: 't-aprobacion',
      tracking_token: 'TRK-APR-04',
      device_brand: 'Apple',
      device_model: 'iPhone 13',
      status: 'ESPERANDO_APROBACION',
      created_at: '2026-08-20T10:00:00.000Z',
      customer: { full_name: 'Lucia Diaz' },
      technician: null,
    },
    {
      id: 't-repuesto',
      tracking_token: 'TRK-REP-05',
      device_brand: 'Motorola',
      device_model: 'Moto G50',
      status: 'ESPERANDO_REPUESTO',
      created_at: '2026-08-20T12:00:00.000Z',
      customer: { full_name: 'Pedro Ramos' },
      technician: { id: 'tech-2', full_name: 'Tech Beta' },
    },
    {
      id: 't-reparacion',
      tracking_token: 'TRK-REP-06',
      device_brand: 'Huawei',
      device_model: 'P30 Pro',
      status: 'EN_REPARACION',
      created_at: '2026-08-16T10:00:00.000Z', // >72h ago
      customer: { full_name: 'Elena Vega' },
      technician: { id: 'tech-1', full_name: 'Tech Alpha' },
    },
    {
      id: 't-listo',
      tracking_token: 'TRK-LIS-07',
      device_brand: 'Apple',
      device_model: 'MacBook Air',
      status: 'LISTO_PARA_RETIRAR',
      created_at: '2026-08-21T14:00:00.000Z',
      customer: { full_name: 'Roberto Mora' },
      technician: { id: 'tech-1', full_name: 'Tech Alpha' },
    },
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, gcTime: 0 },
      },
    });

    vi.mocked(authFetchModule.authFetch).mockImplementation(async (url, options = {}) => {
      if (url.includes('/status') && options.method === 'PATCH') {
        const body = JSON.parse(options.body || '{}');
        return {
          ok: true,
          json: async () => ({ id: 't-updated', status: body.status }),
        };
      }

      if (url.includes('/tickets/stats')) {
        return {
          ok: true,
          json: async () => ({ total: 7, activos: 6, listos: 1, espera: 2 }),
        };
      }

      if (url.includes('/tickets')) {
        return {
          ok: true,
          json: async () => ({ items: mockTickets, total: mockTickets.length }),
        };
      }

      if (url.includes('/technicians')) {
        return {
          ok: true,
          json: async () => [
            { id: 'tech-1', full_name: 'Tech Alpha' },
            { id: 'tech-2', full_name: 'Tech Beta' },
          ],
        };
      }

      return {
        ok: true,
        json: async () => [],
      };
    });

    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-08-21T16:00:00.000Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    localStorage.clear();
  });

  const renderKanban = (tickets = mockTickets, onStatusChange = vi.fn()) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <KanbanBoard tickets={tickets} onStatusChange={onStatusChange} />
      </QueryClientProvider>
    );
  };

  describe('5-Column Ticket Bucketing & Counters', () => {
    it('correctly categorizes tickets into the 5 semantic columns', () => {
      renderKanban();

      expect(screen.getByText('Ingreso / Recepción')).toBeInTheDocument();
      expect(screen.getByText('En Revisión & Diagnóstico')).toBeInTheDocument();
      expect(screen.getByText('Presupuesto & Espera')).toBeInTheDocument();
      expect(screen.getByText('En Reparación')).toBeInTheDocument();
      expect(screen.getByText('Listo para Retirar')).toBeInTheDocument();

      // Check column counts
      // Ingreso has 2 tickets (t-ingreso, t-recibido)
      // Revision has 1 ticket (t-revision)
      // Espera has 2 tickets (t-aprobacion, t-repuesto)
      // Reparacion has 1 ticket (t-reparacion)
      // Listos has 1 ticket (t-listo)
      const ingresoCol = screen.getByText('Ingreso / Recepción').closest('.kanban-column');
      expect(ingresoCol.querySelector('.kanban-column-badge').textContent).toBe('2');

      const revisionCol = screen.getByText('En Revisión & Diagnóstico').closest('.kanban-column');
      expect(revisionCol.querySelector('.kanban-column-badge').textContent).toBe('1');

      const esperaCol = screen.getByText('Presupuesto & Espera').closest('.kanban-column');
      expect(esperaCol.querySelector('.kanban-column-badge').textContent).toBe('2');

      const reparacionCol = screen.getByText('En Reparación').closest('.kanban-column');
      expect(reparacionCol.querySelector('.kanban-column-badge').textContent).toBe('1');

      const listosCol = screen.getByText('Listo para Retirar').closest('.kanban-column');
      expect(listosCol.querySelector('.kanban-column-badge').textContent).toBe('1');
    });

    it('renders empty state when column has 0 tickets', () => {
      const ticketsOnlyRevision = [mockTickets[2]]; // only EN_REVISION
      renderKanban(ticketsOnlyRevision);

      const emptyStates = screen.getAllByText('Sin equipos');
      expect(emptyStates.length).toBe(4); // other 4 columns are empty
    });

    it('renders SLA overdue and diagnostic warning badges on tickets', () => {
      renderKanban();

      // t-reparacion is created on 2026-08-16 (>72h ago) -> should show Vencido
      expect(screen.getByText('Vencido')).toBeInTheDocument();

      // t-revision has no diagnostic notes -> should show Sin diag.
      expect(screen.getByText('Sin diag.')).toBeInTheDocument();

      // Unassigned tickets should show "Sin técnico"
      const unassignedPills = screen.getAllByText('Sin técnico');
      expect(unassignedPills.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Phase 2 Guard Interception & Quick Transitions', () => {
    it('advances status normally when valid transition criteria are met', async () => {
      const onStatusChange = vi.fn();
      renderKanban([mockTickets[2]], onStatusChange); // EN_REVISION with technician

      const advanceBtn = screen.getByRole('button', { name: /Avanzar ticket Redmi Note 10/i });
      fireEvent.click(advanceBtn);

      await waitFor(() => {
        expect(authFetchModule.authFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tickets/t-revision/status'),
          expect.objectContaining({
            method: 'PATCH',
            body: JSON.stringify({ status: 'ESPERANDO_APROBACION' }),
          })
        );
        expect(onStatusChange).toHaveBeenCalledWith(expect.objectContaining({ status: 'ESPERANDO_APROBACION' }));
      });
    });

    it('intercepts transition to EN_REPARACION when technician is missing and opens detail modal', async () => {
      const alertMock = vi.spyOn(window, 'alert').mockImplementation(() => {});
      const onStatusChange = vi.fn();

      // t-aprobacion is ESPERANDO_APROBACION without technician
      renderKanban([mockTickets[3]], onStatusChange);

      const advanceBtn = screen.getByRole('button', { name: /Avanzar ticket iPhone 13/i });
      fireEvent.click(advanceBtn);

      expect(alertMock).toHaveBeenCalledWith(
        expect.stringContaining("Para pasar a 'En Reparación' es obligatorio tener un técnico asignado.")
      );

      // Should NOT have made PATCH call
      const calls = vi.mocked(authFetchModule.authFetch).mock.calls;
      const patchCalls = calls.filter(([url, opts]) => opts?.method === 'PATCH');
      expect(patchCalls.length).toBe(0);

      // Modal should be opened for assignment
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
        expect(screen.getByText('Datos del Cliente')).toBeInTheDocument();
        expect(screen.getAllByText('iPhone 13').length).toBe(2);
      });

      alertMock.mockRestore();
    });

    it('allows transition to EN_REPARACION when technician is assigned', async () => {
      const onStatusChange = vi.fn();

      // t-repuesto is ESPERANDO_REPUESTO WITH technician
      renderKanban([mockTickets[4]], onStatusChange);

      const advanceBtn = screen.getByRole('button', { name: /Avanzar ticket Moto G50/i });
      fireEvent.click(advanceBtn);

      await waitFor(() => {
        expect(authFetchModule.authFetch).toHaveBeenCalledWith(
          expect.stringContaining('/tickets/t-repuesto/status'),
          expect.objectContaining({
            method: 'PATCH',
            body: JSON.stringify({ status: 'EN_REPARACION' }),
          })
        );
        expect(onStatusChange).toHaveBeenCalledWith(expect.objectContaining({ status: 'EN_REPARACION' }));
      });
    });
  });

  describe('View Mode Switching & LocalStorage Persistence in AdminDashboard', () => {
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

    it('defaults to list view and switches to kanban on toggle click with localStorage update', async () => {
      renderDashboard();

      // Wait for dashboard to load tickets
      await waitFor(() => {
        expect(screen.getByText('iPhone 11')).toBeInTheDocument();
      });

      // Initially in list mode -> tickets-grid exists
      expect(document.querySelector('.tickets-grid')).toBeInTheDocument();
      expect(screen.queryByTestId('kanban-board')).not.toBeInTheDocument();

      // Click Kanban switch
      const kanbanBtn = screen.getByRole('button', { name: /Vista Tablero Kanban/i });
      fireEvent.click(kanbanBtn);

      await waitFor(() => {
        expect(screen.getByTestId('kanban-board')).toBeInTheDocument();
        expect(localStorage.getItem('tecnidesk_workbench_view')).toBe('kanban');
      });

      // Switch back to list
      const listBtn = screen.getByRole('button', { name: /Vista Lista/i });
      fireEvent.click(listBtn);

      await waitFor(() => {
        expect(document.querySelector('.tickets-grid')).toBeInTheDocument();
        expect(localStorage.getItem('tecnidesk_workbench_view')).toBe('list');
      });
    });

    it('initializes in kanban mode if saved in localStorage', async () => {
      localStorage.setItem('tecnidesk_workbench_view', 'kanban');
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByTestId('kanban-board')).toBeInTheDocument();
      });
    });
  });
});
