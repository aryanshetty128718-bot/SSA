import { describe, it, expect } from 'vitest';
import { validateBarcode } from '../utils/barcode';

describe('validateBarcode utility', () => {
  it('validates a standard 13-digit EAN-13 code with correct check digit', () => {
    // Nutella EAN-13: 3017620422003
    const result = validateBarcode('3017620422003');
    expect(result.valid).toBe(true);
    expect(result.format).toBe('EAN-13');
    expect(result.clean).toBe('3017620422003');
  });

  it('validates a 12-digit UPC-A code', () => {
    // 012345678905 (valid UPC-A check digit: 5)
    const result = validateBarcode('012345678905');
    expect(result.valid).toBe(true);
    expect(result.format).toBe('UPC-A');
  });

  it('rejects barcodes with invalid check digit', () => {
    // Corrupt check digit of Nutella from 3 to 4
    const result = validateBarcode('3017620422004');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Invalid check digit');
  });

  it('rejects non-numeric characters', () => {
    const result = validateBarcode('30176204220A3');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Barcode must contain only digits');
  });

  it('rejects unsupported lengths', () => {
    const result = validateBarcode('12345');
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Invalid barcode length');
  });

  it('cleans whitespace and hyphens', () => {
    const result = validateBarcode(' 301-762-0422003 ');
    expect(result.valid).toBe(true);
    expect(result.clean).toBe('3017620422003');
  });
});
