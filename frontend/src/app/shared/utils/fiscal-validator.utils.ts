/**
 * Spanish fiscal ID validator: DNI, NIE, CIF.
 * Port of backend/app/services/fiscal_validator.py
 *
 * Sources:
 * - DNI/NIE: Ministerio del Interior
 * - CIF: Agencia Tributaria
 */

const DNI_LETTERS = 'TRWAGMYFPDXBNJZSQVHLCKE';
const NIE_PREFIX: Record<'X' | 'Y' | 'Z', string> = { X: '0', Y: '1', Z: '2' };
const CIF_LETTERS = 'JABCDEFGHI';
const CIF_MUST_LETTER = new Set(['P', 'Q', 'R', 'S', 'N', 'W']);
const CIF_MUST_DIGIT = new Set(['A', 'B', 'E', 'H']);

export interface FiscalValidationResult {
  valid: boolean;
  type?: 'DNI' | 'NIE' | 'CIF';
  suggestion?: string;
}

export function validateSpanishFiscalId(id: string): FiscalValidationResult {
  const fid = id.trim().toUpperCase();

  if (!fid) {
    return { valid: false, suggestion: 'El identificador fiscal no puede estar vacío.' };
  }

  if (/^\d{8}[A-Z]$/.test(fid)) return validateDni(fid);
  if (/^[XYZ]\d{7}[A-Z]$/.test(fid)) return validateNie(fid);
  if (/^[A-Z]\d{7}[A-Z0-9]$/.test(fid)) return validateCif(fid);

  return {
    valid: false,
    suggestion: `'${id}' no tiene un formato válido de DNI, NIE o CIF.`,
  };
}

function validateDni(fid: string): FiscalValidationResult {
  const number = parseInt(fid.slice(0, 8), 10);
  const expected = DNI_LETTERS[number % 23];
  if (fid[8] !== expected) {
    return {
      valid: false,
      type: 'DNI',
      suggestion: `DNI inválido: la letra de control debe ser '${expected}'.`,
    };
  }
  return { valid: true, type: 'DNI' };
}

function validateNie(fid: string): FiscalValidationResult {
  const numberStr = NIE_PREFIX[fid[0] as 'X' | 'Y' | 'Z'] + fid.slice(1, 8);
  const expected = DNI_LETTERS[parseInt(numberStr, 10) % 23];
  if (fid[8] !== expected) {
    return {
      valid: false,
      type: 'NIE',
      suggestion: `NIE inválido: la letra de control debe ser '${expected}'.`,
    };
  }
  return { valid: true, type: 'NIE' };
}

function cifControl(digits: string): { digit: number; letter: string } {
  let oddSum = 0;
  for (const i of [0, 2, 4, 6]) {
    const doubled = parseInt(digits[i], 10) * 2;
    oddSum += Math.floor(doubled / 10) + (doubled % 10);
  }
  const evenSum = [1, 3, 5].reduce((acc, i) => acc + parseInt(digits[i], 10), 0);
  const digit = (10 - ((oddSum + evenSum) % 10)) % 10;
  return { digit, letter: CIF_LETTERS[digit] };
}

function validateCif(fid: string): FiscalValidationResult {
  const orgType = fid[0];
  const digits = fid.slice(1, 8);
  const control = fid[8];
  const { digit, letter } = cifControl(digits);

  if (CIF_MUST_LETTER.has(orgType)) {
    if (control !== letter) {
      return {
        valid: false,
        type: 'CIF',
        suggestion: `CIF inválido: el dígito de control debe ser la letra '${letter}'.`,
      };
    }
  } else if (CIF_MUST_DIGIT.has(orgType)) {
    if (control !== String(digit)) {
      return {
        valid: false,
        type: 'CIF',
        suggestion: `CIF inválido: el dígito de control debe ser el número '${digit}'.`,
      };
    }
  } else {
    if (control !== String(digit) && control !== letter) {
      return {
        valid: false,
        type: 'CIF',
        suggestion: `CIF inválido: el dígito de control debe ser '${digit}' o '${letter}'.`,
      };
    }
  }

  return { valid: true, type: 'CIF' };
}
