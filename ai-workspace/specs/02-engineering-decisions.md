# Engineering Decisions — SaaS-O-Matic

## 1. Payload validation

**Backend:** Pydantic v2 valida todo input antes de llegar a services.
Campos inesperados son ignorados (`model_config = ConfigDict(extra='ignore')`).
Tipos incorrectos devuelven 422 automáticamente con detalle del campo.

**Frontend:** Reactive Forms con Validators de Angular.
Interfaces TypeScript reflejan exactamente los Pydantic schemas.
Conversión snake_case ↔ camelCase centralizada en `api.service.ts`.

## 2. Error handling

Formato único de error en backend:
```json
{ "detail": "Mensaje legible", "code": "ERROR_CODE" }
```

Interceptor HTTP en Angular captura todos los errores.
Los componentes nunca manejan errores HTTP directamente.

## 3. Logging backend

Formato por request:
```
2024-01-15 10:23:45 | POST /customers | 201 | 12ms
2024-01-15 10:23:46 | POST /customers | 422 | FISCAL_ID_INVALID | 3ms
```

Implementado con middleware FastAPI + módulo `logging` estándar.

## 4. Seguridad

- Rate limiting: slowapi, máx 60 req/min por IP
- CORS restringido a localhost:4200 (Angular dev) y localhost:3000
- Queries SQL siempre parametrizadas, nunca interpolación de strings
- Campos devueltos al frontend: solo los definidos en el schema `*Out`
  (nunca exponer campos internos o de audit trail no necesarios)
- Inputs saneados por Pydantic antes de llegar a la DB

## 5. Estructura de datos — alineación front/back

El backend es la fuente de verdad. El frontend refleja los tipos exactos.

```
Backend (Pydantic)          Frontend (TypeScript)
─────────────────           ─────────────────────
CustomerCreate        →     CustomerCreate
CustomerOut           →     Customer
SimulationCreate      →     SimulationCreate
SimulationOut         →     Simulation
```

La conversión de divisa ocurre exclusivamente en el frontend.
El backend persiste y devuelve siempre en EUR.

## 6. Estado en frontend

`CurrencyService` (singleton, providedIn: 'root'):
- `rates = signal<Record<string, number>>({EUR: 1})`
- `currentCurrency = signal<string>('EUR')`
- `convert(eur: number): string` — calculado con computed()

Cargado una sola vez al iniciar la app. Ningún componente llama
directamente a la API de tipos de cambio.

## 7. Git workflow

```
main          ← siempre funciona
feat/backend-setup
feat/billing-engine
feat/fiscal-validator
feat/customer-endpoints
feat/simulation-endpoints
feat/angular-setup
feat/currency-service
feat/dashboard
feat/customer-detail
feat/simulation-form
feat/customer-form
feat/mock-data
feat/readme
```

Merge a main solo cuando la feature tiene tests y funciona end-to-end.

## 8. Performance

**Backend:**
- Rutas declaradas como `def` (NO `async def`) — FastAPI las corre en threadpool automáticamente.
  Usar `async def` con SQLite síncrono es peor: overhead sin beneficio. (Fuente: fastapi.tiangolo.com/async)
- Context manager garantiza cierre de conexión SQLite en cada request
- Logging de duración para detectar queries lentas (>100ms = warning)
- Rate limiter: slowapi (alpha quality, válido para demo; producción real requeriría Redis)

**Frontend:**
- `trackBy` en `*ngFor` de listas de clientes y simulaciones
- Búsqueda de clientes: filtro local con `computed()` sobre el array en memoria.
  Decisión: una herramienta interna con decenas de clientes no justifica una llamada
  HTTP por búsqueda. Carga única al init, filtrado instantáneo sin red.
- `takeUntilDestroyed()` en todos los Observables
- Exchange rate: fetch único al init con `timeout(5000)` y `retry(2)`.
  Si la API externa falla tras 3 intentos, la app opera en EUR (fallback seguro).

## 9. Tests de rendimiento

**Backend:** pytest-benchmark para las funciones de cálculo.
Target: `calculate_base_cost(200)` < 1ms.

**Frontend:** Angular DevTools para detectar ciclos de change detection excesivos.
El slider de simulación no debe provocar más de 1 ciclo por movimiento.

## 10. Mock data con edge cases

Ver `ai-workspace/specs/03-mock-data.md`

---

## 11. Control de divisa — punto único en navbar

**Decisión:** El selector global del navbar es el único punto de control de divisa.

Los componentes `CustomerDetail` y `SimulationForm` tenían tabs locales `['EUR','USD','GBP']`
hardcodeadas — redundantes con el navbar y con solo 3 de las 7 divisas disponibles.
Se eliminaron. Todos los componentes consumen `CurrencyService.currentCurrency()` via Signal.

## 12. Formulario de simulación — solo slider de usuarios

**Decisión:** El formulario de simulación tiene únicamente el slider de usuarios activos.

El documento original pide: *"Un slider o controles dinámicos para ajustar la cantidad
de usuarios"*. Los sliders de storage (1–1000 GB) y API calls (0–1M) no están pedidos
en la UI. Se mantienen en el modelo de datos del backend (el endpoint los acepta con
valores por defecto) pero no se exponen en el formulario — evita confundir al usuario
con controles que no afectan al precio.

## 13. Input numérico + slider sincronizados

**Decisión:** El slider de usuarios (1–200) se complementa con un input numérico sin límite.

El slider cubre el rango visual frecuente. El input permite simular empresas grandes
(500, 1000+ usuarios) sin límite artificial. Ambos se sincronizan: el slider se mueve
hasta su máximo (200) cuando el input supera ese valor, pero el cálculo usa siempre
el valor real del signal.

## 14. GET /stats — endpoint de aggregados del dashboard

**Decisión:** Endpoint dedicado para los tres KPIs del dashboard.

Alternativas consideradas:
- Calcular en frontend desde la lista de clientes → imposible sin datos de simulaciones
- N+1 queries (una por cliente para sus simulaciones) → descartado por ineficiencia
- JOIN en `GET /customers` → solo sirve para `last_simulation_at`, no para totales globales

`GET /stats` hace 3 queries SQL simples y devuelve `total_customers`, `total_simulations`
y `total_mrr` (suma de la simulación más reciente por cliente).
