# SaaS-O-Matic

Herramienta interna para que el equipo comercial simule, optimice y presupueste suscripciones SaaS multi-divisa para clientes corporativos.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLite (sin ORM) |
| Frontend | Angular 21 · Standalone components · Signals |
| Tests backend | pytest (94 tests) |
| Tests frontend | Vitest (22 tests) |

---

## Arrancar en local

### Requisitos previos

- Python 3.12+
- Node.js 18+ y npm

### 1. Backend

```bash
cd backend
python -m venv venv

# Mac / Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

La API queda disponible en `http://localhost:8000`.
La documentación interactiva en `http://localhost:8000/docs`.

La base de datos SQLite (`saas_o_matic.db`) se crea automáticamente en el primer arranque
con datos de prueba (5 clientes y varias simulaciones).

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

La app queda disponible en `http://localhost:4200`.

> El frontend conecta con el backend en `http://localhost:8000` (configurado en
> `src/environments/environment.ts`). Asegúrate de que el backend esté arrancado.

---

## Tests

### Backend

```bash
cd backend
pytest -v
```

Cubre: algoritmo de tramos, validador fiscal (DNI/NIE/CIF), rutas REST, schemas.

### Frontend

```bash
cd frontend
npx vitest run
```

Cubre: `billing.utils.ts` (cálculo de tramos) y `fiscal-validator.utils.ts` (validación ES).

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/customers` | Listar clientes |
| `POST` | `/customers` | Crear cliente (valida DNI/NIE/CIF si país=ES) |
| `GET` | `/customers/:id` | Detalle de cliente |
| `GET` | `/simulations/customer/:id` | Historial de simulaciones |
| `POST` | `/simulations` | Crear simulación (calcula coste por tramos + IVA) |
| `GET` | `/stats` | KPIs globales: clientes, simulaciones, MRR |
| `GET` | `/health` | Health check |

---

## Algoritmo de facturación por tramos

Tarificación acumulativa (no precio único):

| Tramo | Usuarios | Precio/usuario |
|---|---|---|
| 1 | 1–10 | 10 € |
| 2 | 11–50 | 8 € |
| 3 | >50 | 5 € |

Ejemplo: 65 usuarios → 10×10 + 40×8 + 15×5 = **495 € base**

Al coste base se suma el IVA del país del cliente (ES: 21%, DE: 19%, FR/UK: 20%, MX: 16%, US: 0%).

---

## Estructura del repositorio

```
saas-o-matic/
├── backend/               # API REST FastAPI
│   ├── app/
│   │   ├── models/        # Pydantic schemas
│   │   ├── routes/        # Endpoints (customers, simulations, stats)
│   │   └── services/      # Lógica de negocio (billing, fiscal_validator)
│   ├── tests/             # 94 tests pytest
│   └── main.py
├── frontend/              # Angular 17 standalone
│   └── src/app/
│       ├── core/          # Services, interceptors, models
│       ├── features/      # Dashboard, CustomerDetail, CustomerForm, SimulationForm
│       └── shared/        # billing.utils, fiscal-validator.utils
└── ai-workspace/          # Proceso de ingeniería con IA
    ├── specs/             # Product spec y decisiones técnicas
    └── vibe-coding/       # Logs de desarrollo iterativo + screenshots
```
