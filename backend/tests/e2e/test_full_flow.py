"""E2E test: upload -> mapping -> calculation -> results -> CSV export"""
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
Base.metadata.create_all(bind=_engine)

_override_get_db = make_db_override(_Session)
app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")
MAPPING = {
    "勘定科目コード": "account_code",
    "勘定科目名": "account_name",
    "数量": "quantity",
    "単位": "unit",
    "金額": "amount",
}


def test_full_flow():
    # 1. Upload CSV
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post(
            "/api/v1/uploads",
            files={"file": ("accounting_sample.csv", f, "text/csv")},
            data={"data_type": "accounting"},
        )
    assert r.status_code == 201, f"upload failed: {r.text}"
    upload_id = r.json()["upload_id"]

    # 2. Save column mapping
    r = client.post(
        f"/api/v1/uploads/{upload_id}/mappings",
        json={"mappings": MAPPING},
    )
    assert r.status_code == 201, f"mapping failed: {r.text}"

    # 3. Run calculation
    r = client.post(
        "/api/v1/calculations",
        json={"upload_id": upload_id, "emission_factor_version": "2023"},
    )
    assert r.status_code == 202, f"calculation failed: {r.text}"
    job = r.json()
    job_id = job["job_id"]

    # 4. Assert completed
    assert job["status"] == "completed", f"unexpected status: {job['status']}"

    # 5. Check results
    r = client.get(f"/api/v1/calculations/{job_id}/results")
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["grand_total"] > 0, f"grand_total was {summary['grand_total']}"
    assert summary["scope1_total"] > 0, f"scope1_total was {summary['scope1_total']}"

    # 6. CSV export
    r = client.get(f"/api/v1/reports/{job_id}/csv")
    assert r.status_code == 200
    assert "排出量(kg-CO2e)" in r.text, "CSV missing expected header"
