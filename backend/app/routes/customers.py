import logging

from fastapi import APIRouter, HTTPException

from app.database import get_conn
from app.models.schemas import CustomerCreate, CustomerOut
from app.services.fiscal_validator import validate_spanish_fiscal_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerCreate) -> CustomerOut:
    if payload.country == "ES":
        try:
            validate_spanish_fiscal_id(payload.fiscal_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"detail": str(exc), "code": "FISCAL_ID_INVALID"},
            )

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM customers WHERE fiscal_id = ?",
            (payload.fiscal_id,),
        ).fetchone()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Este identificador fiscal ya está registrado.",
            )

        cursor = conn.execute(
            """
            INSERT INTO customers (company, fiscal_id, email, country, plan)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.company,
                payload.fiscal_id,
                payload.email,
                payload.country,
                payload.plan,
            ),
        )
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    logger.info("Customer created: id=%s company='%s'", row["id"], row["company"])
    return CustomerOut(**dict(row))


@router.get("", response_model=list[CustomerOut])
def list_customers(q: str | None = None) -> list[CustomerOut]:
    with get_conn() as conn:
        if q:
            rows = conn.execute(
                """
                SELECT c.*, MAX(s.created_at) AS last_simulation_at
                FROM customers c
                LEFT JOIN simulations s ON s.customer_id = c.id
                WHERE c.company LIKE ? OR c.fiscal_id LIKE ?
                GROUP BY c.id
                ORDER BY c.created_at DESC, c.id DESC
                """,
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT c.*, MAX(s.created_at) AS last_simulation_at
                FROM customers c
                LEFT JOIN simulations s ON s.customer_id = c.id
                GROUP BY c.id
                ORDER BY c.created_at DESC, c.id DESC
                """
            ).fetchall()

    return [CustomerOut(**dict(r)) for r in rows]


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int) -> CustomerOut:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    return CustomerOut(**dict(row))
