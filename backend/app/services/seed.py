"""
Seed script — inserts demo data if the DB is empty.
Only runs on startup, safe to call multiple times.
"""

import logging

from app.database import get_conn

logger = logging.getLogger(__name__)

_CUSTOMERS = [
    ("Acme Corp SL", "A28000727", "contact@acme.com", "ES", "enterprise"),
    ("TechGmbH", "DE123456", "info@techgmbh.de", "DE", "professional"),
    ("Startup Inc", "US-TAX-001", "hello@startup.io", "US", "starter"),
    ("Renault France SA", "FR-456789", "billing@renault.fr", "FR", "professional"),
    ("González & Asociados", "12345678Z", "info@gonzalez.es", "ES", "starter"),
]

_SIMULATIONS = [
    # (company fiscal_id, active_users, storage_gb, api_calls)
    ("A28000727", 5, 50, 10_000),
    ("A28000727", 15, 100, 50_000),
    ("A28000727", 50, 500, 200_000),
    ("A28000727", 75, 1000, 1_000_000),
    ("DE123456", 20, 200, 75_000),
    ("US-TAX-001", 8, 30, 5_000),
]


def seed_if_empty() -> None:
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        if count > 0:
            return

        for company, fiscal_id, email, country, plan in _CUSTOMERS:
            conn.execute(
                """
                INSERT INTO customers (company, fiscal_id, email, country, plan)
                VALUES (?, ?, ?, ?, ?)
                """,
                (company, fiscal_id, email, country, plan),
            )

    logger.info("Seed: %d demo customers inserted", len(_CUSTOMERS))
    _seed_simulations()


def _seed_simulations() -> None:
    from app.services.billing import calculate_base_cost, calculate_total, get_tax_rate

    with get_conn() as conn:
        for fiscal_id, users, storage, api_calls in _SIMULATIONS:
            customer = conn.execute(
                "SELECT id, country FROM customers WHERE fiscal_id = ?",
                (fiscal_id,),
            ).fetchone()

            if not customer:
                logger.warning(
                    "Seed: customer with fiscal_id=%s not found, skipping", fiscal_id
                )
                continue

            base_cost = calculate_base_cost(users)
            tax_rate = get_tax_rate(customer["country"])
            total_cost = calculate_total(base_cost, tax_rate)

            conn.execute(
                """
                INSERT INTO simulations
                    (customer_id, active_users, storage_gb, api_calls,
                     base_cost, tax_rate, total_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer["id"],
                    users,
                    storage,
                    api_calls,
                    base_cost,
                    tax_rate,
                    total_cost,
                ),
            )

    logger.info("Seed: %d demo simulations inserted", len(_SIMULATIONS))
