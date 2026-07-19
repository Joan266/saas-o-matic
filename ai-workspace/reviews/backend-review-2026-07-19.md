# Revisión de calidad — Backend + Frontend SaaS-O-Matic
**Fecha:** 2026-07-19
**Rama:** feat/angular-setup
**Archivos revisados:** main.py, config.py, database.py, schemas.py, routes/*, services/*, tests/* + 17 archivos frontend

---

## Resumen ejecutivo

El backend tiene **1 bug activo visible al usuario**, **2 violaciones de las reglas del proyecto** y **4 problemas menores**. El frontend tiene **2 bugs activos visibles al usuario** y **11 problemas de calidad**. Los servicios de dominio (`billing.py`, `fiscal_validator.py`) y los tests son ejemplares.

---

# BACKEND

## Bugs activos — afectan al usuario

### BUG-01 — Snackbar muestra "[object Object]" al rechazar un fiscal_id español inválido

**Archivos:** `app/routes/customers.py:20-23`, `frontend/src/app/core/interceptors/error.interceptor.ts:20-24`
**Severidad:** Alta

**Causa raíz:**

El backend usa `HTTPException` con un dict como `detail`:
```python
raise HTTPException(
    status_code=422,
    detail={"detail": str(exc), "code": "FISCAL_ID_INVALID"},
)
```

FastAPI envuelve automáticamente en `{"detail": ...}`, por lo que el body que llega al frontend es:
```json
{"detail": {"detail": "CIF 'B83584469' inválido...", "code": "FISCAL_ID_INVALID"}}
```

El interceptor busca `error.error?.code` (raíz del body), pero el `code` está en `error.error.detail.code`:
- `error.error?.code` → `undefined`
- `error.error?.detail` → el objeto `{detail: "...", code: "..."}` (truthy pero no string)
- El snackbar recibe el objeto y muestra `[object Object]`

**Efecto secundario:** El diccionario `ERROR_MESSAGES` del interceptor nunca se usa — dead code.

**Fix:** Usar `JSONResponse` en vez de `HTTPException` para body plano:
```python
from fastapi.responses import JSONResponse
return JSONResponse(
    status_code=422,
    content={"detail": str(exc), "code": "FISCAL_ID_INVALID"},
)
```

---

## Violaciones de reglas del proyecto

### REG-01 — Las rutas acceden directamente a la base de datos

**Archivos:** `app/routes/customers.py`, `app/routes/simulations.py`, `app/routes/stats.py`
**Regla violada:** *"Las rutas NUNCA acceden a la DB directamente — siempre a través de services"* (CLAUDE.md)

Los tres archivos de rutas llaman a `get_conn()` directamente. No existe ningún archivo de servicio para customers, simulations ni stats.

Consecuencias:
- Imposible hacer unit tests de persistencia sin levantar la BD
- Si cambia la fuente de datos, hay que tocar los routes
- La lógica de negocio puede dispersarse sin control

**Fix:** Crear `app/services/customers.py` y `app/services/simulations.py` con las funciones SQL, y que los routes solo llamen a esos servicios.

### REG-02 — Errores 404 y 409 no incluyen el campo `code`

**Archivos:** `app/routes/customers.py:32-35`, `app/routes/simulations.py:23`, `app/routes/simulations.py:61`
**Regla violada:** *"Errores siempre en formato `{"detail": "mensaje", "code": "ERROR_CODE"}`"* (CLAUDE.md)

```python
raise HTTPException(status_code=409, detail="Este identificador fiscal ya está registrado.")
raise HTTPException(status_code=404, detail="Cliente no encontrado.")
```

El interceptor los captura por status code, así que funcionalmente es correcto hoy, pero los códigos `DUPLICATE_FISCAL_ID` y `CUSTOMER_NOT_FOUND` de la spec nunca llegan al frontend.

---

## Problemas de calidad de código (backend)

### CODE-01 — `COUNTRY_TAX` en schemas.py es código muerto

**Archivo:** `app/models/schemas.py:5-12`

Definido pero no usado en ningún sitio. Duplica exactamente `_COUNTRY_TAX` de `billing.py`.
**Fix:** Eliminar las líneas 5-12 de `schemas.py`.

### CODE-02 — `StatsOut` definida en el route file en vez de en schemas.py

**Archivo:** `app/routes/stats.py:9-13`

Todos los modelos Pydantic viven en `schemas.py` excepto este.
**Fix:** Mover `StatsOut` a `schemas.py` e importarla en `stats.py`.

### CODE-03 — HTTPException 409 se lanza dentro del context manager de DB

**Archivo:** `app/routes/customers.py:25-35`

La excepción se lanza dentro de `with get_conn()`, disparando un `conn.rollback()` innecesario (no hay nada que revertir). Engañoso en lectura de código.
**Fix:** Mover la comprobación de duplicado fuera del bloque de escritura.

### CODE-04 — `_seed_simulations` silencia errores sin logging

**Archivo:** `app/services/seed.py:60-61`

```python
if not customer:
    continue  # silencioso
```

**Fix:** `logger.warning("Seed: customer with fiscal_id=%s not found, skipping", fiscal_id)` antes del `continue`.

---

# FRONTEND

## Bugs activos — afectan al usuario

### BUG-02 — El tier preview muestra precios en EUR aunque la divisa sea otra

**Archivo:** `frontend/src/app/features/simulations/simulation-form/simulation-form.component.html:79`
**Severidad:** Alta

```html
<!-- Panel izquierdo — hardcodeado en EUR -->
<span class="tier-row__cost">{{ tier.subtotal | number:'1.2-2' }}€</span>

<!-- Panel derecho — respeta la divisa seleccionada -->
<span class="cost-row__value">{{ currency.format(baseCost()) }}</span>
```

Si el usuario selecciona USD, el panel izquierdo muestra "100.00€" y el derecho "$107.00". Datos contradictorios en la misma pantalla.

**Fix:** `{{ currency.format(tier.subtotal) }}` en la línea 79.

### BUG-03 — `lastSim` en customer-detail muestra la simulación MÁS ANTIGUA, no la más reciente

**Archivo:** `frontend/src/app/features/customers/customer-detail/customer-detail.component.ts:33`
**Severidad:** Alta — dato incorrecto visible al usuario

```typescript
protected readonly lastSim = computed(() => {
  const sims = this.simulations();
  if (!sims.length) return '—';
  return new Date(sims[sims.length - 1].createdAt)...  // ← toma el último del array
});
```

El backend devuelve `ORDER BY created_at DESC` — `sims[0]` es la más reciente, `sims[length-1]` es la más antigua. El campo "última simulación" muestra la fecha incorrecta para cualquier cliente con más de una simulación.

**Fix:** `[...sims].sort((a, b) => a.createdAt < b.createdAt ? -1 : 1).at(-1)` — o simplemente `sims[0]` dado que el orden del backend está garantizado.

---

## Problemas de calidad de código (frontend)

### FE-01 — Variable `start` en billing.utils.ts es dead code

**Archivo:** `frontend/src/app/shared/utils/billing.utils.ts:34,47`

```typescript
let start = 1;       // nunca se usa en el valor de retorno
// ...
start += chunk;      // actualizada pero ignorada
```

**Fix:** Eliminar `let start = 1` y `start += chunk`.

### FE-02 — Color `#4a235a` duplicado en `avatarColors`

**Archivo:** `frontend/src/app/features/customers/dashboard/dashboard.component.ts:38-41` (índices 3 y 9)

**Fix:** Reemplazar uno por un color distinto.

### FE-03 — `avatarColors`, `avatarColor()` e `initials()` duplicados entre dashboard y customer-detail

**Archivos:** `dashboard.component.ts:43-55`, `customer-detail.component.ts:36-39`

Viola DRY. Si cambia el algoritmo hay que actualizarlo en dos sitios.
**Fix:** Extraer a `shared/utils/avatar.utils.ts` e importar en ambos.

### FE-04 — Input de usuarios diverge del signal cuando el valor es < 1

**Archivo:** `frontend/src/app/features/simulations/simulation-form/simulation-form.component.ts:67-70`

```typescript
protected onUsersInputChange(event: Event): void {
  const val = Number((event.target as HTMLInputElement).value);
  if (val >= 1) this.activeUsers.set(Math.floor(val));  // si val < 1, no actualiza
  // el input sigue mostrando 0 aunque el signal siga en el valor anterior
}
```

**Fix:** Si `val < 1`, forzar el input a 1: `(event.target as HTMLInputElement).value = '1'`.

### FE-05 — Botón "Guardar simulación" usa `(click)` en vez de `type="submit"`

**Archivo:** `frontend/src/app/features/simulations/simulation-form/simulation-form.component.html:123-128`

Pulsar Enter en el formulario no guarda.
**Fix:** Envolver en `<form (ngSubmit)="onSave()">` y cambiar el botón a `type="submit"`.

### FE-06 — `storageGb: 1` y `apiCalls: 0` son magic numbers sin comentario

**Archivo:** `frontend/src/app/features/simulations/simulation-form/simulation-form.component.ts:79-80`
**Severidad:** Baja — solo documentación

**Fix:** Añadir `// storage_gb y api_calls no implementados en esta versión`.

### FE-07 — Tasa por usuario en customer-detail muestra € hardcodeado

**Archivo:** `frontend/src/app/features/customers/customer-detail/customer-detail.component.html:119`

`{{ tier.rate }}€` junto a subtotales con `currency.format()`. Inconsistente visualmente.
**Fix:** Aceptable dejar en EUR con nota `(en EUR)`, o convertir también con `currency.format(tier.rate)`.

### FE-08 — Mensaje 409 duplicado entre `ERROR_MESSAGES` y el handler de status code

**Archivo:** `frontend/src/app/core/interceptors/error.interceptor.ts:8,17`
**Nota:** Este issue desaparecerá parcialmente al corregir BUG-01 (backend). Una vez que el 409 incluya `code: "DUPLICATE_FISCAL_ID"`, la entrada en `ERROR_MESSAGES` podrá reemplazar el check explícito por status code.

### FE-09 — `'open.er-api.com'` es un magic string en el interceptor

**Archivo:** `frontend/src/app/core/interceptors/error.interceptor.ts:31`

Si cambia el proveedor de tipos de cambio, el interceptor deja de excluirlo silenciosamente.
**Fix:** Exportar la URL base desde `environment.ts` y comparar contra esa constante.

### FE-10 — Parámetro `q` en `getCustomers()` es dead code

**Archivo:** `frontend/src/app/core/services/api.service.ts:70`

La búsqueda es local desde la refactorización. El parámetro se envía pero el dashboard nunca lo pasa.
**Fix:** Eliminar el parámetro `q` si el filtrado local es definitivo.

### FE-11 — `symbols` duplicado entre `CurrencySelector` y `CurrencyService`

**Archivo:** `frontend/src/app/shared/components/currency-selector/currency-selector.component.ts:99-101`

Dos fuentes de verdad para los símbolos de divisa.
**Fix:** Exportar los símbolos como constante en `types.ts` y referenciarla en ambos sitios.

### FE-12 — Doble llamada a `validateSpanishFiscalId` en cambio de país

**Archivo:** `frontend/src/app/features/customers/customer-form/customer-form.component.ts:51-53`

Al cambiar el país se llama `updateValueAndValidity()` (que ejecuta el validator de Angular, que llama a `validateSpanishFiscalId`) y luego `runFiscalValidation()` (que la llama otra vez).
**Fix:** Eliminar la llamada `runFiscalValidation()` de la suscripción a `country.valueChanges`.

---

# Tabla resumen completa

| ID | Capa | Tipo | Severidad | Archivo(s) | Estado |
|---|---|---|---|---|---|
| BUG-01 | Backend | Bug activo | Alta | routes/customers.py + error.interceptor.ts | Corregido |
| BUG-02 | Frontend | Bug activo | Alta | simulation-form.component.html:79 | Corregido |
| BUG-03 | Frontend | Bug activo | Alta | customer-detail.component.ts:33 | Corregido |
| REG-01 | Backend | Violación de regla | Media | routes/customers.py, simulations.py, stats.py | Corregido |
| REG-02 | Backend | Violación de regla | Media | routes/customers.py, routes/simulations.py | Corregido |
| CODE-01 | Backend | Código muerto | Baja | models/schemas.py | Corregido |
| CODE-02 | Backend | Inconsistencia | Baja | routes/stats.py | Corregido |
| CODE-03 | Backend | Code smell | Baja | routes/customers.py | Corregido |
| CODE-04 | Backend | Log silencioso | Baja | services/seed.py | Corregido |
| FE-01 | Frontend | Código muerto | Baja | billing.utils.ts:34 | Corregido |
| FE-02 | Frontend | Cosmético | Baja | dashboard.component.ts:39 | Corregido |
| FE-03 | Frontend | DRY violation | Media | dashboard.ts + customer-detail.ts | Corregido |
| FE-04 | Frontend | UX bug | Media | simulation-form.component.ts:68 | Corregido |
| FE-05 | Frontend | UX bug | Media | simulation-form.component.html:123 | Corregido |
| FE-06 | Frontend | Documentación | Baja | simulation-form.component.ts:79 | Corregido |
| FE-07 | Frontend | Inconsistencia visual | Baja | customer-detail.component.html:119 | Corregido |
| FE-08 | Frontend | Código duplicado | Media | error.interceptor.ts:8+17 | Pendiente (depende BUG-01) |
| FE-09 | Frontend | Magic string | Media | error.interceptor.ts:31 | Corregido |
| FE-10 | Frontend | Dead code | Baja | api.service.ts:70 | Corregido |
| FE-11 | Frontend | DRY violation | Media | currency-selector.component.ts:99 | Corregido |
| FE-12 | Frontend | Performance | Media | customer-form.component.ts:51 | Corregido |
