"""Integration tests for GET /api/v1/audit-logs"""
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


@pytest.fixture(autouse=True)
def fresh_db():
    app.dependency_overrides[get_db] = _override
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield


client = TestClient(app)


def test_audit_log_after_upload():
    app.dependency_overrides[get_db] = _override
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    r = client.get("/api/v1/audit-logs")
    assert r.status_code == 200
    logs = r.json()["logs"]
    actions = [l["action"] for l in logs]
    assert "upload_created" in actions


def test_audit_log_after_delete():
    app.dependency_overrides[get_db] = _override
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    uid = r.json()["upload_id"]
    client.delete(f"/api/v1/uploads/{uid}")
    r = client.get("/api/v1/audit-logs")
    actions = [l["action"] for l in r.json()["logs"]]
    assert "upload_deleted" in actions


def test_audit_log_pagination():
    app.dependency_overrides[get_db] = _override
    for i in range(3):
        with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
            client.post("/api/v1/uploads", files={"file": (f"f{i}.csv", f, "text/csv")}, data={"data_type": "accounting"})
    r = client.get("/api/v1/audit-logs?limit=2")
    assert r.status_code == 200
    assert len(r.json()["logs"]) == 2
    assert r.json()["total"] >= 3
