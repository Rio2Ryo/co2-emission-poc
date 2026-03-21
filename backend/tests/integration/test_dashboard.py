"""Integration tests for GET /api/v1/dashboard/summary"""
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient

from tests.conftest import make_test_engine, make_test_session_factory, make_db_override
from app.main import app
from app.db.base import Base
from app.db.session import get_db

_engine = make_test_engine()
_Session = make_test_session_factory(_engine)
_override = make_db_override(_Session)


FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
MAPPING = {
    "勘定科目コード": "account_code",
    "勘定科目名": "account_name",
    "数量": "quantity",
    "単位": "unit",
    "金額": "amount",
}


@pytest.fixture(autouse=True)
def fresh_db():
    app.dependency_overrides[get_db] = _override
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield


client = TestClient(app)


def test_dashboard_empty():
    app.dependency_overrides[get_db] = _override
    r = client.get("/api/v1/dashboard/summary")
    assert r.status_code == 200
    d = r.json()
    assert d["total_jobs"] == 0
    assert d["total_emissions_kg"] == 0


def test_dashboard_after_calculation():
    app.dependency_overrides[get_db] = _override
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    uid = r.json()["upload_id"]
    client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": MAPPING})
    client.post("/api/v1/calculations", json={"upload_id": uid, "emission_factor_version": "2023"})

    r = client.get("/api/v1/dashboard/summary")
    assert r.status_code == 200
    d = r.json()
    assert d["total_jobs"] >= 1
    assert d["completed_jobs"] >= 1
    assert d["total_emissions_kg"] > 0
    assert d["scope1_total"] > 0
    assert d["scope2_total"] > 0


def test_dashboard_has_avg():
    app.dependency_overrides[get_db] = _override
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    uid = r.json()["upload_id"]
    client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": MAPPING})
    client.post("/api/v1/calculations", json={"upload_id": uid, "emission_factor_version": "2023"})

    d = client.get("/api/v1/dashboard/summary").json()
    assert d["avg_emissions_per_job"] > 0
    assert d["avg_emissions_per_job"] == d["total_emissions_kg"] / d["completed_jobs"]
