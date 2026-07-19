import { Component, inject, signal, computed, OnInit, DestroyRef } from '@angular/core';
import { RouterLink, ActivatedRoute, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DecimalPipe } from '@angular/common';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { CurrencyService } from '../../../core/services/currency.service';
import { Customer, Simulation, COUNTRY_LABELS, TAX_RATES } from '../../../core/models/types';
import { getTierBreakdown, TierBreakdown } from '../../../shared/utils/billing.utils';
import { avatarColor, initials } from '../../../shared/utils/avatar.utils';

@Component({
  selector: 'app-customer-detail',
  standalone: true,
  imports: [RouterLink, DecimalPipe],
  templateUrl: './customer-detail.component.html',
  styleUrl: './customer-detail.component.css',
})
export class CustomerDetailComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  protected readonly currency = inject(CurrencyService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly customer = signal<Customer | null>(null);
  protected readonly simulations = signal<Simulation[]>([]);
  protected readonly loading = signal(true);
  protected readonly expandedSimId = signal<number | null>(null);

  // Simulations arrive newest-first (backend ORDER BY created_at DESC)
  protected readonly lastSim = computed(() => {
    const sims = this.simulations();
    if (!sims.length) return '—';
    return new Date(sims[0].createdAt).toLocaleDateString('es-ES');
  });

  protected readonly avatarColor = avatarColor;
  protected readonly initials = initials;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    if (!id) { this.router.navigate(['/']); return; }
    forkJoin([this.api.getCustomer(id), this.api.getSimulations(id)] as const)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: ([customer, simulations]) => {
          this.customer.set(customer);
          this.simulations.set(simulations);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.router.navigate(['/']);
        },
      });
  }

  protected toggleExpand(simId: number): void {
    this.expandedSimId.set(this.expandedSimId() === simId ? null : simId);
  }

  protected tierBreakdown(sim: Simulation): TierBreakdown[] {
    return getTierBreakdown(sim.activeUsers);
  }

  protected countryLabel(code: string): string {
    return COUNTRY_LABELS[code] ?? code;
  }

  protected taxRate(code: string): number {
    return (TAX_RATES[code] ?? 0) * 100;
  }

  protected formatDate(iso: string): string {
    return new Date(iso).toLocaleString('es-ES', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }
}
