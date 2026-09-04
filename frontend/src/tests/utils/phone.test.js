import { describe, it, expect } from 'vitest';
import { isValidMobilePhone, cleanPhoneNumber } from '../../utils/phone';

describe('Phone Validation Utility', () => {
  describe('cleanPhoneNumber', () => {
    it('removes spaces, hyphens, and parentheses while preserving leading plus', () => {
      expect(cleanPhoneNumber('099-123-4567')).toBe('0991234567');
      expect(cleanPhoneNumber('(099) 123 4567')).toBe('0991234567');
      expect(cleanPhoneNumber('+593 98 765-4321')).toBe('+593987654321');
      expect(cleanPhoneNumber('   0991234567   ')).toBe('0991234567');
    });

    it('returns empty string for null, undefined or empty input', () => {
      expect(cleanPhoneNumber('')).toBe('');
      expect(cleanPhoneNumber(null)).toBe('');
      expect(cleanPhoneNumber(undefined)).toBe('');
    });
  });

  describe('isValidMobilePhone', () => {
    it('accepts standard 10-digit Ecuadorian mobile numbers starting with 09', () => {
      expect(isValidMobilePhone('0991234567')).toBe(true);
      expect(isValidMobilePhone('0987654321')).toBe(true);
      expect(isValidMobilePhone('0951122334')).toBe(true);
    });

    it('accepts formatted mobile numbers with spaces or dashes', () => {
      expect(isValidMobilePhone('099 123-4567')).toBe(true);
      expect(isValidMobilePhone('(098) 765-4321')).toBe(true);
    });

    it('accepts international Ecuadorian mobile numbers (+5939... or 5939...)', () => {
      expect(isValidMobilePhone('+593987654321')).toBe(true);
      expect(isValidMobilePhone('+593 98 765 4321')).toBe(true);
      expect(isValidMobilePhone('593987654321')).toBe(true);
    });

    it('rejects provincial landlines', () => {
      expect(isValidMobilePhone('022345678')).toBe(false); // Pichincha landline (9 digits, starts with 02)
      expect(isValidMobilePhone('042123456')).toBe(false); // Guayas landline (9 digits, starts with 04)
    });

    it('rejects incomplete or truncated numbers', () => {
      expect(isValidMobilePhone('099123')).toBe(false);
      expect(isValidMobilePhone('09')).toBe(false);
      expect(isValidMobilePhone('099123456')).toBe(false); // 9 digits
    });

    it('rejects invalid mobile prefixes', () => {
      expect(isValidMobilePhone('0891234567')).toBe(false); // Starts with 08
      expect(isValidMobilePhone('0791234567')).toBe(false); // Starts with 07
      expect(isValidMobilePhone('1234567890')).toBe(false); // Starts with 1
    });

    it('returns true for optional empty values', () => {
      expect(isValidMobilePhone('')).toBe(true);
      expect(isValidMobilePhone('   ')).toBe(true);
      expect(isValidMobilePhone(null)).toBe(true);
      expect(isValidMobilePhone(undefined)).toBe(true);
    });
  });
});
