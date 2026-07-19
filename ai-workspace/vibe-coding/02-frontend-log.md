# Frontend Log — Vibe Coding con IA

**Herramienta:** Claude Code (claude-sonnet-4-6)
**Rama:** feat/angular-setup

---

## Sesión 1 — Implementación de las 3 vistas principales

### Contexto
El backend estaba completo (89 tests). La infraestructura del frontend (ApiService, CurrencyService,
ErrorInterceptor, billing.utils.ts, tipos, tokens de diseño) también estaba hecha.
Restaban 3 stubs vacíos + el validador fiscal en TypeScript.

> **Nota sobre el historial git:** La infraestructura core (commit `5a19e61`) aparece como el
> commit más reciente en la rama porque los archivos estuvieron sin commitear durante el desarrollo
> y se añadieron al final junto con el resto de archivos sin traquear. El orden de desarrollo
> real fue: infraestructura → stubs → implementación → review. Los commits `da4dc77` y `185418a`
> reflejan ese trabajo correctamente.

### Prompt enviado a la IA
Plan estructurado con specs completas por componente:
- Estado exacto (qué Signals, qué computed())
- Secciones del template por orden
- Convenciones obligatorias (inject(), takeUntilDestroyed, trackBy, etc.)
- Sin libertad creativa en la arquitectura — solo implementación

### Lo que generó la IA
1. `fiscal-validator.utils.ts` — port de Python a TypeScript del validador DNI/NIE/CIF
2. `fiscal-validator.utils.spec.ts` — 11 tests Vitest
3. `CustomerDetailComponent` — 3 archivos (ts + html + css)
4. `CustomerFormComponent` — 3 archivos
5. `SimulationFormComponent` — 3 archivos

---

## Auditoría y correcciones aplicadas

### 1. Error en test NIE — RECHAZADO y corregido

**Problema detectado:** El spec tenía `Y3859799T` como NIE válido, pero al ejecutar los tests falló.

**Análisis:** Y→1, numberStr = "13859799", 13859799 % 23 = 22 → letra 'E', no 'T'.
La IA generó un valor de prueba sin verificar el algoritmo.

**Corrección:** Cambié `Y3859799T` → `Y3859799E` en el spec.

**Decisión:** MODIFICADO — el validador era correcto, el test tenía datos erróneos.

---

### 2. Error de tipos TypeScript con takeUntilDestroyed — DETECTADO y corregido

**Problema:** La IA usó el patrón:
```ts
private readonly destroyRef$ = takeUntilDestroyed(); // almacenado en campo
// ...
.pipe(this.destroyRef$).subscribe({ next: (customer) => ... }) // customer: unknown
```
Cuando `takeUntilDestroyed()` se almacena como campo, TypeScript infiere
`OperatorFunction<unknown, unknown>`, lo que rompe la inferencia de tipos en el subscribe.

**Corrección:** Cambié al patrón estándar del dashboard existente:
```ts
private readonly destroyRef = inject(DestroyRef);
// ...
.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(...)
```

**Decisión:** MODIFICADO — patrón funcional pero incompatible con strict TypeScript.

---

### 3. DB sin columna updated_at — DETECTADO en runtime

**Problema:** Al arrancar el backend para el QA visual, `/customers` devolvía 500.
La tabla `customers` en SQLite no tenía la columna `updated_at` (la DB se había
creado antes de que el schema la incluyera).

**Corrección:** `ALTER TABLE customers ADD COLUMN updated_at TEXT` + backfill desde `created_at`.

**Decisión:** Fix de datos, no de código.

---

### 4. Code review post-implementación — Senior Angular

Tras completar la implementación, lancé un `/review` específico para Angular moderno.
Hallazgos relevantes y decisiones tomadas:

#### ReactiveFormsModule importado sin usar (SimulationForm)
Los sliders no usan formGroup — usan eventos nativos + Signals.
`ReactiveFormsModule` estaba en `imports` por inercia.
→ **Eliminado.**

#### Métodos como `tier1Pct()` / `tier2Pct()` innecesariamente dinámicos
Calculaban `(10/200)*100 + '%'` = constante. Llamados en cada ciclo de CD.
→ **Convertidos a `readonly string` constantes.**

#### `currentPct()` dead code
Declarado pero nunca referenciado en el template.
→ **Eliminado.**

#### `lastSim()` método regular en vez de `computed()`
Derivaba de `simulations()` (Signal) pero era un método normal, inconsistente
con el patrón Signals del componente y recalculado en cada CD.
→ **Convertido a `computed()`.**

#### `<div (click)>` en filas de simulación
Un `<div>` con handler de click no es accesible por teclado ni semánticamente correcto.
→ **Cambiado a `<button type="button">` con `aria-expanded`.**

#### Error fiscal ID visible mientras se escribe
Los demás campos usan `fieldInvalid()` que comprueba `touched`. El fiscal ID
mostraba error desde el primer carácter porque usaba la señal directamente.
→ **Corregido: error solo visible tras `touched`.**

#### Route param guard
`Number(null)` = 0, lo que haría GET /customers/0. No había validación del param.
→ **Añadido guard: `if (!id) { router.navigate(['/']); return; }`**

#### Tipo `NIE_PREFIX`
`Record<string, string>` → `Record<'X' | 'Y' | 'Z', string>` para type safety.
Requirió cast en el punto de acceso (`fid[0] as 'X' | 'Y' | 'Z'`) ya que
la regex garantiza el valor pero TypeScript no puede inferirlo.
→ **Aplicado.**

#### aria-describedby en formulario
Los mensajes de error no estaban vinculados a sus inputs.
→ **Añadidos `id` a spans de error y `aria-describedby` en inputs.**

---

## Verificación final

```
ng build --configuration development → ✅ sin errores
npx vitest run → 22/22 tests ✅
Playwright screenshots → 4 vistas verificadas ✅
```

## Proceso de QA visual

Screenshots tomados con Playwright tras completar todos los componentes:
- `01-dashboard.png` — 5 clientes con datos seeded
- `02-customer-detail.png` — Acme Corp, primera simulación expandida con desglose de tramos
- `03-simulation-form.png` — slider en 65 usuarios, proyección 598.95€ (21% IVA ES)
- `04-customer-form-validation.png` — CIF inválido B83584469, error "debe ser el número '6'"

Los cálculos del simulador se verificaron manualmente:
- 65 usuarios: 10×10 + 40×8 + 15×5 = 100 + 320 + 75 = 495€ base + 21% = 598.95€ ✓

---

## Sesión 2 — Revisión visual en vivo + correcciones

### Contexto
Se revisó la app funcionando contra el documento original (`Prueba Devs con IA.docx`).
Se identificaron bugs reales, decisiones a corregir y mejoras de criterio técnico.

---

### Análisis de cada punto revisado

#### 1. Tabs locales de divisa — ELIMINADAS

**Problema:** `CustomerDetailComponent` y `SimulationFormComponent` tenían tabs
`['EUR','USD','GBP']` hardcodeadas que duplicaban el selector del navbar (7 divisas).
Si el usuario seleccionaba MXN en el navbar y navegaba al detalle, ninguna tab
quedaba activa — estado visual roto.

**Decisión:** Eliminar las tabs locales. El selector del navbar es el único punto
de control de divisa. Todos los componentes consumen `CurrencyService.currentCurrency()`
via Signal — el cambio propaga automáticamente.

**Eliminado:** `DISPLAY_CURRENCIES`, `displayCurrencies`, `setCurrency()`, import
`Currency` en ambos componentes. CSS muerto de `.currency-tabs` y `.currency-tab`.

---

#### 2. Stats del dashboard — CORREGIDOS

**Problema:** "Simulaciones guardadas" y "MRR simulado" mostraban `—`.
Dead code: `customers().reduce((acc, _) => acc + 0, 0)`.

**Decisión:** Añadir `GET /stats` en backend + llamar `getStats()` en `ngOnInit`.
El dashboard ahora muestra datos reales desde el primer render.

---

#### 3. Columna "Últ. Simulación" — CORREGIDA

**Problema:** Hardcodeada: `<span class="last-sim text-muted">—</span>`.

**Decisión:** Backend añade `last_simulation_at` via LEFT JOIN.
Frontend mapea el campo en `api.service.ts` y formatea con `toLocaleString('es-ES')`.

---

#### 4. Sliders de almacenamiento y llamadas API — ELIMINADOS

**Problema detectado al revisar el documento original:**

El documento pide en la Vista 3: *"Un slider o controles dinámicos para ajustar
**la cantidad de usuarios**"* — singular. Los sliders de storage y API calls no
estaban pedidos en la UI.

El spec derivado (`01-product-spec.md`) los añadió por extrapolar que si el
backend los recoge, el frontend debería configurarlos. Error de interpretación.

**Decisión:** Eliminar sliders de storage y API calls del formulario.
El backend sigue recibiendo `storage_gb: 1, api_calls: 0` como valores por defecto
— el contrato de la API no cambia.

**Justificación:** Tres sliders donde solo uno afecta al precio es confuso para el
equipo comercial. La UX correcta muestra solo los controles que tienen impacto real.

---

#### 5. Plan badge — MOVIDO al info grid

**Problema:** El badge de plan estaba en el header junto al nombre de empresa.
El info grid (ID Fiscal, Email, País, Últ. simulación) es donde deben estar
todos los metadatos del cliente.

**Decisión:** Mover badge al info grid como quinta celda.
Header queda más limpio. Grid usa `auto-fill minmax(180px, 1fr)` para 5 celdas.

---

#### 6. Input numérico para usuarios — AÑADIDO

**Motivación:** El slider topa en 200 usuarios. Un comercial simulando 500 o 1000
usuarios no puede usarlo. El documento no especifica límite superior.

**Decisión:** Slider (1–200) + input numérico sincronizados:
- Slider: ajuste rápido/visual con marcadores de tramo en 10 y 50
- Input: cualquier valor `>= 1` sin límite superior
- Sync: `sliderValue = computed(() => Math.min(activeUsers(), 200))`
- El cálculo usa siempre el valor real del signal, no el del slider

---

#### 7. Buscador — CAMBIADO a filtro local

**Problema:** El buscador hacía `GET /customers?q=` en cada búsqueda (con 300ms debounce).
Para una herramienta interna con decenas de clientes es innecesario.

**Decisión:** Cargar todos los clientes una vez en `ngOnInit`. Filtrar localmente:
```typescript
filteredCustomers = computed(() => {
  const q = this.searchQuery().toLowerCase().trim();
  if (!q) return this.customers();
  return this.customers().filter(c =>
    c.company.toLowerCase().includes(q) ||
    c.fiscalId.toLowerCase().includes(q)
  );
});
```

**Eliminado:** `Subject`, `debounceTime`, `distinctUntilChanged`, `switchMap`, `startWith`.
**Resultado:** Filtrado instantáneo, sin loading states, sin llamadas HTTP.

---

#### 8. Timeout y retry en API de tipos de cambio — AÑADIDOS

**Motivación:** El documento evalúa explícitamente *"manejo de estados de carga/error
al consumir la API externa"*. Si la API cuelga indefinidamente, la app queda bloqueada.

**Implementación:**
```typescript
.pipe(timeout(5000), retry(2))
```

Flujo: petición → si > 5s → timeout → reintento (hasta 2 veces) →
si falla → "⚠ EUR (sin conexión)" en navbar, app opera en EUR.

---

#### 9. Selector de divisa — MÁS VISIBLE en navbar

**Problema:** El botón era gris neutro (`--surface-raised`) — prácticamente invisible.
El navbar es el único punto de control de divisa. Debe ser identificable.

**Cambio:** Fondo `--accent-dim` (tinte amber 12%), borde amber 40%, texto amber
`font-weight: 700`. Hover: tinte más fuerte + borde completo.

---

#### 10. Fecha y hora en historial de simulaciones — AÑADIDAS

**Motivación:** Si un comercial hace varias simulaciones el mismo día, la fecha sola
no diferencia cuál es cuál. La hora añade contexto real sin coste de complejidad.

**Cambio:** `toLocaleDateString` → `toLocaleString` con `hour: '2-digit', minute: '2-digit'`.

---

### Decisiones conscientes de NO implementar

| Feature | Motivo |
|---|---|
| Edit/Delete clientes y simulaciones | No pedido en el documento |
| Caching de rutas (RouteReuseStrategy) | Over-engineering para este scope |
| State transfer entre rutas | Acoplamiento innecesario |
| Validación fiscal para países distintos de ES | Spec solo pide validación española |
| Tabla compartida como componente reutilizable | Dashboard y detalle tienen datos distintos; una sola instancia no justifica abstracción |
| Filtros en tabla de simulaciones | No pedido; volumen bajo en demo |

---

### Verificación final sesión 2

```
pytest -v → 94/94 tests ✅
ng build --configuration development → sin errores ✅
```
