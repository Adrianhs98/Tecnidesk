import { describe, it, expect } from 'vitest';
import { formatCurrency } from '../../utils/currency';

describe('formatCurrency', () => {
  describe('Standard output formatting', () => {
    it('formats valid integer numbers', () => {
      expect(formatCurrency(15)).toBe('$15.00');
      expect(formatCurrency(0)).toBe('$0.00');
    });

    it('formats valid floating point numbers', () => {
      expect(formatCurrency(12.3)).toBe('$12.30');
      expect(formatCurrency(12.345)).toBe('$12.35');
      expect(formatCurrency(99.99)).toBe('$99.99');
    });

    it('formats valid numeric strings', () => {
      expect(formatCurrency('45.99')).toBe('$45.99');
      expect(formatCurrency('100')).toBe('$100.00');
      expect(formatCurrency('0.5')).toBe('$0.50');
    });
  });

  describe('Handling invalid or missing inputs safely', () => {
    it('returns default fallback for null or undefined', () => {
      expect(formatCurrency(null)).toBe('$0.00');
      expect(formatCurrency(undefined)).toBe('$0.00');
      expect(formatCurrency('')).toBe('$0.00');
    });

    it('returns default fallback for invalid strings and NaN', () => {
      expect(formatCurrency('abc')).toBe('$0.00');
      expect(formatCurrency(NaN)).toBe('$0.00');
    });

    it('supports custom fallback value', () => {
      expect(formatCurrency(null, { fallback: '-' })).toBe('-');
      expect(formatCurrency(undefined, { fallback: 'En evaluacion' })).toBe('En evaluacion');
      expect(formatCurrency('invalid', { fallback: 'N/A' })).toBe('N/A');
    });
  });

  describe('Options configuration', () => {
    it('supports omitting currency symbol', () => {
      expect(formatCurrency(15, { showSymbol: false })).toBe('15.00');
      expect(formatCurrency('45.99', { showSymbol: false })).toBe('45.99');
    });
  });
});
