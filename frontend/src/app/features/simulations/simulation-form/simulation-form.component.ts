import { Component, inject, signal, computed, OnInit, DestroyRef } from '@angular/core';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DecimalPipe } from '@angular/common';
import { ApiService } from '../../../core/services/api.service';
import { CurrencyService } from '../../../core/services/currency.service';
import { Customer, TAX_RATES } from '../../../core/models/types';
import { calcBaseCost, getTierBreakdown, TierBreakdown } from '../../../shared/utils/billing.utils';

@Component({
  selector: 'app-simulation-form',
  standalone: true,
  imports: [RouterLink, DecimalPipe],
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

  // Computed billing values
  protected readonly baseCost = computed(() => calcBaseCost(this.activeUsers()));
  protected readonly tierBreakdown = computed<TierBreakdown[]>(() => getTierBreakdown(this.activeUsers()));
  protected readonly taxRate = computed(() => TAX_RATES[this.customer()?.country ?? ''] ?? 0);
  protected readonly taxAmount = computed(() => this.baseCost() * this.taxRate());
  protected readonly totalEur = computed(() => this.baseCost() + this.taxAmount());
  protected readonly totalDisplay = computed(() => this.currency.format(this.totalEur()));

  // Slider range caps at 200; actual value can exceed it via the number input
  protected readonly sliderMax = 200;
  protected readonly sliderValue = computed(() => Math.min(this.activeUsers(), this.sliderMax));

  // Tier threshold markers: fixed percentages based on slider range (1-200)
  protected readonly tier1Pct = '5%';   // 10/200
  protected readonly tier2Pct = '25%';  // 50/200

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) { this.router.navigate(['/']); return; }
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

  protected onUsersInputChange(event: Event): void {
    const val = Number((event.target as HTMLInputElement).value);
    if (val >= 1) this.activeUsers.set(Math.floor(val));
  }

  protected onSave(): void {
    if (this.saving() || !this.customer()) return;
    this.saving.set(true);

    this.api.createSimulation({
      customerId: this.customer()!.id,
      activeUsers: this.activeUsers(),
      storageGb: 1,
      apiCalls: 0,
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
