from pydantic import BaseModel, EmailStr, field_validator, model_validator, ConfigDict

VALID_PLANS = {"starter", "professional", "enterprise"}


# ── Customer ──────────────────────────────────────────────────────────────────


class CustomerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str
    fiscal_id: str
    email: EmailStr
    country: str
    plan: str

    @field_validator("company")
    @classmethod
    def company_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre de empresa no puede estar vacío.")
        return v

    @field_validator("country")
    @classmethod
    def country_uppercase(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("fiscal_id")
    @classmethod
    def fiscal_id_not_empty(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("El identificador fiscal no puede estar vacío.")
        return v

    @field_validator("plan")
    @classmethod
    def plan_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in VALID_PLANS:
            raise ValueError(f"Plan inválido. Opciones: {sorted(VALID_PLANS)}")
        return v


class CustomerOut(BaseModel):
    id: int
    company: str
    fiscal_id: str
    email: str
    country: str
    plan: str
    created_at: str
    updated_at: str
    last_simulation_at: str | None = None


# ── Simulation ────────────────────────────────────────────────────────────────


class SimulationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: int
    active_users: int
    storage_gb: int
    api_calls: int

    @model_validator(mode="after")
    def values_are_positive(self) -> "SimulationCreate":
        errors = []
        if self.active_users < 1:
            errors.append("active_users debe ser >= 1.")
        if self.storage_gb < 1:
            errors.append("storage_gb debe ser >= 1.")
        if self.api_calls < 0:
            errors.append("api_calls debe ser >= 0.")
        if errors:
            raise ValueError(" ".join(errors))
        return self


class SimulationOut(BaseModel):
    id: int
    customer_id: int
    active_users: int
    storage_gb: int
    api_calls: int
    base_cost: float
    tax_rate: float
    total_cost: float
    created_at: str


# ── Stats ─────────────────────────────────────────────────────────────────────


class StatsOut(BaseModel):
    total_customers: int
    total_simulations: int
    total_mrr: float
