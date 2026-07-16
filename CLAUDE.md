# SaaS-O-Matic — Contexto de proyecto para Claude

## Qué es este proyecto
Herramienta interna de billing simulation para equipo comercial.
Spec completa: `ai-workspace/specs/01-product-spec.md`
Decisiones de ingeniería: `ai-workspace/specs/02-engineering-decisions.md`

## Stack
- Backend: Python 3.12 + FastAPI + SQLite (sin ORM)
- Frontend: Angular 17+ standalone components + Angular Material + Signals
- Tests backend: pytest
- Tests frontend: Jest + Angular Testing Library
- Visual QA: Playwright (screenshots tras cada vista)

## Reglas que NUNCA se rompen

### Backend
- Las rutas NUNCA acceden a la DB directamente — siempre a través de services
- Los services NUNCA importan tipos de FastAPI
- Rutas declaradas como `def` (NO `async def`) con SQLite — FastAPI las corre en threadpool automáticamente
- Queries SQL siempre con parámetros posicionales `?` — nunca f-strings
- Errores siempre en formato `{"detail": "mensaje", "code": "ERROR_CODE"}`
- Logging en cada request: `[timestamp] METHOD /path → status (Xms)`
- Conexiones SQLite: siempre con context manager, nunca dejar conexión abierta

### Frontend
- URLs del backend SOLO en `environment.ts` — nunca hardcodeadas en servicios
- Tipos TypeScript deben ser espejo exacto de los Pydantic schemas del backend
- Conversión snake_case → camelCase se hace en `api.service.ts`, nunca en componentes
- Estado de divisa SOLO en `CurrencyService` con Signals — nunca en componentes
- Errores HTTP capturados en interceptor global — nunca en cada componente por separado
- Desuscribirse de todos los Observables en `ngOnDestroy` (o usar `takeUntilDestroyed`)

### Git
- `main` siempre funciona y despliega limpio
- Una rama por feature: `feat/billing-engine`, `feat/customer-form`, etc.
- Commits atómicos: un commit = una cosa concreta
- Nunca hacer commit directamente a main

## Algoritmos — NO tirar de memoria, usar fuentes oficiales

### DNI/NIE/CIF español
- Fuente oficial: AEAT + BOE
- DNI: 8 dígitos + letra. Letra = "TRWAGMYFPDXBNJZSQVHLCKE"[numero % 23]
- NIE: X→0, Y→1, Z→2, luego igual que DNI
- CIF: posiciones IMPARES (1,3,5,7 = índices 0,2,4,6) × 2 sumando cifras; posiciones PARES (2,4,6 = índices 1,3,5) directo
  control_digit = (10 - ((A+B) % 10)) % 10 | control_letra = "JABCDEFGHI"[control_digit]
- TRAMPA FRECUENTE: NO invertir pares e impares — verificar siempre con B83584469 (CIF válido conocido)

### Tiered pricing
- Acumulativo, NO precio único por volumen
- Tramo 1: 1–10 usuarios → 10€/u
- Tramo 2: 11–50 usuarios → 8€/u (solo esos 40)
- Tramo 3: >50 usuarios → 5€/u (solo el exceso)
- Test obligatorio: 10u=100€, 11u=108€, 50u=420€, 51u=425€, 60u=470€

## Gestión de errores — protocolo completo

### Backend devuelve siempre
```json
{ "detail": "Mensaje legible para el usuario", "code": "SNAKE_CASE_CODE" }
```
Códigos definidos: FISCAL_ID_INVALID, DUPLICATE_FISCAL_ID, CUSTOMER_NOT_FOUND,
INVALID_PLAN, VALIDATION_ERROR

### Frontend interpreta
- Interceptor HTTP en `core/interceptors/error.interceptor.ts`
- Traduce códigos a mensajes en español para el usuario
- 422 → mostrar mensaje del campo específico
- 409 → "Este identificador fiscal ya está registrado"
- 404 → redirigir o mostrar estado vacío
- 5xx → "Error del servidor, inténtalo de nuevo"
- Sin conexión → "No se puede conectar con el servidor"

## Performance — qué vigilar

### Backend
- SQLite: conexiones siempre cerradas con context manager
- FastAPI es async pero SQLite es síncrono — usar `run_in_executor` si hay operaciones lentas
- Rate limiting básico: slowapi (1 librería, 5 minutos de setup)
- Logging de duración de cada request para identificar queries lentas

### Frontend
- Unsubscribe de todos los Observables
- `trackBy` en todos los `*ngFor` con listas
- Llamada a exchange rate API: una sola vez al iniciar, cachear en Signal
- Debounce en el buscador (300ms) para no saturar el backend

## Tests — qué cubrir obligatoriamente

### Backend (pytest)
- `billing.py`: todos los casos de tramos (incluyendo exactamente 10, 11, 50, 51 usuarios)
- `fiscal_validator.py`: DNI válido, DNI letra incorrecta, NIE válido, CIF válido, CIF inválido, string aleatorio
- `POST /customers`: happy path, fiscal_id duplicado, DNI inválido con country=ES, DNI con country=DE (debe pasar)
- `POST /simulations`: happy path, customer inexistente, usuarios=0

### Frontend (Jest)
- `billing.utils.ts`: mismos casos que backend
- `CurrencyService`: conversión correcta, cambio de divisa actualiza Signal

## Visual QA con Playwright
Tras completar cada vista, tomar screenshot y verificar:
1. Dashboard con listado de clientes
2. Detalle de cliente con simulaciones
3. Formulario de simulación con slider en distintos valores
4. Formulario de nuevo cliente con error de validación visible

Screenshots guardados en `ai-workspace/vibe-coding/screenshots/`
