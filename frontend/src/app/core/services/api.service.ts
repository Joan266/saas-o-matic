import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Customer, CustomerCreate, Simulation, SimulationCreate, Stats } from '../models/types';

interface CustomerRaw {
  id: number;
  company: string;
  fiscal_id: string;
  email: string;
  country: string;
  plan: string;
  created_at: string;
  updated_at: string;
  last_simulation_at?: string;
}

interface StatsRaw {
  total_customers: number;
  total_simulations: number;
  total_mrr: number;
}

interface SimulationRaw {
  id: number;
  customer_id: number;
  active_users: number;
  storage_gb: number;
  api_calls: number;
  base_cost: number;
  tax_rate: number;
  total_cost: number;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  private toCustomer(raw: CustomerRaw): Customer {
    return {
      id: raw.id,
      company: raw.company,
      fiscalId: raw.fiscal_id,
      email: raw.email,
      country: raw.country,
      plan: raw.plan as Customer['plan'],
      createdAt: raw.created_at,
      updatedAt: raw.updated_at,
      lastSimulationAt: raw.last_simulation_at,
    };
  }

  private toSimulation(raw: SimulationRaw): Simulation {
    return {
      id: raw.id,
      customerId: raw.customer_id,
      activeUsers: raw.active_users,
      storageGb: raw.storage_gb,
      apiCalls: raw.api_calls,
      baseCost: raw.base_cost,
      taxRate: raw.tax_rate,
      totalCost: raw.total_cost,
      createdAt: raw.created_at,
    };
  }

  getCustomers(q?: string): Observable<Customer[]> {
    let params = new HttpParams();
    if (q) params = params.set('q', q);
    return this.http
      .get<CustomerRaw[]>(`${this.base}/customers`, { params })
      .pipe(map(rows => rows.map(r => this.toCustomer(r))));
  }

  getCustomer(id: number): Observable<Customer> {
    return this.http
      .get<CustomerRaw>(`${this.base}/customers/${id}`)
      .pipe(map(r => this.toCustomer(r)));
  }

  createCustomer(payload: CustomerCreate): Observable<Customer> {
    const body = {
      company: payload.company,
      fiscal_id: payload.fiscalId,
      email: payload.email,
      country: payload.country,
      plan: payload.plan,
    };
    return this.http
      .post<CustomerRaw>(`${this.base}/customers`, body)
      .pipe(map(r => this.toCustomer(r)));
  }

  getSimulations(customerId: number): Observable<Simulation[]> {
    return this.http
      .get<SimulationRaw[]>(`${this.base}/simulations/customer/${customerId}`)
      .pipe(map(rows => rows.map(r => this.toSimulation(r))));
  }

  getStats(): Observable<Stats> {
    return this.http
      .get<StatsRaw>(`${this.base}/stats`)
      .pipe(map(r => ({
        totalCustomers: r.total_customers,
        totalSimulations: r.total_simulations,
        totalMrr: r.total_mrr,
      })));
  }

  createSimulation(payload: SimulationCreate): Observable<Simulation> {
    const body = {
      customer_id: payload.customerId,
      active_users: payload.activeUsers,
      storage_gb: payload.storageGb,
      api_calls: payload.apiCalls,
    };
    return this.http
      .post<SimulationRaw>(`${this.base}/simulations`, body)
      .pipe(map(r => this.toSimulation(r)));
  }
}
