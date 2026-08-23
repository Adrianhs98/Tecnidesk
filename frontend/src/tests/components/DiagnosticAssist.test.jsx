import { render, screen, fireEvent } from '@testing-library/react';
import DiagnosticAssistPanel from '../../features/admin/components/DiagnosticAssistPanel';
import * as diagnosticApi from '../../api/diagnostic';
import { vi } from 'vitest';

vi.mock('../../api/diagnostic');

describe('DiagnosticAssistPanel', () => {
  it('renders correctly and handles diagnose click', async () => {
    diagnosticApi.diagnoseTicket.mockResolvedValue({
      probable_cause: 'Pantalla rota',
      summary_explanation: 'El dispositivo presenta signos de impacto.',
      had_sufficient_evidence: true,
      similarity_distance: 0.15,
      maturity_source: 'real_validated',
      citations: [],
      recommended_steps: ['Reemplazar display']
    });

    render(<DiagnosticAssistPanel ticketId="123" onApplyAssist={vi.fn()} />);
    
    const btn = screen.getByText(/Asistente de Diagnóstico IA/i);
    expect(btn).toBeInTheDocument();
    
    fireEvent.click(btn);
    
    expect(await screen.findByText(/Sugerencia de IA/i)).toBeInTheDocument();
    expect(await screen.findByText(/Pantalla rota/i)).toBeInTheDocument();
  });
});
