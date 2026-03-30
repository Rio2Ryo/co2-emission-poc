"""Integration tests for GET /api/v1/comparisons"""
import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from fastapi.testclient import TestClient

from tests.conftest import make_test_engine, make_test_session_factory, make_db_override
from app.main import app
from app.db.base import Base
from app.db.session import get_db

_engine = make_test_engine()
_Session = make_test_session_factory(_engine)
Base.metadata.create_all(bind=_engine)

_override = make_db_override(_Session)
app.dependency_overrides[get_db] = _override
client = TestClient(app)

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
MAPPING = {
    "勘定科目コード": "account_code",
    "勘定科目名": "account_name",
    "数量": "quantity",
    "単位": "unit",
    "金額": "amount",
}


def test_compare_two_versions():
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    uid = r.json()["upload_id"]
    client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": MAPPING})

    r1 = client.post("/api/v1/calculations", json={"upload_id": uid, "emission_factor_version": "2023"})
    j1 = r1.json()["job_id"]

    r2 = client.post(f"/api/v1/calculations/{j1}/recalculate", json={"emission_factor_version": "2021"})
    j2 = r2.json()["job_id"]

    r = client.get(f"/api/v1/comparisons?job_ids={j1},{j2}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["comparisons"]) == 2
    assert "delta" in data
    assert data["delta"]["grand_total"] != 0


def test_compare_invalid_ids():
    r = client.get(f"/api/v1/comparisons?job_ids={uuid.uuid4()}")
    assert r.status_code == 400
