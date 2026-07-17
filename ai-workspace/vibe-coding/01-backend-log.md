# Backend Log — Vibe Coding con IA

**Herramienta:** Claude Code (claude-sonnet-4-6)
**Rama:** feat/backend-setup (mergeado en master via PR #1)

---

## Sesión 1 — Implementación del API REST completa

### Contexto
Punto de partida: estructura base del repositorio y spec del producto.
Objetivo: API REST funcional con motor de facturación y validador fiscal.

### Prompt enviado a la IA
Spec estructurada con:
- Schema exacto de tablas SQLite (customers + simulations)
- Algoritmo de tramos acumulativo con casos de prueba obligatorios
- Algoritmo DNI/NIE/CIF con fuente oficial (AEAT/BOE)
- Contrato de errores: `{"detail": "...", "code": "SNAKE_CASE"}`
- Arquitectura de capas: routes → services → DB (sin ORM)
- Lista explícita de tests obligatorios

### Lo que generó la IA
1. `app/database.py` — init_db(), get_conn() con context manager
2. `app/models/schemas.py` — Pydantic v2: CustomerCreate, CustomerOut, SimulationCreate, SimulationOut
3. `app/services/billing.py` — calc_base_cost(), get_tier_breakdown()
4. `app/services/fiscal_validator.py` — validador DNI/NIE/CIF
5. `app/routes/customers.py` — GET/POST /customers, GET /customers/:id
6. `app/routes/simulations.py` — POST /simulations, GET /simulations/customer/:id
7. `main.py` — FastAPI app, CORS, logging middleware, seed data
8. `tests/` — 89 tests pytest

---

## Correcciones aplicadas durante el desarrollo

### 1. Schema de tablas definido desde el principio — SOLICITADO

**Decisión del usuario:** Pedir el schema completo de SQLite antes de generar código,
incluyendo columnas `created_at` y `updated_at` con defaults.

**Motivo:** Sin schema explícito la IA tiende a añadir columnas en iteraciones
posteriores, lo que rompe DBs ya inicializadas en desarrollo.

**Resultado:** Schema completo en `init_db()` desde el primer commit, con
`updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))`.

---

### 2. Datos de IVA consultados externamente — SOLICITADO

**Decisión del usuario:** No dejar que la IA tire de memoria para los tipos de IVA
por país — riesgo de alucinación en datos fiscales.

**Corrección:** Se especificó en el prompt que los tipos de IVA debían declararse
como constante explícita verificable:

```python
COUNTRY_TAX: dict[str, float] = {
    "ES": 0.21,
    "DE": 0.19,
    "FR": 0.20,
    "UK": 0.20,
    "MX": 0.16,
    "US": 0.00,
}
```

Los valores se verificaron contra fuentes oficiales antes de aceptar el código.

---

### 3. Lazy loading eliminado — SOLICITADO

**Decisión del usuario:** La IA propuso lazy loading de módulos de servicios
para optimizar el tiempo de arranque. Se rechazó por innecesario en este contexto
(app interna, < 10 usuarios concurrentes, arranque en milisegundos).

**Resultado:** Imports directos en todos los módulos. Código más legible y trazable.

---

### 4. Tests de validación fiscal — SOLICITADOS

**Decisión del usuario:** Pedir explícitamente tests para el validador fiscal,
no dejar que la IA decida qué cubrir.

**Tests generados y verificados:**
- DNI válido (`12345678Z`)
- DNI letra incorrecta (`12345678A` → error con sugerencia de letra correcta)
- NIE válido (`X1234567L`)
- CIF válido (`B83584466`)
- CIF inválido (`B83584469` — último dígito incorrecto)
- String sin formato reconocido
- Caso no-ES: cualquier fiscal_id pasa sin validación

---

### 5. Tests del algoritmo de tramos — SOLICITADOS

**Decisión del usuario:** Pedir cobertura exhaustiva de los casos límite del
algoritmo de tramos, incluyendo exactamente los valores de borde.

**Tests generados y verificados:**
```
10  usuarios → 100.00 € (exactamente tramo 1 lleno)
11  usuarios → 108.00 € (primer usuario en tramo 2)
50  usuarios → 420.00 € (tramo 2 lleno: 100 + 320)
51  usuarios → 425.00 € (primer usuario en tramo 3)
60  usuarios → 470.00 € (10 usuarios en tramo 3)
65  usuarios → 495.00 € (caso de referencia del spec)
200 usuarios → 1,000.00 € (techo del slider frontend)
```

Estos mismos valores se usaron para verificar el frontend (SimulationForm slider).

---

## Auditoría post-implementación — Review senior Python/FastAPI

Tras completar la implementación, se lanzó `/review` con perfil de senior developer
experto en Python, FastAPI y SQLite.

Resultado: **SHIP** — sin issues CRITICAL ni HIGH.

### Hallazgo MEDIUM corregido

#### Error contract incompleto en validación fiscal (customers.py:20)

**Problema detectado:** La ruta `POST /customers` lanzaba la excepción de fiscal
inválido con `detail=str(exc)` — una cadena plana. El contrato de error del
proyecto requiere `{"detail": "...", "code": "SNAKE_CASE"}` en todos los errores.
El frontend necesita el campo `code` para discriminar el tipo de error en el
interceptor HTTP.

**Código anterior:**
```python
except ValueError as exc:
    raise HTTPException(status_code=422, detail=str(exc))
```

**Corrección aplicada:**
```python
except ValueError as exc:
    raise HTTPException(
        status_code=422,
        detail={"detail": str(exc), "code": "FISCAL_ID_INVALID"},
    )
```

**Test actualizado** (`test_routes.py::test_es_invalid_fiscal_id_rejected`):
```python
# Antes:
assert "inválido" in res.json()["detail"]

# Después:
body = res.json()["detail"]
assert body["code"] == "FISCAL_ID_INVALID"
assert "inválido" in body["detail"]
```

**Resultado:** 89/89 tests passing tras la corrección.

---

## Verificación final

```
pytest -v → 89/89 tests ✅
ng build --configuration development → sin errores ✅
```

## Arquitectura resultante

```
backend/
├── app/
│   ├── database.py          # init_db(), get_conn() context manager
│   ├── models/
│   │   └── schemas.py       # Pydantic v2 schemas (Customer, Simulation)
│   ├── routes/
│   │   ├── customers.py     # GET+POST /customers, GET /customers/:id
│   │   └── simulations.py   # POST /simulations, GET /simulations/customer/:id
│   └── services/
│       ├── billing.py       # calc_base_cost(), get_tier_breakdown()
│       └── fiscal_validator.py  # validate_spanish_fiscal_id()
├── tests/                   # 89 tests pytest
│   ├── test_billing.py      # Algoritmo de tramos (casos límite)
│   ├── test_fiscal_validator.py  # DNI/NIE/CIF
│   ├── test_routes.py       # Integración /customers + /simulations
│   └── test_schemas.py      # Validación Pydantic
└── main.py                  # App, CORS, logging, seed data
```
