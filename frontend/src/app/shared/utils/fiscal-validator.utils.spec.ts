import { describe, it, expect } from 'vitest';
import { validateSpanishFiscalId } from './fiscal-validator.utils';

describe('validateSpanishFiscalId', () => {
  describe('DNI', () => {
    it('accepts a valid DNI', () => {
      // 12345678Z: 12345678 % 23 = 14 → 'Z'
      const result = validateSpanishFiscalId('12345678Z');
      expect(result.valid).toBe(true);
      expect(result.type).toBe('DNI');
    });

    it('rejects DNI with wrong control letter', () => {
      // Correct letter for 12345678 is Z, not A
      const result = validateSpanishFiscalId('12345678A');
      expect(result.valid).toBe(false);
      expect(result.type).toBe('DNI');
      expect(result.suggestion).toContain("'Z'");
    });

    it('is case-insensitive', () => {
      const result = validateSpanishFiscalId('12345678z');
      expect(result.valid).toBe(true);
    });
  });

  describe('NIE', () => {
    it('accepts a valid NIE starting with X', () => {
      // X0000000T: X→0, 00000000 % 23 = 0 → 'T'
      const result = validateSpanishFiscalId('X0000000T');
      expect(result.valid).toBe(true);
      expect(result.type).toBe('NIE');
    });

    it('accepts a valid NIE starting with Y', () => {
      // Y3859799E: Y→1, 13859799 % 23 = 22 → 'E'
      const result = validateSpanishFiscalId('Y3859799E');
      expect(result.valid).toBe(true);
      expect(result.type).toBe('NIE');
    });

    it('rejects NIE with wrong control letter', () => {
      const result = validateSpanishFiscalId('X0000000A');
      expect(result.valid).toBe(false);
      expect(result.type).toBe('NIE');
    });
  });

  describe('CIF', () => {
    it('accepts valid CIF B83584466', () => {
      const result = validateSpanishFiscalId('B83584466');
      expect(result.valid).toBe(true);
      expect(result.type).toBe('CIF');
    });

    it('rejects invalid CIF B83584469', () => {
      const result = validateSpanishFiscalId('B83584469');
      expect(result.valid).toBe(false);
      expect(result.type).toBe('CIF');
    });

    it('accepts CIF must-letter type (P org)', () => {
      // P type must use letter control — compute correct one
      // digits: 0000000 → odd sum = 0, even sum = 0, digit = 0, letter = J
      const result = validateSpanishFiscalId('P0000000J');
      expect(result.valid).toBe(true);
      expect(result.type).toBe('CIF');
    });
  });

  describe('invalid formats', () => {
    it('rejects random strings', () => {
      const result = validateSpanishFiscalId('INVALID123');
      expect(result.valid).toBe(false);
      expect(result.suggestion).toBeDefined();
    });

    it('rejects empty string', () => {
      const result = validateSpanishFiscalId('');
      expect(result.valid).toBe(false);
    });
  });
});
