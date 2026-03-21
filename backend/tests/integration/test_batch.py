"""Integration tests for POST /api/v1/uploads/batch"""
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


def test_batch_upload_two_files():
    app.dependency_overrides[get_db] = _override
    f1 = open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb")
    f2 = open(os.path.join(FIXTURES, "sales_sample.csv"), "rb")
    r = client.post(
        "/api/v1/uploads/batch",
        files=[("files", ("a.csv", f1, "text/csv")), ("files", ("s.csv", f2, "text/csv"))],
        data={"data_type": "accounting"},
    )
    f1.close()
    f2.close()
    assert r.status_code == 201
    d = r.json()
    assert len(d["uploads"]) == 2
    assert d["uploads"][0]["upload_id"] != d["uploads"][1]["upload_id"]


def test_batch_upload_empty():
    app.dependency_overrides[get_db] = _override
    r = client.post("/api/v1/uploads/batch", data={"data_type": "accounting"})
    assert r.status_code == 422  # no files provided
