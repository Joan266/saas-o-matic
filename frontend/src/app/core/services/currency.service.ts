import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Currency, CURRENCIES } from '../models/types';

export type { Currency };
export { CURRENCIES };

interface ExchangeRateResponse {
  rates: Record<string, number>;
  time_last_update_utc: string;
}

@Injectable({ providedIn: 'root' })
export class CurrencyService {
  private readonly http = inject(HttpClient);

  readonly rates = signal<Record<string, number>>({ EUR: 1 });
  readonly currentCurrency = signal<Currency>('EUR');
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly lastUpdated = signal<Date | null>(null);

  readonly currencySymbol = computed(() => {
    const symbols: Record<Currency, string> = {
      EUR: '€', USD: '$', GBP: '£', MXN: '$', JPY: '¥', CHF: 'Fr', CAD: '$',
    };
    return symbols[this.currentCurrency()];
  });

  loadRates(): void {
    this.loading.set(true);
    this.http
      .get<ExchangeRateResponse>(environment.exchangeRateUrl)
      .subscribe({
        next: (data) => {
          this.rates.set(data.rates);
          this.lastUpdated.set(new Date(data.time_last_update_utc));
          this.loading.set(false);
          this.error.set(null);
        },
        error: () => {
          this.loading.set(false);
          this.error.set(
            'No se pudo obtener el tipo de cambio. Mostrando importes en EUR con el último tipo guardado.',
          );
        },
      });
  }

  setCurrency(currency: Currency): void {
    this.currentCurrency.set(currency);
  }

  convert(eurAmount: number): number {
    const rate = this.rates()[this.currentCurrency()] ?? 1;
    return Math.round(eurAmount * rate * 100) / 100;
  }

  format(eurAmount: number): string {
    const converted = this.convert(eurAmount);
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: this.currentCurrency(),
      minimumFractionDigits: 2,
    }).format(converted);
  }
}
