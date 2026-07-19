import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.schemas import SimulationCreate, SimulationOut
from app.services import simulations as simulations_svc
from app.services.billing import calculate_base_cost, calculate_total, get_tax_rate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["simulations"])


@router.post("", response_model=SimulationOut, status_code=201)
def create_simulation(payload: SimulationCreate):
    country = simulations_svc.get_customer_country(payload.customer_id)
    if country is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente no encontrado.", "code": "CUSTOMER_NOT_FOUND"},
        )

    base_cost = calculate_base_cost(payload.active_users)
    tax_rate = get_tax_rate(country)
    total_cost = calculate_total(base_cost, tax_rate)

    sim = simulations_svc.create_simulation(
        customer_id=payload.customer_id,
        active_users=payload.active_users,
        storage_gb=payload.storage_gb,
        api_calls=payload.api_calls,
        base_cost=base_cost,
        tax_rate=tax_rate,
        total_cost=total_cost,
    )
    logger.info(
        "Simulation created: id=%s customer_id=%s users=%s total=%.2f",
        sim.id,
        sim.customer_id,
        sim.active_users,
        sim.total_cost,
    )
    return sim


@router.get("/customer/{customer_id}", response_model=list[SimulationOut])
def get_customer_simulations(customer_id: int):
    result = simulations_svc.get_simulations_for_customer(customer_id)
    if result is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente no encontrado.", "code": "CUSTOMER_NOT_FOUND"},
        )
    return result
