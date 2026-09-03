import { render, screen } from '@testing-library/react';
import React from 'react';
import { describe, it, expect } from 'vitest';

const ExampleComponent = () => <div>Hello, Test!</div>;

describe('Example Component', () => {
  it('renders correctly', () => {
    render(<ExampleComponent />);
    expect(screen.getByText('Hello, Test!')).toBeInTheDocument();
  });
});


