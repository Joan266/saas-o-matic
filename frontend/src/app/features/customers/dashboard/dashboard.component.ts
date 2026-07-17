import { Component, inject, signal, computed, OnInit, DestroyRef } from '@angular/core';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { debounceTime, distinctUntilChanged, Subject, switchMap, startWith } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { CurrencyService } from '../../../core/services/currency.service';
import { Customer } from '../../../core/models/types';
import { COUNTRY_LABELS } from '../../../core/models/types';

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
  protected readonly loading = signal(true);
  protected readonly searchQuery = signal('');

  private readonly search$ = new Subject<string>();

  protected readonly totalSimulations = computed(() =>
    this.customers().reduce((acc, _) => acc + 0, 0),
  );

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
    this.search$
      .pipe(
        startWith(''),
        debounceTime(300),
        distinctUntilChanged(),
        switchMap(q => {
          this.loading.set(true);
          return this.api.getCustomers(q || undefined);
        }),
        takeUntilDestroyed(this.destroyRef),
      )
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
    this.search$.next(value);
  }

  get mrr(): number {
    return this.customers().reduce((acc, c) => acc + 0, 0);
  }
}
