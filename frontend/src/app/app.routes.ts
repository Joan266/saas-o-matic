import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/customers/dashboard/dashboard.component').then(
        m => m.DashboardComponent,
      ),
  },
  {
    path: 'customers/new',
    loadComponent: () =>
      import('./features/customers/customer-form/customer-form.component').then(
        m => m.CustomerFormComponent,
      ),
  },
  {
    path: 'customers/:id',
    loadComponent: () =>
      import('./features/customers/customer-detail/customer-detail.component').then(
        m => m.CustomerDetailComponent,
      ),
  },
  {
    path: 'customers/:id/simulate',
    loadComponent: () =>
      import('./features/simulations/simulation-form/simulation-form.component').then(
        m => m.SimulationFormComponent,
      ),
  },
  { path: '**', redirectTo: '' },
];
