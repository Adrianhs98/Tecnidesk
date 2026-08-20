/**
 * Utility functions for currency formatting.
 * Standardizes monetary amounts across the application.
 */

/**
 * Formats a monetary amount into a standard currency string (USD).
 *
 * @param {number|string|null|undefined} amount - The amount to format.
 * @param {Object} [options] - Formatting options.
 * @param {string} [options.fallback="$0.00"] - Fallback string when amount is null, undefined, or invalid.
 * @param {boolean} [options.showSymbol=true] - Whether to include the "$" prefix.
 * @returns {string} The formatted currency string.
 */
export function formatCurrency(amount, options = {}) {
  const { fallback = "$0.00", showSymbol = true } = options;

  if (amount === null || amount === undefined || amount === "") {
    return fallback;
  }

  const numeric = typeof amount === "number" ? amount : parseFloat(amount);

  if (Number.isNaN(numeric)) {
    return fallback;
  }

  const formatted = numeric.toFixed(2);
  return showSymbol ? `$${formatted}` : formatted;
}
