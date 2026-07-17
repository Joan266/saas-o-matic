export type Plan = 'starter' | 'professional' | 'enterprise';
export type Currency = 'EUR' | 'USD' | 'GBP' | 'MXN' | 'JPY' | 'CHF' | 'CAD';

export const CURRENCIES: Currency[] = ['EUR', 'USD', 'GBP', 'MXN', 'JPY', 'CHF', 'CAD'];

export const COUNTRY_LABELS: Record<string, string> = {
  ES: '🇪🇸 España',
  DE: '🇩🇪 Alemania',
  FR: '🇫🇷 Francia',
  UK: '🇬🇧 Reino Unido',
  MX: '🇲🇽 México',
  US: '🇺🇸 Estados Unidos',
};

export const TAX_RATES: Record<string, number> = {
  ES: 0.21,
  DE: 0.19,
  FR: 0.20,
  UK: 0.20,
  MX: 0.16,
  US: 0.00,
};

export interface Customer {
  id: number;
  company: string;
  fiscalId: string;
  email: string;
  country: string;
  plan: Plan;
  createdAt: string;
  updatedAt: string;
  lastSimulationAt?: string;
}

export interface Stats {
  totalCustomers: number;
  totalSimulations: number;
  totalMrr: number;
}

export interface CustomerCreate {
  company: string;
  fiscalId: string;
  email: string;
  country: string;
  plan: Plan;
}

export interface Simulation {
  id: number;
  customerId: number;
  activeUsers: number;
  storageGb: number;
  apiCalls: number;
  baseCost: number;
  taxRate: number;
  totalCost: number;
  createdAt: string;
}

export interface SimulationCreate {
  customerId: number;
  activeUsers: number;
  storageGb: number;
  apiCalls: number;
}

export interface ApiError {
  detail: string;
  code?: string;
}
