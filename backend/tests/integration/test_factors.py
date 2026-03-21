"""Integration tests for GET /api/v1/factors"""
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


def test_list_factors():
    r = client.get("/api/v1/factors")
    assert r.status_code == 200
    d = r.json()
    assert "versions" in d
    for ver in ("2023", "2022", "2021"):
        assert ver in d["versions"], f"missing version {ver}"
        entries = d["versions"][ver]
        assert len(entries) >= 1
        for e in entries:
            assert "activity_type" in e
            assert "unit" in e
            assert "factor_value" in e
            assert "scope" in e


def test_factors_electricity_2023():
    r = client.get("/api/v1/factors")
    entries = r.json()["versions"]["2023"]
    elec = [e for e in entries if e["activity_type"] == "electricity"]
    assert len(elec) == 1
    assert elec[0]["factor_value"] == 0.453
    assert elec[0]["scope"] == 2
