import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.models.schemas import CustomerCreate, CustomerOut
from app.services import customers as customers_svc
from app.services.fiscal_validator import validate_spanish_fiscal_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate):
    if payload.country == "ES":
        try:
            validate_spanish_fiscal_id(payload.fiscal_id)
        except ValueError as exc:
            return JSONResponse(
                status_code=422,
                content={"detail": str(exc), "code": "FISCAL_ID_INVALID"},
            )

    if customers_svc.fiscal_id_exists(payload.fiscal_id):
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Este identificador fiscal ya está registrado.",
                "code": "DUPLICATE_FISCAL_ID",
            },
        )

    customer = customers_svc.create_customer(payload)
    logger.info("Customer created: id=%s company='%s'", customer.id, customer.company)
    return customer


@router.get("", response_model=list[CustomerOut])
def list_customers(q: str | None = None) -> list[CustomerOut]:
    return customers_svc.list_customers(q)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int):
    customer = customers_svc.get_customer_by_id(customer_id)
    if not customer:
        return JSONResponse(
            status_code=404,
            content={"detail": "Cliente no encontrado.", "code": "CUSTOMER_NOT_FOUND"},
        )
    return customer
