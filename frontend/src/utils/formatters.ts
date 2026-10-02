/**
 * Format a number as a percentage string (e.g., 0.1234 → "12.34%").
 */
export function formatPercent(value: number, decimals = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a number as currency with thousands separators (e.g., 12345.6 → "$12,345.60").
 */
export function formatCurrency(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format a number with thousands separators (e.g., 12345.6 → "12,345.60").
 */
export function formatNumber(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

/**
 * Format a Sharpe ratio or similar decimal metric (e.g., 1.234 → "1.23").
 */
export function formatRatio(value: number, decimals = 2): string {
  return value.toFixed(decimals);
}

/**
 * Format basis points (e.g., 0.0025 → "25 bps").
 */
export function formatBps(value: number): string {
  return `${Math.round(value * 10000)} bps`;
}
