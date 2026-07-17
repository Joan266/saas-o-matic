export interface TierBreakdown {
  label: string;
  users: number;
  rate: number;
  subtotal: number;
}

const TIERS: [number | null, number][] = [
  [10, 10],
  [40, 8],
  [null, 5],
];

export function calcBaseCost(activeUsers: number): number {
  if (activeUsers < 1) return 0;
  let cost = 0;
  let remaining = activeUsers;

  for (const [cap, rate] of TIERS) {
    if (remaining <= 0) break;
    const chunk = cap !== null ? Math.min(remaining, cap) : remaining;
    cost += chunk * rate;
    remaining -= chunk;
  }

  return Math.round(cost * 100) / 100;
}

export function getTierBreakdown(activeUsers: number): TierBreakdown[] {
  if (activeUsers < 1) return [];

  const result: TierBreakdown[] = [];
  let remaining = activeUsers;
  let start = 1;

  const defs = [
    { cap: 10 as number | null, rate: 10, label: '1–10' },
    { cap: 40 as number | null, rate: 8, label: '11–50' },
    { cap: null as number | null, rate: 5, label: '>50' },
  ];

  for (const { cap, rate, label } of defs) {
    if (remaining <= 0) break;
    const chunk = cap !== null ? Math.min(remaining, cap) : remaining;
    result.push({ label: `Tramo ${label}`, users: chunk, rate, subtotal: chunk * rate });
    remaining -= chunk;
    start += chunk;
  }

  return result;
}
