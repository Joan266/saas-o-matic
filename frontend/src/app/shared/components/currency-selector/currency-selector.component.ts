import { Component, inject, signal, HostListener, ElementRef } from '@angular/core';
import { CurrencyService } from '../../../core/services/currency.service';
import { CURRENCIES, Currency } from '../../../core/models/types';

@Component({
  selector: 'app-currency-selector',
  standalone: true,
  template: `
    <div class="cs-wrapper">
      <button class="cs-trigger" (click)="toggle()" [class.cs-trigger--open]="open()">
        {{ currencyService.currentCurrency() }} {{ currencyService.currencySymbol() }}
        <svg width="10" height="6" viewBox="0 0 10 6" fill="none">
          <path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </button>

      @if (open()) {
        <div class="cs-dropdown">
          @for (c of currencies; track c) {
            <button
              class="cs-option"
              [class.cs-option--active]="c === currencyService.currentCurrency()"
              (click)="select(c)"
            >
              {{ c }} {{ symbols[c] }}
            </button>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    .cs-wrapper { position: relative; }

    .cs-trigger {
      display: flex;
      align-items: center;
      gap: 6px;
      background: var(--surface-raised);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text-primary);
      font-family: 'Space Grotesk', sans-serif;
      font-size: 0.8125rem;
      font-weight: 500;
      padding: 6px 10px;
      cursor: pointer;
      white-space: nowrap;
      transition: border-color 0.15s;
    }

    .cs-trigger:hover,
    .cs-trigger--open { border-color: var(--accent); }

    .cs-trigger svg { opacity: 0.6; transition: transform 0.15s; }
    .cs-trigger--open svg { transform: rotate(180deg); }

    .cs-dropdown {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 4px;
      min-width: 110px;
      z-index: 200;
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
    }

    .cs-option {
      display: block;
      width: 100%;
      background: none;
      border: none;
      color: var(--text-secondary);
      font-family: 'Space Grotesk', sans-serif;
      font-size: 0.8125rem;
      padding: 7px 10px;
      text-align: left;
      cursor: pointer;
      border-radius: 6px;
      transition: background 0.1s, color 0.1s;
    }

    .cs-option:hover { background: var(--surface-raised); color: var(--text-primary); }
    .cs-option--active { color: var(--accent); font-weight: 600; }
  `],
})
export class CurrencySelectorComponent {
  protected readonly currencyService = inject(CurrencyService);
  private readonly elRef = inject(ElementRef);

  protected readonly open = signal(false);
  protected readonly currencies: Currency[] = CURRENCIES;
  protected readonly symbols: Record<Currency, string> = {
    EUR: '€', USD: '$', GBP: '£', MXN: '$', JPY: '¥', CHF: 'Fr', CAD: '$',
  };

  toggle(): void {
    this.open.update(v => !v);
  }

  select(c: Currency): void {
    this.currencyService.setCurrency(c);
    this.open.set(false);
  }

  @HostListener('document:click', ['$event'])
  onOutsideClick(e: Event): void {
    if (!this.elRef.nativeElement.contains(e.target)) {
      this.open.set(false);
    }
  }
}
