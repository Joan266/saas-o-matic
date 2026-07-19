import logging

from app.database import get_conn
from app.models.schemas import CustomerCreate, CustomerOut

logger = logging.getLogger(__name__)


def fiscal_id_exists(fiscal_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM customers WHERE fiscal_id = ?",
            (fiscal_id,),
        ).fetchone()
    return row is not None


def create_customer(payload: CustomerCreate) -> CustomerOut:
    with get_conn() as conn:
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
    return CustomerOut(**dict(row))


def list_customers(q: str | None) -> list[CustomerOut]:
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


def get_customer_by_id(customer_id: int) -> CustomerOut | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
    if not row:
        return None
    return CustomerOut(**dict(row))
