import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import StatusBadge from '../../components/shared/StatusBadge';

describe('StatusBadge Component', () => {
  it('renders "EN_ESPERA_INGRESO" status with "Recibido" label and tokens', () => {
    render(<StatusBadge status="EN_ESPERA_INGRESO" />);

    const badge = screen.getByText('Recibido');
    expect(badge).toBeInTheDocument();
    expect(screen.getByText('REC')).toBeInTheDocument();

    const container = badge.closest('.ticket-badge');
    expect(container).toHaveStyle({
      color: '#0369a1',
      backgroundColor: '#f0f9ff',
    });
  });

  it('renders "ESPERANDO_REPUESTO" with violet palette from DESIGN.md', () => {
    render(<StatusBadge status="ESPERANDO_REPUESTO" />);

    const badge = screen.getByText('Esperando repuesto');
    expect(badge).toBeInTheDocument();

    const container = badge.closest('.ticket-badge');
    expect(container).toHaveStyle({
      color: '#6d28d9',
      backgroundColor: '#f5f3ff',
    });
  });

  it('renders "LISTO_PARA_RETIRAR" with emerald palette', () => {
    render(<StatusBadge status="LISTO_PARA_RETIRAR" />);

    const badge = screen.getByText('Listo');
    expect(badge).toBeInTheDocument();

    const container = badge.closest('.ticket-badge');
    expect(container).toHaveStyle({
      color: '#047857',
      backgroundColor: '#ecfdf5',
    });
  });

  it('gracefully handles unknown status with safe neutral fallback', () => {
    render(<StatusBadge status="CUSTOM_OR_UNKNOWN" />);

    expect(screen.getByText('CUSTOM_OR_UNKNOWN')).toBeInTheDocument();
  });

  it('omits leading icon indicator when showIcon is false', () => {
    render(<StatusBadge status="EN_ESPERA_INGRESO" showIcon={false} />);

    expect(screen.getByText('Recibido')).toBeInTheDocument();
    expect(screen.queryByText('REC')).not.toBeInTheDocument();
  });
});
