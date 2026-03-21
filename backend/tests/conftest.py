"""
Pytest configuration and shared fixtures.

Set TEST_DATABASE_URL to run tests against PostgreSQL:
  TEST_DATABASE_URL=postgresql://co2poc:co2poc@localhost:5432/co2poc_test pytest
Default: SQLite in-memory.
"""
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient


def _make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url)


def make_test_engine():
    url = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    return _make_engine(url)


def make_test_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def make_db_override(session_factory):
    def _override() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()
    return _override
