# Mock Data & Edge Cases

## Clientes de demo (insertar si DB vacía)

| ID | Empresa            | Fiscal ID  | País | Plan         | Notas                        |
|----|--------------------|------------|------|--------------|------------------------------|
| 1  | Acme Corp SL       | A28000727  | ES   | enterprise   | CIF español válido (verificado: suma=23, control=7 ✓) |
| 2  | TechGmbH           | DE123456   | DE   | professional | País no-ES, sin validación   |
| 3  | Startup Inc        | US-TAX-001 | US   | starter      | USA, IVA 0%                  |
| 4  | Renault France SA  | FR-456789  | FR   | professional | Francia, IVA 20%             |
| 5  | González & Asoc.   | 12345678Z  | ES   | starter      | DNI español válido           |

## Edge cases — Algoritmo de tramos (billing)

| Usuarios | Cálculo esperado                              | Total €  |
|----------|-----------------------------------------------|----------|
| 1        | 1×10                                          | 10.00    |
| 10       | 10×10                                         | 100.00   |
| 11       | 10×10 + 1×8                                   | 108.00   |
| 50       | 10×10 + 40×8                                  | 420.00   |
| 51       | 10×10 + 40×8 + 1×5                            | 425.00   |
| 60       | 10×10 + 40×8 + 10×5                           | 470.00   |
| 200      | 10×10 + 40×8 + 150×5                          | 1170.00  |
| 0        | Error 422 (active_users >= 1)                 | —        |
| -1       | Error 422                                     | —        |

## Edge cases — Validación DNI/NIE/CIF

### DNI válidos
| Input      | Resultado |
|------------|-----------|
| 12345678Z  | Válido    |
| 00000000T  | Válido    |
| 99999999R  | Válido    |

### DNI inválidos
| Input      | Resultado                              |
|------------|----------------------------------------|
| 12345678A  | Inválido — letra incorrecta            |
| 1234567Z   | Inválido — solo 7 dígitos              |
| 123456789Z | Inválido — 9 dígitos                   |
| ABCDEFGHZ  | Inválido — no son dígitos              |
| (vacío)    | Error 422                              |

### NIE válidos
| Input      | Resultado |
|------------|-----------|
| X1234567L  | Válido    |
| Y0000000T  | Válido    |
| Z3456789P  | Válido    |

### CIF válidos
| Input      | Resultado                                              |
|------------|--------------------------------------------------------|
| A28000727  | Válido — suma_impar=8, suma_par=15, total=23, ctrl=7 ✓ |
| B83584466  | Válido — suma_impar=19, suma_par=15, total=34, ctrl=6 ✓|

### CIF inválidos
| Input      | Resultado                                         |
|------------|---------------------------------------------------|
| B83584469  | Inválido — control esperado 6, recibido 9         |
| A28000720  | Inválido — control esperado 7, recibido 0         |
| B8358446   | Inválido — formato (solo 6 dígitos centrales)     |

### Casos especiales país no-ES
| Input      | País | Resultado                              |
|------------|------|----------------------------------------|
| CUALQUIER  | DE   | Aceptado sin validar                   |
| 00000000T  | DE   | Aceptado (aunque sea DNI válido)       |
| INVALIDO!  | US   | Aceptado                               |

## Edge cases — IVA

| País | IVA   | Base 100€ → Total |
|------|-------|-------------------|
| ES   | 21%   | 121.00€           |
| DE   | 19%   | 119.00€           |
| FR   | 20%   | 120.00€           |
| UK   | 20%   | 120.00€           |
| MX   | 16%   | 116.00€           |
| US   | 0%    | 100.00€           |
| JP   | 0%    | 100.00€ (fallback)|

## Edge cases — Conversión de divisa

| Escenario                       | Comportamiento esperado               |
|---------------------------------|---------------------------------------|
| API de tasas no disponible      | Mostrar costes en EUR, warning visible|
| Divisa seleccionada no en rates | Fallback a EUR                        |
| Cambio de divisa con historial  | Toda la tabla se recalcula al instante|
| Tasa = 0 (datos corruptos)      | Fallback a EUR, no dividir por cero   |

## Edge cases — Formulario de nuevo cliente

| Escenario                           | Comportamiento esperado               |
|-------------------------------------|---------------------------------------|
| Email sin @                         | Error de validación en campo          |
| Fiscal ID duplicado                 | Error 409 → mensaje claro en UI       |
| DNI inválido con país ES            | Error 422 → mensaje específico DNI    |
| DNI "inválido" con país DE          | Guardado correctamente                |
| Empresa con caracteres especiales   | Guardado correctamente (é, ñ, ü...)   |
| Empresa vacía                       | Error de validación                   |
| Plan fuera de enum                  | Error 422 (no debería ocurrir con select) |

## Simulaciones de ejemplo (para historial rico en demo)

Para cliente Acme Corp (enterprise, ES, 21% IVA):

| Usuarios | Storage | API calls  | Base €  | Total con IVA € |
|----------|---------|------------|---------|-----------------|
| 5        | 50      | 10,000     | 50.00   | 60.50           |
| 15       | 100     | 50,000     | 140.00  | 169.40          |
| 50       | 500     | 200,000    | 420.00  | 508.20          |
| 75       | 1000    | 1,000,000  | 595.00  | 719.95          |
| 200      | 1000    | 1,000,000  | 1170.00 | 1415.70         |
