import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, throwError } from 'rxjs';

const ERROR_MESSAGES: Record<string, string> = {
  FISCAL_ID_INVALID: 'El identificador fiscal no es válido.',
  DUPLICATE_FISCAL_ID: 'Este identificador fiscal ya está registrado.',
  CUSTOMER_NOT_FOUND: 'Cliente no encontrado.',
  INVALID_PLAN: 'El plan seleccionado no es válido.',
  VALIDATION_ERROR: 'Error de validación en los datos enviados.',
};

function resolveMessage(error: HttpErrorResponse): string {
  if (error.status === 0) return 'No se puede conectar con el servidor.';
  if (error.status === 409) return 'Este identificador fiscal ya está registrado.';
  if (error.status === 404) return 'Recurso no encontrado.';
  if (error.status >= 500) return 'Error del servidor. Inténtalo de nuevo.';

  const code: string | undefined = error.error?.code;
  if (code && ERROR_MESSAGES[code]) return ERROR_MESSAGES[code];

  const detail: string | undefined = error.error?.detail;
  if (detail) return detail;

  return 'Error inesperado. Inténtalo de nuevo.';
}

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  // Exchange rate errors are handled by CurrencyService directly
  if (req.url.includes('open.er-api.com')) {
    return next(req);
  }

  const snackBar = inject(MatSnackBar);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      snackBar.open(resolveMessage(error), 'Cerrar', {
        duration: 5000,
        panelClass: ['snack-error'],
      });
      return throwError(() => error);
    }),
  );
};
