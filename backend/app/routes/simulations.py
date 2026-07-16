import logging

from fastapi import APIRouter, HTTPException

from app.database import get_conn
from app.models.schemas import SimulationCreate, SimulationOut
from app.services.billing import calculate_base_cost, calculate_total, get_tax_rate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SimulationOut, status_code=201)
def create_simulation(payload: SimulationCreate) -> SimulationOut:
    with get_conn() as conn:
        customer = conn.execute(
            "SELECT country FROM customers WHERE id = ?",
            (payload.customer_id,),
        ).fetchone()

    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    base_cost = calculate_base_cost(payload.active_users)
    tax_rate = get_tax_rate(customer["country"])
    total_cost = calculate_total(base_cost, tax_rate)

    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO simulations
                (customer_id, active_users, storage_gb, api_calls,
                 base_cost, tax_rate, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (payload.customer_id, payload.active_users, payload.storage_gb,
             payload.api_calls, base_cost, tax_rate, total_cost),
        )
        row = conn.execute(
            "SELECT * FROM simulations WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    logger.info(
        "Simulation created: id=%s customer_id=%s users=%s total=%.2f",
        row["id"], row["customer_id"], row["active_users"], row["total_cost"],
    )
    return SimulationOut(**dict(row))


@router.get("/customer/{customer_id}", response_model=list[SimulationOut])
def get_customer_simulations(customer_id: int) -> list[SimulationOut]:
    with get_conn() as conn:
        customer = conn.execute(
            "SELECT id FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()

        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado.")

        rows = conn.execute(
            """
            SELECT * FROM simulations
            WHERE customer_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()

    return [SimulationOut(**dict(r)) for r in rows]
