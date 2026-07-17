"""
Integration tests for /customers and /simulations endpoints.
Uses a temporary SQLite DB to avoid polluting the dev database.
"""

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
import app.database as db_module


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redirect DB to a temp file and re-initialize for each test."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    init_db()
    yield


@pytest.fixture
def client(temp_db):
    from main import app

    return TestClient(app)


@pytest.fixture
def es_customer(client):
    """Create and return a valid Spanish customer."""
    res = client.post(
        "/customers",
        json={
            "company": "Acme Corp SL",
            "fiscal_id": "A28000727",
            "email": "contact@acme.com",
            "country": "ES",
            "plan": "enterprise",
        },
    )
    assert res.status_code == 201
    return res.json()


# ── POST /customers ───────────────────────────────────────────────────────────


class TestCreateCustomer:
    def test_happy_path_non_es(self, client):
        res = client.post(
            "/customers",
            json={
                "company": "TechGmbH",
                "fiscal_id": "DE123456",
                "email": "info@techgmbh.de",
                "country": "DE",
                "plan": "professional",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["company"] == "TechGmbH"
        assert data["country"] == "DE"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_happy_path_es_valid_cif(self, client):
        res = client.post(
            "/customers",
            json={
                "company": "Acme Corp SL",
                "fiscal_id": "A28000727",
                "email": "contact@acme.com",
                "country": "ES",
                "plan": "enterprise",
            },
        )
        assert res.status_code == 201

    def test_es_invalid_fiscal_id_rejected(self, client):
        res = client.post(
            "/customers",
            json={
                "company": "Fake Corp",
                "fiscal_id": "B83584469",
                "email": "fake@fake.com",
                "country": "ES",
                "plan": "starter",
            },
        )
        assert res.status_code == 422
        body = res.json()["detail"]
        assert body["code"] == "FISCAL_ID_INVALID"
        assert "inválido" in body["detail"]

    def test_invalid_fiscal_id_non_es_accepted(self, client):
        # Non-ES countries skip fiscal validation
        res = client.post(
            "/customers",
            json={
                "company": "Startup Inc",
                "fiscal_id": "ANYTHING-GOES",
                "email": "hello@startup.com",
                "country": "US",
                "plan": "starter",
            },
        )
        assert res.status_code == 201

    def test_duplicate_fiscal_id_returns_409(self, client, es_customer):
        res = client.post(
            "/customers",
            json={
                "company": "Other Corp",
                "fiscal_id": "A28000727",  # same as es_customer
                "email": "other@corp.com",
                "country": "DE",
                "plan": "starter",
            },
        )
        assert res.status_code == 409

    def test_invalid_email_returns_422(self, client):
        res = client.post(
            "/customers",
            json={
                "company": "Bad Corp",
                "fiscal_id": "DE999",
                "email": "not-an-email",
                "country": "DE",
                "plan": "starter",
            },
        )
        assert res.status_code == 422

    def test_invalid_plan_returns_422(self, client):
        res = client.post(
            "/customers",
            json={
                "company": "Bad Corp",
                "fiscal_id": "DE999",
                "email": "ok@corp.com",
                "country": "DE",
                "plan": "gold",
            },
        )
        assert res.status_code == 422

    def test_extra_fields_rejected(self, client):
        res = client.post(
            "/customers",
            json={
                "company": "Bad Corp",
                "fiscal_id": "DE999",
                "email": "ok@corp.com",
                "country": "DE",
                "plan": "starter",
                "hacked": "value",
            },
        )
        assert res.status_code == 422


# ── GET /customers ────────────────────────────────────────────────────────────


class TestListCustomers:
    def test_empty_list(self, client):
        res = client.get("/customers")
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_created_customers(self, client, es_customer):
        res = client.get("/customers")
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_search_by_company(self, client, es_customer):
        res = client.get("/customers?q=Acme")
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_search_by_fiscal_id(self, client, es_customer):
        res = client.get("/customers?q=A28000727")
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_search_no_results(self, client, es_customer):
        res = client.get("/customers?q=ZZZNOTFOUND")
        assert res.status_code == 200
        assert res.json() == []


# ── GET /customers/:id ────────────────────────────────────────────────────────


class TestGetCustomer:
    def test_happy_path(self, client, es_customer):
        res = client.get(f"/customers/{es_customer['id']}")
        assert res.status_code == 200
        assert res.json()["fiscal_id"] == "A28000727"

    def test_not_found_returns_404(self, client):
        res = client.get("/customers/9999")
        assert res.status_code == 404


# ── POST /simulations ─────────────────────────────────────────────────────────


class TestCreateSimulation:
    def test_happy_path_es_21_vat(self, client, es_customer):
        res = client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 15,
                "storage_gb": 100,
                "api_calls": 50000,
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["base_cost"] == 140.00
        assert data["tax_rate"] == 0.21
        assert data["total_cost"] == 169.40

    def test_customer_not_found_returns_404(self, client):
        res = client.post(
            "/simulations",
            json={
                "customer_id": 9999,
                "active_users": 10,
                "storage_gb": 50,
                "api_calls": 1000,
            },
        )
        assert res.status_code == 404

    def test_zero_users_returns_422(self, client, es_customer):
        res = client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 0,
                "storage_gb": 50,
                "api_calls": 1000,
            },
        )
        assert res.status_code == 422

    def test_negative_storage_returns_422(self, client, es_customer):
        res = client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 10,
                "storage_gb": -1,
                "api_calls": 1000,
            },
        )
        assert res.status_code == 422


# ── GET /simulations/customer/:id ─────────────────────────────────────────────


class TestGetCustomerSimulations:
    def test_empty_history(self, client, es_customer):
        res = client.get(f"/simulations/customer/{es_customer['id']}")
        assert res.status_code == 200
        assert res.json() == []

    def test_returns_simulations_ordered_desc(self, client, es_customer):
        cid = es_customer["id"]
        client.post(
            "/simulations",
            json={
                "customer_id": cid,
                "active_users": 10,
                "storage_gb": 50,
                "api_calls": 1000,
            },
        )
        client.post(
            "/simulations",
            json={
                "customer_id": cid,
                "active_users": 50,
                "storage_gb": 200,
                "api_calls": 5000,
            },
        )
        res = client.get(f"/simulations/customer/{cid}")
        assert res.status_code == 200
        sims = res.json()
        assert len(sims) == 2
        # Most recent first
        assert sims[0]["active_users"] == 50

    def test_customer_not_found_returns_404(self, client):
        res = client.get("/simulations/customer/9999")
        assert res.status_code == 404


# ── GET /stats ────────────────────────────────────────────────────────────────


class TestGetStats:
    def test_empty_db(self, client):
        res = client.get("/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total_customers"] == 0
        assert data["total_simulations"] == 0
        assert data["total_mrr"] == 0.0

    def test_counts_customers_and_simulations(self, client, es_customer):
        client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 15,
                "storage_gb": 100,
                "api_calls": 50000,
            },
        )
        res = client.get("/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total_customers"] == 1
        assert data["total_simulations"] == 1
        assert data["total_mrr"] == pytest.approx(169.40, rel=1e-3)

    def test_mrr_uses_latest_simulation_per_customer(self, client, es_customer):
        # Two simulations for same customer — MRR should use only the latest
        client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 10,
                "storage_gb": 50,
                "api_calls": 0,
            },
        )
        client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 50,
                "storage_gb": 200,
                "api_calls": 0,
            },
        )
        res = client.get("/stats")
        data = res.json()
        assert data["total_simulations"] == 2
        # latest sim: 50 users = (10×10)+(40×8) = 420 base, ×1.21 = 508.20
        assert data["total_mrr"] == pytest.approx(508.20, rel=1e-3)

    def test_last_simulation_at_in_list(self, client, es_customer):
        # Verify last_simulation_at is returned in GET /customers
        client.post(
            "/simulations",
            json={
                "customer_id": es_customer["id"],
                "active_users": 10,
                "storage_gb": 50,
                "api_calls": 0,
            },
        )
        res = client.get("/customers")
        assert res.status_code == 200
        customer = res.json()[0]
        assert customer["last_simulation_at"] is not None

    def test_last_simulation_at_null_when_no_sims(self, client, es_customer):
        res = client.get("/customers")
        customer = res.json()[0]
        assert customer["last_simulation_at"] is None
