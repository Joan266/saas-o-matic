# Frontend Log — Vibe Coding con IA

**Herramienta:** Claude Code (claude-sonnet-4-6)
**Rama:** feat/angular-setup

---

## Sesión 1 — Implementación de las 3 vistas principales

### Contexto
El backend estaba completo (89 tests). La infraestructura del frontend (ApiService, CurrencyService,
ErrorInterceptor, billing.utils.ts, tipos, tokens de diseño) también estaba hecha.
Restaban 3 stubs vacíos + el validador fiscal en TypeScript.

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
