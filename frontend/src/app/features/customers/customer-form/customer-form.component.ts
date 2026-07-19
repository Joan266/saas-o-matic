import { Component, inject, signal, OnInit, DestroyRef } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ApiService } from '../../../core/services/api.service';
import { COUNTRY_LABELS, Plan } from '../../../core/models/types';
import { validateSpanishFiscalId } from '../../../shared/utils/fiscal-validator.utils';

const COUNTRIES = Object.entries(COUNTRY_LABELS).map(([code, label]) => ({ code, label }));

const PLANS: { value: Plan; label: string }[] = [
  { value: 'starter', label: 'Starter' },
  { value: 'professional', label: 'Professional' },
  { value: 'enterprise', label: 'Enterprise' },
];

@Component({
  selector: 'app-customer-form',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './customer-form.component.html',
  styleUrl: './customer-form.component.css',
})
export class CustomerFormComponent implements OnInit {
  private readonly api = inject(ApiService);
  private readonly router = inject(Router);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly submitting = signal(false);
  protected readonly fiscalIdError = signal<string | null>(null);
  protected readonly fiscalIdType = signal<string | null>(null);

  protected get fiscalIdTouched(): boolean {
    return !!this.form.get('fiscalId')?.touched;
  }

  protected readonly countries = COUNTRIES;
  protected readonly plans = PLANS;

  protected readonly form = this.fb.group({
    company: ['', [Validators.required, Validators.minLength(2)]],
    country: ['ES', Validators.required],
    plan: ['starter' as Plan, Validators.required],
    fiscalId: ['', [Validators.required, this.fiscalIdValidator()]],
    email: ['', [Validators.required, Validators.email]],
  });

  ngOnInit(): void {
    // Re-validate fiscalId when country changes — updateValueAndValidity triggers
    // the fiscalId validator AND the valueChanges subscription below, so
    // runFiscalValidation() is called once via fiscalId.valueChanges, not twice.
    this.form.get('country')!.valueChanges.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.form.get('fiscalId')!.updateValueAndValidity();
    });

    this.form.get('fiscalId')!.valueChanges.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(() => {
      this.runFiscalValidation();
    });
  }

  private fiscalIdValidator() {
    return (control: AbstractControl): ValidationErrors | null => {
      const country = this.form?.get('country')?.value;
      if (country !== 'ES') return null;
      const val = control.value as string;
      if (!val) return null;
      const result = validateSpanishFiscalId(val);
      return result.valid ? null : { fiscalId: true };
    };
  }

  private runFiscalValidation(): void {
    const country = this.form.get('country')!.value;
    const val = this.form.get('fiscalId')!.value as string;

    if (country !== 'ES' || !val) {
      this.fiscalIdError.set(null);
      this.fiscalIdType.set(null);
      return;
    }

    const result = validateSpanishFiscalId(val);
    this.fiscalIdType.set(result.type ?? null);
    this.fiscalIdError.set(result.valid ? null : (result.suggestion ?? 'Identificador fiscal inválido.'));
  }

  protected onSubmit(): void {
    if (this.form.invalid || this.submitting()) return;

    const val = this.form.getRawValue();
    this.submitting.set(true);

    this.api.createCustomer({
      company: val.company!,
      fiscalId: val.fiscalId!,
      email: val.email!,
      country: val.country!,
      plan: val.plan as Plan,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (customer) => {
        this.router.navigate(['/customers', customer.id]);
      },
      error: () => {
        this.submitting.set(false);
      },
    });
  }

  protected fieldInvalid(name: string): boolean {
    const ctrl = this.form.get(name)!;
    return ctrl.invalid && ctrl.touched;
  }
}
