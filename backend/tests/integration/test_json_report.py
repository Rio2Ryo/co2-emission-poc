"""Integration tests for GET /api/v1/reports/{job_id}/json"""
import os
import uuid

TEST_DB = f"/tmp/co2poc_test_jr_{uuid.uuid4().hex[:8]}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db

_engine = create_engine(f"sqlite:///{TEST_DB}", connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


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


def test_json_report_full():
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("a.csv", f, "text/csv")}, data={"data_type": "accounting"})
    uid = r.json()["upload_id"]
    client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": MAPPING})
    r = client.post("/api/v1/calculations", json={"upload_id": uid, "emission_factor_version": "2023"})
    job_id = r.json()["job_id"]

    r = client.get(f"/api/v1/reports/{job_id}/json")
    assert r.status_code == 200
    d = r.json()
    assert d["metadata"]["job_id"] == job_id
    assert d["metadata"]["emission_factor_version"] == "2023"
    assert d["metadata"]["data_type"] == "accounting"
    assert d["summary"]["grand_total"] > 0
    assert len(d["rows"]) == 5


def test_json_report_not_found():
    r = client.get(f"/api/v1/reports/{uuid.uuid4()}/json")
    assert r.status_code == 404
