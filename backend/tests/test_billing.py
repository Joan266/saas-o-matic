"""
Tests for billing engine — tiered pricing + tax.
Edge cases from ai-workspace/specs/03-mock-data.md
"""

import pytest

from app.services.billing import calculate_base_cost, calculate_total, get_tax_rate


# ── Tiered pricing ────────────────────────────────────────────────────────────

class TestCalculateBaseCost:
    def test_single_user(self):
        assert calculate_base_cost(1) == 10.00

    def test_exactly_tier1_boundary(self):
        # 10 users — all in tier 1
        assert calculate_base_cost(10) == 100.00

    def test_one_into_tier2(self):
        # 11 users: 10×10 + 1×8 = 108
        assert calculate_base_cost(11) == 108.00

    def test_enunciado_example(self):
        # From the challenge doc: 15 users → 140€
        assert calculate_base_cost(15) == 140.00

    def test_exactly_tier2_boundary(self):
        # 50 users: 10×10 + 40×8 = 420
        assert calculate_base_cost(50) == 420.00

    def test_one_into_tier3(self):
        # 51 users: 10×10 + 40×8 + 1×5 = 425
        assert calculate_base_cost(51) == 425.00

    def test_tier3_example(self):
        # 60 users: 10×10 + 40×8 + 10×5 = 470
        assert calculate_base_cost(60) == 470.00

    def test_large_volume(self):
        # 200 users: 10×10 + 40×8 + 150×5 = 1170
        assert calculate_base_cost(200) == 1170.00

    def test_zero_users_raises(self):
        with pytest.raises(ValueError):
            calculate_base_cost(0)

    def test_negative_users_raises(self):
        with pytest.raises(ValueError):
            calculate_base_cost(-1)


# ── Tax rates ─────────────────────────────────────────────────────────────────

class TestGetTaxRate:
    @pytest.mark.parametrize("country,expected", [
        ("ES", 0.21),
        ("DE", 0.19),
        ("FR", 0.20),
        ("UK", 0.20),
        ("MX", 0.16),
        ("US", 0.00),
        ("JP", 0.00),   # unknown country → default 0
        ("",   0.00),   # empty → default 0
    ])
    def test_known_rates(self, country: str, expected: float):
        assert get_tax_rate(country) == expected

    def test_lowercase_country_accepted(self):
        assert get_tax_rate("es") == 0.21


# ── Total with tax ────────────────────────────────────────────────────────────

class TestCalculateTotal:
    def test_spain_21_percent(self):
        # 100€ base + 21% = 121€
        assert calculate_total(100.00, 0.21) == 121.00

    def test_usa_zero_tax(self):
        assert calculate_total(100.00, 0.00) == 100.00

    def test_rounding(self):
        # 140€ + 21% = 169.4€
        assert calculate_total(140.00, 0.21) == 169.40

    def test_full_flow_es_15_users(self):
        # Full flow: 15 users, ES customer
        base = calculate_base_cost(15)       # 140.00
        rate = get_tax_rate("ES")            # 0.21
        total = calculate_total(base, rate)  # 169.40
        assert base == 140.00
        assert total == 169.40
