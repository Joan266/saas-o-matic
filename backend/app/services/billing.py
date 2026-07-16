"""
Billing engine — tiered pricing + tax calculation.

Tiers (cumulative/acumulativo):
  users  1–10  →  10 €/user
  users 11–50  →   8 €/user
  users  >50   →   5 €/user

Tax rates by country (standard VAT 2026, verified from official sources):
  ES 21% | DE 19% | FR 20% | UK 20% | MX 16% | US 0% | default 0%
"""

_TIERS: list[tuple[int | None, float]] = [
    (10, 10.0),   # first 10 users at 10 €
    (40, 8.0),    # next 40 users (11–50) at 8 €
    (None, 5.0),  # remainder at 5 €
]

_COUNTRY_TAX: dict[str, float] = {
    "ES": 0.21,
    "DE": 0.19,
    "FR": 0.20,
    "UK": 0.20,
    "MX": 0.16,
    "US": 0.00,
}


def calculate_base_cost(active_users: int) -> float:
    """Return cumulative tiered cost in EUR, before tax."""
    if active_users < 1:
        raise ValueError("active_users must be >= 1")

    cost = 0.0
    remaining = active_users

    for cap, rate in _TIERS:
        if remaining <= 0:
            break
        chunk = min(remaining, cap) if cap is not None else remaining
        cost += chunk * rate
        remaining -= chunk

    return round(cost, 2)


def get_tax_rate(country: str) -> float:
    """Return VAT rate for a given ISO-2 country code. Defaults to 0.0."""
    return _COUNTRY_TAX.get(country.upper(), 0.0)


def calculate_total(base_cost: float, tax_rate: float) -> float:
    """Return base_cost with tax applied, rounded to 2 decimal places."""
    return round(base_cost * (1 + tax_rate), 2)
