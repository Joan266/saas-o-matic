from app.database import get_conn
from app.models.schemas import SimulationOut


def get_customer_country(customer_id: int) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT country FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
    return row["country"] if row else None


def create_simulation(
    customer_id: int,
    active_users: int,
    storage_gb: int,
    api_calls: int,
    base_cost: float,
    tax_rate: float,
    total_cost: float,
) -> SimulationOut:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO simulations
                (customer_id, active_users, storage_gb, api_calls,
                 base_cost, tax_rate, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                active_users,
                storage_gb,
                api_calls,
                base_cost,
                tax_rate,
                total_cost,
            ),
        )
        row = conn.execute(
            "SELECT * FROM simulations WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return SimulationOut(**dict(row))


def get_simulations_for_customer(customer_id: int) -> list[SimulationOut] | None:
    """Return simulations ordered newest-first, or None if customer doesn't exist."""
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
        if not exists:
            return None
        rows = conn.execute(
            """
            SELECT * FROM simulations
            WHERE customer_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (customer_id,),
        ).fetchall()
    return [SimulationOut(**dict(r)) for r in rows]
