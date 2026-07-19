import { Component, inject, OnInit } from '@angular/core';
import { RouterOutlet, RouterLink } from '@angular/router';
import { CurrencyService } from './core/services/currency.service';
import { CurrencySelectorComponent } from './shared/components/currency-selector/currency-selector.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, CurrencySelectorComponent],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  protected readonly currencyService = inject(CurrencyService);

  ngOnInit(): void {
    this.currencyService.loadRates();
  }
}
