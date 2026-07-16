"""
Tests for Pydantic schemas — input validation and field rules.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import CustomerCreate, SimulationCreate


# ── CustomerCreate ────────────────────────────────────────────────────────────

class TestCustomerCreate:
    def _valid(self, **overrides) -> dict:
        base = {
            "company": "Acme Corp SL",
            "fiscal_id": "B12345678",
            "email": "contact@acme.com",
            "country": "ES",
            "plan": "professional",
        }
        return {**base, **overrides}

    def test_happy_path(self):
        c = CustomerCreate(**self._valid())
        assert c.company == "Acme Corp SL"
        assert c.country == "ES"
        assert c.plan == "professional"

    def test_country_normalized_to_uppercase(self):
        c = CustomerCreate(**self._valid(country="es"))
        assert c.country == "ES"

    def test_plan_normalized_to_lowercase(self):
        c = CustomerCreate(**self._valid(plan="PROFESSIONAL"))
        assert c.plan == "professional"

    def test_plan_starter_valid(self):
        c = CustomerCreate(**self._valid(plan="starter"))
        assert c.plan == "starter"

    def test_plan_enterprise_valid(self):
        c = CustomerCreate(**self._valid(plan="enterprise"))
        assert c.plan == "enterprise"

    def test_invalid_plan_raises(self):
        with pytest.raises(ValidationError, match="Plan inválido"):
            CustomerCreate(**self._valid(plan="gold"))

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            CustomerCreate(**self._valid(email="not-an-email"))

    def test_empty_company_raises(self):
        with pytest.raises(ValidationError, match="vacío"):
            CustomerCreate(**self._valid(company="   "))

    def test_empty_fiscal_id_raises(self):
        with pytest.raises(ValidationError, match="vacío"):
            CustomerCreate(**self._valid(fiscal_id=""))

    def test_fiscal_id_normalized_to_uppercase(self):
        c = CustomerCreate(**self._valid(fiscal_id="b12345678"))
        assert c.fiscal_id == "B12345678"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            CustomerCreate(**self._valid(unknown_field="hack"))

    def test_special_characters_in_company(self):
        # Spanish/European characters must be accepted
        c = CustomerCreate(**self._valid(company="González & Asociados, S.L."))
        assert "González" in c.company

    def test_missing_required_field_raises(self):
        data = self._valid()
        del data["email"]
        with pytest.raises(ValidationError):
            CustomerCreate(**data)


# ── SimulationCreate ──────────────────────────────────────────────────────────

class TestSimulationCreate:
    def _valid(self, **overrides) -> dict:
        base = {
            "customer_id": 1,
            "active_users": 15,
            "storage_gb": 100,
            "api_calls": 50000,
        }
        return {**base, **overrides}

    def test_happy_path(self):
        s = SimulationCreate(**self._valid())
        assert s.active_users == 15
        assert s.api_calls == 50000

    def test_zero_active_users_raises(self):
        with pytest.raises(ValidationError, match="active_users"):
            SimulationCreate(**self._valid(active_users=0))

    def test_negative_active_users_raises(self):
        with pytest.raises(ValidationError):
            SimulationCreate(**self._valid(active_users=-1))

    def test_zero_storage_raises(self):
        with pytest.raises(ValidationError, match="storage_gb"):
            SimulationCreate(**self._valid(storage_gb=0))

    def test_negative_api_calls_raises(self):
        with pytest.raises(ValidationError, match="api_calls"):
            SimulationCreate(**self._valid(api_calls=-1))

    def test_zero_api_calls_valid(self):
        # api_calls >= 0, so 0 is valid
        s = SimulationCreate(**self._valid(api_calls=0))
        assert s.api_calls == 0

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            SimulationCreate(**self._valid(injected="malicious"))

    def test_missing_customer_id_raises(self):
        data = self._valid()
        del data["customer_id"]
        with pytest.raises(ValidationError):
            SimulationCreate(**data)
