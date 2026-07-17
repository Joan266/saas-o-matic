import { describe, it, expect } from 'vitest';
import { calcBaseCost, getTierBreakdown } from './billing.utils';

describe('calcBaseCost', () => {
  it('10 usuarios → 100€', () => expect(calcBaseCost(10)).toBe(100));
  it('11 usuarios → 108€', () => expect(calcBaseCost(11)).toBe(108));
  it('50 usuarios → 420€', () => expect(calcBaseCost(50)).toBe(420));
  it('51 usuarios → 425€', () => expect(calcBaseCost(51)).toBe(425));
  it('60 usuarios → 470€', () => expect(calcBaseCost(60)).toBe(470));
  it('1 usuario → 10€', () => expect(calcBaseCost(1)).toBe(10));
  it('0 usuarios → 0€', () => expect(calcBaseCost(0)).toBe(0));
  it('15 usuarios → 140€', () => expect(calcBaseCost(15)).toBe(140));
});

describe('getTierBreakdown', () => {
  it('65 usuarios → 3 tramos', () => {
    const breakdown = getTierBreakdown(65);
    expect(breakdown).toHaveLength(3);
    expect(breakdown[0]).toEqual({ label: 'Tramo 1–10', users: 10, rate: 10, subtotal: 100 });
    expect(breakdown[1]).toEqual({ label: 'Tramo 11–50', users: 40, rate: 8, subtotal: 320 });
    expect(breakdown[2]).toEqual({ label: 'Tramo >50', users: 15, rate: 5, subtotal: 75 });
  });

  it('5 usuarios → 1 tramo', () => {
    const breakdown = getTierBreakdown(5);
    expect(breakdown).toHaveLength(1);
    expect(breakdown[0].subtotal).toBe(50);
  });

  it('0 usuarios → sin tramos', () => {
    expect(getTierBreakdown(0)).toHaveLength(0);
  });
});
