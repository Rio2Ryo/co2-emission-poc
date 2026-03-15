"""API統合テスト: アップロード→マッピング→算出→結果取得→レポート出力"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_PATH = "/tmp/co2poc_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# テスト用DBセットアップ
test_engine = create_engine(
    f"sqlite:///{TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=test_engine)

client = TestClient(app)

FIXTURES = os.path.join(os.path.dirname(__file__), "..", "fixtures")

STANDARD_MAPPING = {
    "勘定科目コード": "account_code",
    "勘定科目名":     "account_name",
    "数量":           "quantity",
    "単位":           "unit",
    "金額":           "amount",
}


# ---- ヘルスチェック -------------------------------------------------------

def test_health():
    """IT-000: ヘルスエンドポイント"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---- アップロード ---------------------------------------------------------

def test_upload_accounting_csv_success():
    """IT-001: 正常系 - 会計CSVアップロード"""
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post(
            "/api/v1/uploads",
            files={"file": ("accounting_sample.csv", f, "text/csv")},
            data={"data_type": "accounting"},
        )
    assert r.status_code == 201
    data = r.json()
    assert data["upload_id"] is not None
    assert data["row_count"] == 5
    assert data["status"] == "pending_mapping"
    assert "勘定科目名" in data["headers"]


def test_upload_empty_file():
    """IT-002: 異常系 - 空ファイル → 422"""
    r = client.post(
        "/api/v1/uploads",
        files={"file": ("empty.csv", b"", "text/csv")},
        data={"data_type": "accounting"},
    )
    assert r.status_code == 422


def test_upload_invalid_extension():
    """IT-003: 異常系 - .csv以外 → 422"""
    r = client.post(
        "/api/v1/uploads",
        files={"file": ("test.xlsx", b"binary", "application/octet-stream")},
        data={"data_type": "accounting"},
    )
    assert r.status_code == 422


def test_upload_missing_required_column():
    """IT-004: 異常系 - 必須列欠落 → 422"""
    with open(os.path.join(FIXTURES, "accounting_sample_invalid.csv"), "rb") as f:
        r = client.post(
            "/api/v1/uploads",
            files={"file": ("invalid.csv", f, "text/csv")},
            data={"data_type": "accounting"},
        )
    assert r.status_code == 422


# ---- マッピング -----------------------------------------------------------

def _upload_sample():
    """テスト用アップロードヘルパー"""
    with open(os.path.join(FIXTURES, "accounting_sample.csv"), "rb") as f:
        r = client.post(
            "/api/v1/uploads",
            files={"file": ("accounting_sample.csv", f, "text/csv")},
            data={"data_type": "accounting"},
        )
    assert r.status_code == 201
    return r.json()["upload_id"]


def test_save_mapping():
    """IT-005: 列マッピング保存"""
    upload_id = _upload_sample()
    r = client.post(
        f"/api/v1/uploads/{upload_id}/mappings",
        json={"mappings": STANDARD_MAPPING},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["mapping_id"] is not None
    assert data["upload_id"] == upload_id


def test_save_mapping_not_found():
    """IT-006: 異常系 - 存在しないupload_id → 404"""
    r = client.post(
        "/api/v1/uploads/nonexistent-id/mappings",
        json={"mappings": STANDARD_MAPPING},
    )
    assert r.status_code == 404


# ---- 算出 ----------------------------------------------------------------

def _upload_and_map():
    """アップロード + マッピング済みのupload_idを返すヘルパー"""
    upload_id = _upload_sample()
    client.post(
        f"/api/v1/uploads/{upload_id}/mappings",
        json={"mappings": STANDARD_MAPPING},
    )
    return upload_id


def test_full_calculation_flow():
    """IT-007: 統合フロー - アップロード → マッピング → 算出 → 結果確認"""
    upload_id = _upload_and_map()

    # 算出実行
    r = client.post(
        "/api/v1/calculations",
        json={"upload_id": upload_id},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    assert r.json()["status"] == "completed"

    # 結果取得
    r2 = client.get(f"/api/v1/calculations/{job_id}/results")
    assert r2.status_code == 200
    data = r2.json()
    assert len(data["rows"]) == 5
    assert data["summary"]["grand_total"] > 0

    # Scope2（電力）が正しく算出されていること
    scope2_rows = [row for row in data["rows"] if row["scope"] == 2]
    assert len(scope2_rows) >= 1
    # 電力1000kWh × 0.453 = 453.0 kg-CO2e
    elec_row = next(r for r in scope2_rows if r["activity_type"] == "electricity")
    assert elec_row["amount_kg_co2e"] == pytest.approx(453.0, rel=1e-2)


def test_scope_summary_integrity():
    """IT-008: grand_total = scope1 + scope2 + scope3"""
    upload_id = _upload_and_map()
    r = client.post("/api/v1/calculations", json={"upload_id": upload_id})
    job_id = r.json()["job_id"]

    r2 = client.get(f"/api/v1/calculations/{job_id}/results")
    s = r2.json()["summary"]
    assert s["grand_total"] == pytest.approx(
        s["scope1_total"] + s["scope2_total"] + s["scope3_total"], rel=1e-5
    )


def test_calculation_job_not_found():
    """IT-009: 存在しないジョブID → 404"""
    r = client.get("/api/v1/calculations/nonexistent-job-id/results")
    assert r.status_code == 404


def test_recalculation_different_version():
    """IT-010: 再計算 - 異なる係数バージョンで結果が変わること"""
    upload_id = _upload_and_map()

    r1 = client.post("/api/v1/calculations",
                     json={"upload_id": upload_id, "emission_factor_version": "2023"})
    job1_id = r1.json()["job_id"]
    total1 = client.get(f"/api/v1/calculations/{job1_id}/results").json()["summary"]["grand_total"]

    r2 = client.post(f"/api/v1/calculations/{job1_id}/recalculate",
                     json={"emission_factor_version": "2021"})
    job2_id = r2.json()["job_id"]
    total2 = client.get(f"/api/v1/calculations/{job2_id}/results").json()["summary"]["grand_total"]

    # 2021と2023で電力係数が異なるので合計が異なる
    assert total1 != total2


def test_recalculation_idempotency():
    """IT-011: 再計算の冪等性 - 同バージョン2回実行 → 同一結果"""
    upload_id = _upload_and_map()

    r1 = client.post("/api/v1/calculations",
                     json={"upload_id": upload_id, "emission_factor_version": "2023"})
    job_id = r1.json()["job_id"]

    r2 = client.post(f"/api/v1/calculations/{job_id}/recalculate",
                     json={"emission_factor_version": "2023"})
    job2_id = r2.json()["job_id"]

    t1 = client.get(f"/api/v1/calculations/{job_id}/results").json()["summary"]["grand_total"]
    t2 = client.get(f"/api/v1/calculations/{job2_id}/results").json()["summary"]["grand_total"]
    assert t1 == pytest.approx(t2, rel=1e-10)


# ---- レポート出力 ---------------------------------------------------------

def test_csv_export():
    """IT-012: CSV出力 - 正常系"""
    upload_id = _upload_and_map()
    r = client.post("/api/v1/calculations", json={"upload_id": upload_id})
    job_id = r.json()["job_id"]

    r2 = client.get(f"/api/v1/reports/{job_id}/csv")
    assert r2.status_code == 200
    assert "text/csv" in r2.headers["content-type"]
    content = r2.text
    assert "排出量(kg-CO2e)" in content
    assert "Scope2合計" in content


def test_csv_export_job_not_found():
    """IT-013: CSV出力 - 存在しないジョブ → 404"""
    r = client.get("/api/v1/reports/nonexistent/csv")
    assert r.status_code == 404
