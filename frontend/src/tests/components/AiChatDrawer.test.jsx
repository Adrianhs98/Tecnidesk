import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AiChatDrawer from '../../features/technician/AiChatDrawer';
import * as diagnosticApi from '../../api/diagnostic';

vi.mock('../../api/diagnostic', () => ({
  sendDiagnosticChat: vi.fn(),
  sendFreeDiagnosticChat: vi.fn(),
  getDiagnosticChatHistory: vi.fn(),
  confirmCorrection: vi.fn(),
}));

describe('AiChatDrawer - Technical Reasoning & Mode Selection', () => {
  const mockTicketContext = {
    id: 'ticket-1234',
    device_brand: 'Apple',
    device_model: 'iPhone 13',
    issue_description: 'Corto en línea principal',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    diagnosticApi.getDiagnosticChatHistory.mockResolvedValue({ messages: [] });
  });

  it('renders mode selector pill when ticket context is active', async () => {
    render(
      <AiChatDrawer
        isOpen={true}
        onClose={vi.fn()}
        ticketContext={mockTicketContext}
        context="ticket"
      />
    );

    const modePill = await screen.findByTestId('ai-mode-pill-btn');
    expect(modePill).toBeInTheDocument();
    expect(modePill).toHaveTextContent('Rápida');
  });

  it('opens popover when mode pill is clicked and allows switching to reasoning', async () => {
    render(
      <AiChatDrawer
        isOpen={true}
        onClose={vi.fn()}
        ticketContext={mockTicketContext}
        context="ticket"
      />
    );

    const modePill = await screen.findByTestId('ai-mode-pill-btn');
    fireEvent.click(modePill);

    const popover = await screen.findByTestId('ai-mode-popover');
    expect(popover).toBeInTheDocument();
    expect(screen.getByText('Respuesta rápida')).toBeInTheDocument();
    expect(screen.getByText('Razonamiento técnico')).toBeInTheDocument();

    // Select Reasoning mode
    const reasoningOption = screen.getByTestId('mode-option-reasoning');
    fireEvent.click(reasoningOption);

    // Popover should close and pill should now show "Razonamiento"
    expect(screen.queryByTestId('ai-mode-popover')).not.toBeInTheDocument();
    expect(modePill).toHaveTextContent('Razonamiento');
  });

  it('dispatches deep_research=true to sendDiagnosticChat when reasoning mode is active', async () => {
    diagnosticApi.sendDiagnosticChat.mockResolvedValue({
      id: 'ai-msg-1',
      role: 'assistant',
      content: 'Revisar condensador C1204 en línea PP_VDD_MAIN.',
      sources: [
        {
          title: 'Guía de Reparación iPhone 13',
          url: 'https://esquematicos.com/iphone-13',
        },
      ],
    });

    render(
      <AiChatDrawer
        isOpen={true}
        onClose={vi.fn()}
        ticketContext={mockTicketContext}
        context="ticket"
      />
    );

    // Switch to reasoning
    const modePill = await screen.findByTestId('ai-mode-pill-btn');
    fireEvent.click(modePill);
    fireEvent.click(screen.getByTestId('mode-option-reasoning'));

    // Type and send
    const input = screen.getByTestId('ai-chat-input');
    fireEvent.change(input, { target: { value: '¿Qué componente suele fallar en este modelo?' } });

    const sendBtn = screen.getByTestId('ai-send-btn');
    fireEvent.click(sendBtn);

    await waitFor(() => {
      expect(diagnosticApi.sendDiagnosticChat).toHaveBeenCalledWith(
        'ticket-1234',
        '¿Qué componente suele fallar en este modelo?',
        true // deep_research === true
      );
    });

    // Verify sources accordion is displayed
    const accordion = await screen.findByTestId('ai-sources-accordion');
    expect(accordion).toBeInTheDocument();
    expect(screen.getByText(/Fuentes web consultadas \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText('Guía de Reparación iPhone 13')).toBeInTheDocument();
  });
});
