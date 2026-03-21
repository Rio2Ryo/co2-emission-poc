"""E2E test: sales and POS CSV upload flows"""
import os

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


def _run_flow(filename, data_type):
    with open(os.path.join(FIXTURES, filename), "rb") as f:
        r = client.post(
            "/api/v1/uploads",
            files={"file": (filename, f, "text/csv")},
            data={"data_type": data_type},
        )
    assert r.status_code == 201, f"upload {filename} failed: {r.text}"
    uid = r.json()["upload_id"]

    r = client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": {}})
    assert r.status_code == 201, f"mapping failed: {r.text}"

    r = client.post(
        "/api/v1/calculations",
        json={"upload_id": uid, "emission_factor_version": "2023"},
    )
    assert r.status_code == 202, f"calculation failed: {r.text}"
    job_id = r.json()["job_id"]

    r = client.get(f"/api/v1/calculations/{job_id}/results")
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["grand_total"] >= 0, f"grand_total was {summary['grand_total']}"
    return summary


def test_sales_flow():
    s = _run_flow("sales_sample.csv", "sales")
    assert s["grand_total"] >= 0


def test_pos_flow():
    s = _run_flow("pos_sample.csv", "pos")
    assert s["grand_total"] >= 0
