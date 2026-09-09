/**
 * Phone utilities for Ecuadorian mobile numbers.
 */

/**
 * Sanitizes phone input by removing spaces, dashes, parentheses and periods,
 * while preserving a leading '+' if present.
 *
 * @param {string|null|undefined} phone
 * @returns {string}
 */
export function cleanPhoneNumber(phone) {
  if (!phone || typeof phone !== 'string') return '';
  const trimmed = phone.trim();
  if (trimmed.startsWith('+')) {
    return '+' + trimmed.slice(1).replace(/\D/g, '');
  }
  return trimmed.replace(/\D/g, '');
}

/**
 * Validates whether the given phone string matches Ecuadorian mobile phone formats:
 * - National format: exactly 10 digits starting with '09' (e.g., 0991234567)
 * - International format: +5939XXXXXXXX or 5939XXXXXXXX (total 12 digits excluding +)
 *
 * Returns true if the phone is null, undefined, or empty (when optional).
 *
 * @param {string|null|undefined} phone
 * @returns {boolean}
 */
export function isValidMobilePhone(phone) {
  if (phone === null || phone === undefined) return true;
  if (typeof phone !== 'string') return false;
  if (phone.trim() === '') return true;

  const cleaned = cleanPhoneNumber(phone);

  // National mobile: 09 followed by 8 digits (10 digits total)
  const isNationalMobile = /^09\d{8}$/.test(cleaned);

  // International mobile: +5939 or 5939 followed by 8 digits
  const isInternationalMobile = /^(?:\+5939|5939)\d{8}$/.test(cleaned);

  return isNationalMobile || isInternationalMobile;
}

/**
 * Normalizes a phone input into pure digits suitable for WhatsApp / API payloads:
 * - Strips spaces, dashes, parentheses, dots and leading '+'
 * - Auto-converts Ecuadorian national mobile numbers ('09XXXXXXXX') into international '5939XXXXXXXX'
 *
 * @param {string|null|undefined} phone
 * @returns {string}
 */
export function normalizeWhatsAppNumber(phone) {
  if (!phone || typeof phone !== 'string') return '';
  const digitsOnly = phone.replace(/\D/g, '');
  if (!digitsOnly) return '';

  // If standard Ecuadorian 10-digit mobile starting with 09 (e.g. 0991234567)
  if (/^09\d{8}$/.test(digitsOnly)) {
    return '593' + digitsOnly.slice(1);
  }

  return digitsOnly;
}

/**
 * Validates whether the given phone string can be normalized into a valid WhatsApp mobile number.
 * - Must not contain alphabetic characters or invalid symbols
 * - Must normalize to between 10 and 20 digits
 * - For Ecuadorian numbers (starting with 593), strictly enforces mobile prefix 5939 (12 digits)
 * - Rejects empty / whitespace values
 *
 * @param {string|null|undefined} phone
 * @returns {boolean}
 */
export function isValidWhatsAppNumber(phone) {
  if (!phone || typeof phone !== 'string') return false;
  if (phone.trim() === '') return false;

  // Reject unexpected characters like letters or special punctuation
  if (/[^\d\s+\-().]/.test(phone)) return false;

  const normalized = normalizeWhatsAppNumber(phone);

  // Length must be between 10 and 20 digits
  if (normalized.length < 10 || normalized.length > 20) return false;

  // If Ecuadorian country code (593), enforce mobile prefix 5939 (12 digits) and reject landlines
  if (normalized.startsWith('593')) {
    return /^5939\d{8}$/.test(normalized);
  }

  // If starts with 0 (e.g. landline with provincial prefix like 02, 04), reject
  if (normalized.startsWith('0')) {
    return false;
  }

  return /^\d{10,20}$/.test(normalized);
}
