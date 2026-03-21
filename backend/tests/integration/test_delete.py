"""Integration tests for DELETE /api/v1/uploads/{upload_id}"""
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


def test_delete_upload():
    # Upload
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    assert r.status_code == 201
    uid = r.json()["upload_id"]

    # Map + calculate
    client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": MAPPING})
    r = client.post("/api/v1/calculations", json={"upload_id": uid, "emission_factor_version": "2023"})
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    # Delete
    r = client.delete(f"/api/v1/uploads/{uid}")
    assert r.status_code == 204

    # Verify gone
    r = client.get("/api/v1/uploads")
    ids = [u["upload_id"] for u in r.json()["uploads"]]
    assert uid not in ids

    # Cascaded job results should be gone
    r = client.get(f"/api/v1/calculations/{job_id}/results")
    assert r.status_code == 404


def test_delete_nonexistent():
    r = client.delete(f"/api/v1/uploads/{uuid.uuid4()}")
    assert r.status_code == 404


def test_delete_returns_json_on_404():
    r = client.delete(f"/api/v1/uploads/{uuid.uuid4()}")
    assert r.status_code == 404
    assert "application/json" in r.headers.get("content-type", "")
