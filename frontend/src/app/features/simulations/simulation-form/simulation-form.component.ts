import { Component, inject, signal, computed, OnInit, DestroyRef } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DecimalPipe } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';
import { CurrencyService } from '../../../core/services/currency.service';
import { Customer, TAX_RATES } from '../../../core/models/types';
import { Currency } from '../../../core/services/currency.service';
import { calcBaseCost, getTierBreakdown, TierBreakdown } from '../../../shared/utils/billing.utils';

const DISPLAY_CURRENCIES: Currency[] = ['EUR', 'USD', 'GBP'];

@Component({
  selector: 'app-simulation-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, DecimalPipe],
  templateUrl: './simulation-form.component.html',
  styleUrl: './simulation-form.component.css',
})
export class SimulationFormComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  protected readonly currency = inject(CurrencyService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly customer = signal<Customer | null>(null);
  protected readonly loadingCustomer = signal(true);
  protected readonly saving = signal(false);

  protected readonly activeUsers = signal(15);
  protected readonly storageGb = signal(100);
  protected readonly apiCallsK = signal(50);

  protected readonly displayCurrencies = DISPLAY_CURRENCIES;

  // Computed billing values
  protected readonly baseCost = computed(() => calcBaseCost(this.activeUsers()));
  protected readonly tierBreakdown = computed<TierBreakdown[]>(() => getTierBreakdown(this.activeUsers()));
  protected readonly taxRate = computed(() => TAX_RATES[this.customer()?.country ?? ''] ?? 0);
  protected readonly taxAmount = computed(() => this.baseCost() * this.taxRate());
  protected readonly totalEur = computed(() => this.baseCost() + this.taxAmount());
  protected readonly totalDisplay = computed(() => this.currency.format(this.totalEur()));

  // Tier threshold markers for slider UI
  protected readonly tier1Max = 10;
  protected readonly tier2Max = 50;
  protected readonly sliderMax = 200;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getCustomer(id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (customer) => {
          this.customer.set(customer);
          this.loadingCustomer.set(false);
        },
        error: () => {
          this.loadingCustomer.set(false);
          this.router.navigate(['/']);
        },
      });
  }

  protected onUsersChange(event: Event): void {
    this.activeUsers.set(Number((event.target as HTMLInputElement).value));
  }

  protected onStorageChange(event: Event): void {
    this.storageGb.set(Number((event.target as HTMLInputElement).value));
  }

  protected onApiCallsChange(event: Event): void {
    this.apiCallsK.set(Number((event.target as HTMLInputElement).value));
  }

  protected setCurrency(c: Currency): void {
    this.currency.setCurrency(c);
  }

  protected tier1Pct(): string {
    return `${(this.tier1Max / this.sliderMax) * 100}%`;
  }

  protected tier2Pct(): string {
    return `${(this.tier2Max / this.sliderMax) * 100}%`;
  }

  protected currentPct(): number {
    return (this.activeUsers() / this.sliderMax) * 100;
  }

  protected onSave(): void {
    if (this.saving() || !this.customer()) return;
    this.saving.set(true);

    this.api.createSimulation({
      customerId: this.customer()!.id,
      activeUsers: this.activeUsers(),
      storageGb: this.storageGb(),
      apiCalls: this.apiCallsK() * 1000,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: () => {
        this.router.navigate(['/customers', this.customer()!.id]);
      },
      error: () => {
        this.saving.set(false);
      },
    });
  }
}
