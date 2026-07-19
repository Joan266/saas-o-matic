from app.database import get_conn
from app.models.schemas import StatsOut


def get_stats() -> StatsOut:
    with get_conn() as conn:
        total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        total_simulations = conn.execute("SELECT COUNT(*) FROM simulations").fetchone()[
            0
        ]
        # MRR = sum of most recent simulation per customer (latest by id)
        mrr_row = conn.execute(
            """
            SELECT COALESCE(SUM(s.total_cost), 0)
            FROM simulations s
            INNER JOIN (
                SELECT customer_id, MAX(id) AS max_id FROM simulations GROUP BY customer_id
            ) latest ON s.id = latest.max_id
            """
        ).fetchone()
    return StatsOut(
        total_customers=total_customers,
        total_simulations=total_simulations,
        total_mrr=float(mrr_row[0]),
    )
