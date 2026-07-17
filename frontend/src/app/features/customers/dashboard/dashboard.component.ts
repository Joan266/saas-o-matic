import { Component, inject, signal, computed, OnInit, DestroyRef } from '@angular/core';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { CurrencyService } from '../../../core/services/currency.service';
import { Customer, Stats, COUNTRY_LABELS } from '../../../core/models/types';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [RouterLink, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(ApiService);
  protected readonly currency = inject(CurrencyService);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly customers = signal<Customer[]>([]);
  protected readonly stats = signal<Stats | null>(null);
  protected readonly loading = signal(true);
  protected readonly searchQuery = signal('');

  protected readonly filteredCustomers = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    if (!q) return this.customers();
    return this.customers().filter(c =>
      c.company.toLowerCase().includes(q) ||
      c.fiscalId.toLowerCase().includes(q)
    );
  });

  protected readonly countryLabel = (code: string) =>
    COUNTRY_LABELS[code] ?? code;

  protected readonly avatarColors = [
    '#c84b31', '#2e4057', '#1b6ca8', '#4a235a', '#1e5631',
    '#7d3c98', '#1a5276', '#784212', '#1b4f72', '#4a235a',
  ];

  avatarColor(company: string): string {
    const idx = company.charCodeAt(0) % this.avatarColors.length;
    return this.avatarColors[idx];
  }

  initials(company: string): string {
    return company
      .split(' ')
      .slice(0, 2)
      .map(w => w[0])
      .join('')
      .toUpperCase();
  }

  ngOnInit(): void {
    this.api.getStats()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({ next: s => this.stats.set(s) });

    this.api.getCustomers()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: customers => {
          this.customers.set(customers);
          this.loading.set(false);
        },
        error: () => this.loading.set(false),
      });
  }

  onSearch(value: string): void {
    this.searchQuery.set(value);
  }

  protected formatLastSim(iso: string | undefined): string {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('es-ES', {
      day: '2-digit', month: 'short', year: 'numeric',
    });
  }
}
