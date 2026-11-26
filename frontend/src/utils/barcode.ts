/**
 * GS1 GTIN/EAN barcode validation & check-digit calculation
 */
export function validateBarcode(barcode: string): { valid: boolean; format?: string; clean?: string; error?: string } {
  const cleaned = barcode.replace(/[\s-]/g, '').trim();
  if (!cleaned) {
    return { valid: false, error: 'Please enter a barcode' };
  }
  if (!/^\d+$/.test(cleaned)) {
    return { valid: false, error: 'Barcode must contain only digits' };
  }
  if (![8, 12, 13, 14].includes(cleaned.length)) {
    return { valid: false, error: `Invalid barcode length (${cleaned.length} digits). Expected standard 8, 12, 13, or 14 digits.` };
  }

  // Determine format name
  let format = 'EAN-13';
  if (cleaned.length === 8) format = 'EAN-8';
  else if (cleaned.length === 12) format = 'UPC-A';
  else if (cleaned.length === 14) format = 'GTIN-14';

  // Check digit calculation
  const digits = cleaned.split('').map(Number);
  const checkDigit = digits[digits.length - 1];
  const payload = digits.slice(0, -1);

  // Pad to payload digits for alternating weights (3, 1, 3, 1...) from right
  let sum = 0;
  let multiplier = 3;
  for (let i = payload.length - 1; i >= 0; i--) {
    sum += payload[i] * multiplier;
    multiplier = multiplier === 3 ? 1 : 3;
  }
  const expectedCheck = (10 - (sum % 10)) % 10;

  if (checkDigit !== expectedCheck) {
    return { valid: false, error: `Invalid check digit (${checkDigit}). Expected ${expectedCheck}.` };
  }

  return { valid: true, format, clean: cleaned };
}
