# SaaS-O-Matic — Product Spec

## 1. Qué es y para quién

Herramienta interna para el equipo comercial. Permite registrar clientes corporativos y
simular cuánto les costaría una suscripción SaaS según sus parámetros de uso
(usuarios, almacenamiento, llamadas API), con conversión de divisa en tiempo real.

No requiere autenticación. Es una herramienta de uso interno.

---

## 2. Entidades de datos

### Customer
| Campo      | Tipo   | Reglas                                              |
|------------|--------|-----------------------------------------------------|
| id         | int    | PK autoincremental                                  |
| company    | string | Requerido                                           |
| fiscal_id  | string | Requerido, único. Si país=ES → validar DNI/NIE/CIF  |
| email      | string | Formato email válido                                |
| country    | string | Código ISO 2 letras (ES, DE, FR, US…)               |
| plan       | string | Enum: starter / professional / enterprise           |
| created_at | string | datetime UTC, generado por DB                       |

### Simulation
| Campo       | Tipo  | Reglas                                    |
|-------------|-------|-------------------------------------------|
| id          | int   | PK autoincremental                        |
| customer_id | int   | FK → Customer                             |
| active_users| int   | >= 1                                      |
| storage_gb  | int   | >= 1                                      |
| api_calls   | int   | >= 0                                      |
| base_cost   | float | Calculado por el backend (tramos)         |
| tax_rate    | float | Según país del cliente                    |
| total_cost  | float | base_cost × (1 + tax_rate)                |
| created_at  | string| datetime UTC, generado por DB             |

---

## 3. Reglas de negocio

### 3.1 Algoritmo de tarificación por tramos (Tiered Pricing)

El coste base se calcula de forma **acumulativa**:

```
Tramo 1: usuarios  1–10  → 10 €/usuario
Tramo 2: usuarios 11–50  →  8 €/usuario
Tramo 3: usuarios  >50   →  5 €/usuario
```

**Ejemplo con 15 usuarios:**
- Tramo 1: 10 usuarios × 10€ = 100€
- Tramo 2:  5 usuarios ×  8€ =  40€
- **Total base: 140€**

**Ejemplo con 60 usuarios:**
- Tramo 1: 10 × 10€ = 100€
- Tramo 2: 40 ×  8€ = 320€
- Tramo 3: 10 ×  5€ =  50€
- **Total base: 470€**

### 3.2 IVA por país

| País | Código | IVA   |
|------|--------|-------|
| España      | ES | 21%  |
| Alemania    | DE | 19%  |
| Francia     | FR | 20%  |
| Reino Unido | UK | 20%  |
| México      | MX | 16%  |
| USA         | US |  0%  |
| Resto       | — |   0%  |

**Total con IVA:** `total_cost = base_cost × (1 + tax_rate)`

### 3.3 Validación fiscal española (solo si country = "ES")

Se debe validar el `fiscal_id` usando el algoritmo oficial. Tres tipos posibles:

**DNI** — formato `12345678Z`
- 8 dígitos + 1 letra
- Letra = `"TRWAGMYFPDXBNJZSQVHLCKE"[ numero % 23 ]`

**NIE** — formato `X1234567Z`
- Empieza por X, Y o Z (se sustituye por 0, 1, 2 respectivamente)
- Resto igual que DNI

**CIF** — formato `B12345678`
- Primera letra = tipo de organización
- 7 dígitos centrales (posiciones 1–7)
- Posiciones **impares** (1,3,5,7) → multiplicar por 2, sumar las cifras del resultado
- Posiciones **pares** (2,4,6) → sumar directamente
- Total = suma_impares + suma_pares
- control_digit = (10 - (total % 10)) % 10
- control_letra = "JABCDEFGHI"[control_digit]  (0→J, 1→A, ... 9→I)
- Tipo de org determina si el control es dígito, letra, o cualquiera de los dos

Si el identificador no pasa la validación → error 422 con mensaje descriptivo.
Si el país no es ES → se acepta cualquier string en fiscal_id (sin validar).

### 3.4 Conversión de divisa

- Se consume `https://open.er-api.com/v6/latest/EUR` al cargar el frontend
- El usuario puede cambiar la divisa desde un selector (EUR, USD, GBP, MXN, JPY, CHF, CAD)
- Todos los costes en pantalla se recalculan en tiempo real sin llamar al backend
- El backend siempre guarda y devuelve los valores **en EUR**

---

## 4. Contrato de la API (Backend)

### POST /customers
Registra un nuevo cliente.

**Body:**
```json
{
  "company": "Acme Corp",
  "fiscal_id": "12345678Z",
  "email": "contact@acme.com",
  "country": "ES",
  "plan": "professional"
}
```

**Respuestas:**
- `201` — Cliente creado (devuelve objeto Customer completo)
- `409` — fiscal_id duplicado
- `422` — validación fallida (fiscal ID inválido, email malformado, plan desconocido)

---

### GET /customers
Lista todos los clientes. Soporta búsqueda opcional.

**Query params:** `?q=texto` — filtra por company o fiscal_id (LIKE)

**Respuesta 200:**
```json
[{ "id": 1, "company": "Acme Corp", ... }]
```

---

### GET /customers/:id
Devuelve un cliente por ID.

**Respuestas:**
- `200` — Objeto Customer
- `404` — No encontrado

---

### POST /simulations
Registra una simulación y calcula coste.

**Body:**
```json
{
  "customer_id": 1,
  "active_users": 15,
  "storage_gb": 100,
  "api_calls": 50000
}
```

**Respuestas:**
- `201` — Simulación guardada con costes calculados
- `404` — customer_id no existe
- `422` — valores negativos

---

### GET /simulations/customer/:id
Devuelve el historial de simulaciones de un cliente, orden desc por fecha.

**Respuesta 200:**
```json
[{ "id": 1, "customer_id": 1, "active_users": 15, "base_cost": 140.0, ... }]
```

---

## 5. Vistas del frontend (Angular)

### Vista 1 — Dashboard
- Buscador en tiempo real (filtra al escribir, llama a `GET /customers?q=`)
- Listado de clientes en cards o tabla
- Botón "Nuevo cliente" → abre formulario (modal o página nueva)
- Selector de divisa visible en el header (aplica a toda la app)

### Vista 2 — Detalle del cliente
- Card con todos los datos del cliente
- Tabla de simulaciones históricas con costes convertidos a divisa seleccionada
- Botón "Nueva simulación"

### Vista 3 — Formulario de simulación
- Slider para usuarios activos (1–200)
- Slider para storage GB (1–1000)
- Slider para API calls (1.000–1.000.000)
- Preview en tiempo real del coste base (calculado en frontend con la misma lógica de tramos)
- Al guardar → llama a `POST /simulations` y refresca el historial

### Vista 4 — Formulario de nuevo cliente
- Campos: empresa, fiscal_id, email, país (select), plan (select)
- Si país = ES → el backend devolverá 422 si el ID es inválido, mostrar mensaje claro
- Al guardar exitosamente → redirigir al detalle del cliente

---

## 6. Stack técnico

| Capa       | Tecnología                                      |
|------------|-------------------------------------------------|
| Backend    | Python 3.12 + FastAPI                           |
| Base datos | SQLite (archivo local, sin ORM)                 |
| Frontend   | Angular 22 (standalone, selectorless, Signals)  |
| HTTP       | HttpClient / httpResource() de Angular          |
| Estilos    | Angular Material                                |
| Estado     | Angular Signals                                 |
| Divisa API | open.er-api.com (pública, sin key, caché 24h)   |

---

## 7. Estructura de carpetas

### Backend
```
backend/
├── main.py                  # Entry point FastAPI, CORS, startup
├── requirements.txt
├── saas_o_matic.db          # Generado en runtime
└── app/
    ├── database.py          # Conexión SQLite, init_db(), get_conn()
    ├── models/
    │   └── schemas.py       # Pydantic models: CustomerCreate, SimulationCreate, *Out
    ├── services/
    │   ├── billing.py       # calculate_base_cost(), get_tax_rate(), calculate_total()
    │   └── fiscal_validator.py  # validate_spanish_fiscal_id() → DNI/NIE/CIF
    └── routes/
        ├── customers.py     # POST /customers, GET /customers, GET /customers/:id
        └── simulations.py   # POST /simulations, GET /simulations/customer/:id
```

Regla: las rutas nunca acceden a la DB directamente. Los servicios nunca importan FastAPI.

### Frontend
```
frontend/
└── src/
    └── app/
        ├── core/
        │   └── services/
        │       ├── api.service.ts        # HttpClient wrapper (customers + simulations)
        │       └── currency.service.ts   # Signal: currentCurrency, rates, convert()
        ├── features/
        │   ├── customers/
        │   │   ├── dashboard/            # Vista 1: buscador + listado
        │   │   ├── customer-detail/      # Vista 2: card + historial simulaciones
        │   │   └── customer-form/        # Vista 4: formulario alta cliente
        │   └── simulations/
        │       └── simulation-form/      # Vista 3: sliders + preview en tiempo real
        └── shared/
            ├── utils/
            │   └── billing.utils.ts      # calcBaseCost() — misma lógica de tramos que backend
            └── components/
                └── currency-selector/    # Selector divisa reutilizable (header)
```

---

## 8. Decisiones de diseño clave

### Estado de divisa con Signals
`CurrencyService` es el único dueño del estado de divisa. Todos los componentes que
muestran precios lo inyectan y usan `convert(eurAmount)`:

```typescript
// currency.service.ts
currentCurrency = signal('EUR');
rates = signal<Record<string, number>>({});

convert(eur: number): string {
  const rate = this.rates()[this.currentCurrency()] ?? 1;
  return (eur * rate).toFixed(2);
}
```

### Lógica de tramos duplicada en frontend
El preview del slider debe ser instantáneo (sin llamadas al backend).
`billing.utils.ts` implementa `calcBaseCost(users: number): number` con
la misma lógica acumulativa que `services/billing.py`.

### Backend siempre en EUR
El backend calcula y persiste `base_cost` y `total_cost` en EUR siempre.
La conversión de divisa es responsabilidad exclusiva del frontend.

### Sin ORM
Queries SQL directas con sqlite3 y parámetros posicionales (`?`).
Evita complejidad innecesaria para el scope del proyecto.

---

## 9. Rutas Angular

| Ruta                       | Componente             | Descripción                        |
|----------------------------|------------------------|------------------------------------|
| `/`                        | DashboardComponent     | Buscador + listado de clientes     |
| `/customers/new`           | CustomerFormComponent  | Formulario alta de cliente         |
| `/customers/:id`           | CustomerDetailComponent| Card + historial de simulaciones   |
| `/customers/:id/simulate`  | SimulationFormComponent| Sliders + preview coste en tiempo real |

Navegación:
- Dashboard → click en cliente → `/customers/:id`
- Dashboard → "Nuevo cliente" → `/customers/new`
- CustomerDetail → "Nueva simulación" → `/customers/:id/simulate`
- Tras guardar cliente nuevo → redirigir a `/customers/:id`
- Tras guardar simulación → redirigir a `/customers/:id`

---

## 10. Dependencies

### Backend (`requirements.txt`)
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic[email]==2.8.2
slowapi==0.1.9
pytest==8.3.0
pytest-benchmark==4.0.0
httpx==0.27.0          # para TestClient de FastAPI
```

### Frontend
```
@angular/core: ^22.0.0
@angular/material: ^22.0.0
```

---

## 11. Mock data para demo

Insertar al arrancar si la DB está vacía:

| Empresa       | Fiscal ID  | País | Plan          |
|---------------|------------|------|---------------|
| Acme Corp SL  | B83584469  | ES   | enterprise    |
| TechGmbH      | DE123456   | DE   | professional  |
| Startup Inc   | US-001     | US   | starter       |
| Renault France| FR-456     | FR   | professional  |
