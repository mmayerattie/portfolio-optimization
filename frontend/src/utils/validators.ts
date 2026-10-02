import type { Position } from '../types/portfolio';

export interface ValidationError {
  field: string;
  message: string;
}

/**
 * Validate a list of portfolio positions.
 */
export function validatePositions(positions: Position[]): ValidationError[] {
  const errors: ValidationError[] = [];

  if (positions.length < 1) {
    errors.push({ field: 'positions', message: 'At least 1 position is required.' });
  }

  const seen = new Set<string>();
  for (let i = 0; i < positions.length; i++) {
    const p = positions[i];
    const ticker = p.ticker.trim().toUpperCase();

    if (!ticker) {
      errors.push({ field: `positions[${i}].ticker`, message: 'Ticker cannot be empty.' });
    }
    if (p.shares <= 0) {
      errors.push({ field: `positions[${i}].shares`, message: 'Shares must be greater than 0.' });
    }
    if (p.cost_basis !== undefined && p.cost_basis < 0) {
      errors.push({ field: `positions[${i}].cost_basis`, message: 'Cost basis cannot be negative.' });
    }
    if (seen.has(ticker)) {
      errors.push({ field: `positions[${i}].ticker`, message: `Duplicate ticker: ${ticker}` });
    }
    seen.add(ticker);
  }

  return errors;
}
