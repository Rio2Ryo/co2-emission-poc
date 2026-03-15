"""Integration tests for list endpoints (uploads, calculations)"""
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


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
    """Reset DB before each test."""
    app.dependency_overrides[get_db] = _override
    Base.metadata.drop_all(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    yield
    app.dependency_overrides[get_db] = _override


client = TestClient(app)


def test_list_uploads_empty():
    app.dependency_overrides[get_db] = _override
    r = client.get("/api/v1/uploads")
    assert r.status_code == 200
    assert r.json()["uploads"] == []


def test_list_uploads_after_create():
    app.dependency_overrides[get_db] = _override
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        client.post("/api/v1/uploads", files={"file": ("test.csv", f, "text/csv")}, data={"data_type": "accounting"})
    r = client.get("/api/v1/uploads")
    uploads = r.json()["uploads"]
    assert len(uploads) == 1
    assert uploads[0]["filename"] == "test.csv"


def test_list_calculations_after_run():
    app.dependency_overrides[get_db] = _override
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post("/api/v1/uploads", files={"file": ("calc.csv", f, "text/csv")}, data={"data_type": "accounting"})
    uid = r.json()["upload_id"]
    client.post(f"/api/v1/uploads/{uid}/mappings", json={"mappings": MAPPING})
    client.post("/api/v1/calculations", json={"upload_id": uid, "emission_factor_version": "2023"})

    r = client.get("/api/v1/calculations")
    jobs = r.json()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["grand_total"] > 0
