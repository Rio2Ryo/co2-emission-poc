# CO2 Emission PoC

会計データ・売上/POSデータから CO2 排出量を算出し、将来的に環境金融・カーボンクレジット活用へ拡張できるシステムの PoC / MVP。

---

## 概要

| 項目 | 内容 |
|------|------|
| フェーズ | Phase 1 MVP / PoC |
| バックエンド | FastAPI (Python 3.12) + SQLAlchemy 1.4 + SQLite |
| テスト | pytest (ユニット 38件 + 統合 14件 = **52件、全通過**) |
| 算出方式 | 活動量 × 排出係数（環境省2023年度版ベース） |

---

## クイックスタート（デモ実行）

```bash
cd /root/.openclaw/workspace/co2-emission-poc/backend
PYTHONPATH=. python3 scripts/demo_api_flow.py
```

実行すると `accounting_sample.csv` を使って upload → mapping → calculation → recalculation → CSV export の全フローを実行し、`ALL CHECKS PASSED` を出力します。

CSVレポートをファイルに書き出す場合は `--csv-out` を指定します:

```bash
PYTHONPATH=. python3 scripts/demo_api_flow.py --csv-out /tmp/co2-demo-report.csv
```

---

## フロントエンドデモ（ローカル確認）

バックエンドサーバーを起動したあと、別ターミナルでフロントエンドを静的配信します:

```bash
# ターミナル1: バックエンド起動
cd /root/.openclaw/workspace/co2-emission-poc/backend
PYTHONPATH=. python3 -m uvicorn app.main:app --reload

# ターミナル2: frontend/ を静的配信
cd /root/.openclaw/workspace/co2-emission-poc
python3 -m http.server 8090 --directory frontend/
# → http://localhost:8090 でブラウザ確認
```

`frontend/index.html` を開くと CSV アップロード → 排出量算出 → スコープ別サマリ表示 → CSV ダウンロードの UI が利用できます。

---

## セットアップ

```bash
# apt (Ubuntu 24.04)
sudo apt-get install -y python3 python3-fastapi python3-sqlalchemy python3-pydantic python3-uvicorn python3-httpx python3-pytest

cd backend
```

---

## テスト実行

```bash
cd backend

# ユニットテスト (38件)
PYTHONPATH=. python3 -m pytest tests/unit/ -v

# API統合テスト (14件)
PYTHONPATH=. python3 -m pytest tests/integration/ -v

# 全テスト
PYTHONPATH=. python3 -m pytest tests/unit/ tests/integration/ -v
```

**期待結果**: 75+ passed

---

## サーバー起動

```bash
cd backend
PYTHONPATH=. python3 -m uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/uploads` | List all past uploads |
| POST | `/api/v1/uploads` | Upload a CSV file (accounting/sales/pos) |
| GET | `/api/v1/uploads/{upload_id}` | Get upload status and row count |
| DELETE | `/api/v1/uploads/{upload_id}` | Delete upload and all cascaded data |
| POST | `/api/v1/uploads/{upload_id}/mappings` | Save column mapping |
| GET | `/api/v1/calculations` | List all past calculation jobs with grand totals |
| POST | `/api/v1/calculations` | Start a new calculation job |
| GET | `/api/v1/calculations/{job_id}` | Get job status |
| GET | `/api/v1/calculations/{job_id}/results` | Get per-row results and scope summary |
| POST | `/api/v1/calculations/{job_id}/recalculate` | Re-run with different factor version |
| GET | `/api/v1/comparisons?job_ids=id1,id2` | Compare scope totals and delta between jobs |
| GET | `/api/v1/reports/{job_id}/csv` | Export results as CSV |
| GET | `/api/v1/reports/{job_id}/json` | Export results as structured JSON report |
| POST | `/api/v1/uploads/batch` | Batch upload multiple CSV files |
| GET | `/api/v1/dashboard/summary` | Aggregate stats across all completed jobs |
| GET | `/api/v1/audit-logs` | Paginated audit trail (supports limit, offset, action filter) |
| GET | `/api/v1/factors` | List available emission factor versions and entries |
| GET | `/health` | Health check |

Swagger UI: http://localhost:8000/docs

---

## サンプルCSV

| ファイル | 内容 |
|---------|------|
| `tests/fixtures/accounting_sample.csv` | 会計データ正常系 (5行、Scope1/2/3含む) |
| `tests/fixtures/accounting_sample_invalid.csv` | 必須列欠落（異常系テスト用） |
| `tests/fixtures/sales_sample.csv` | 販売データ正常系 |
| `tests/fixtures/pos_sample.csv` | POSデータ正常系 |

---

## 算出ロジック

```
排出量 (kg-CO2e) = 活動量 × 排出係数
```

| 活動種別 | 単位 | 係数 (2023) | Scope |
|---------|------|------------|-------|
| 電力 | kWh | 0.453 kg-CO2e/kWh | 2 |
| 天然ガス | m³ | 2.21 kg-CO2e/m³ | 1 |
| ガソリン | L | 2.32 kg-CO2e/L | 1 |
| 軽油 | L | 2.58 kg-CO2e/L | 1 |

> 係数出典: 環境省 算定・報告・公表制度 排出係数（仮値）

---

## 3概念の分離（重要）

| 概念 | 定義 | 実装フェーズ |
|------|------|-------------|
| **排出量算出** | 活動量 × 係数 = CO2量 | ✅ Phase 1 実装済み |
| **削減量算出** | ベースライン - 実績 = 削減量 | Phase 3 (未実装) |
| **クレジット化** | 削減量の検証・発行・売買 | Phase 3 (スコープ外) |

---

## 実装済み / 未実装

### ✅ 実装済み (Phase 1)
- CSV取込（会計/販売/POS）
- 列マッピング
- Scope/活動種別分類（コード・キーワードベース）
- 排出係数DB（インメモリ、バージョン管理付き）
- 排出量算出
- Scope別集計
- 算出ジョブ管理
- 再計算（係数バージョン変更対応）
- 監査ログ
- CSVエクスポート
- ユニットテスト 38件
- API統合テスト 14件

### ⬜ 未実装 (Phase 2以降)
- フロントエンド (Next.js)
- PostgreSQL対応（現在SQLite）
- PDF出力
- 商品辞書・原材料分解
- AI未登録商品推定
- POS APIリアルタイム連携
- 削減量トラッキング
- MRV対応
- 認証・認可

---

## ディレクトリ構成

```
co2-emission-poc/
└── backend/
    ├── app/
    │   ├── core/
    │   │   ├── emission.py          # 排出量算出（純粋関数）
    │   │   ├── aggregation.py       # Scope集計（純粋関数）
    │   │   ├── mapping.py           # 列マッピング（純粋関数）
    │   │   ├── classification.py    # Scope分類（純粋関数）
    │   │   ├── factor_repository.py # 排出係数DB（バージョン管理）
    │   │   └── calculator.py        # 算出パイプライン
    │   ├── api/v1/
    │   │   ├── uploads.py           # CSV取込・マッピングAPI
    │   │   ├── calculations.py      # 算出・再計算API
    │   │   └── reports.py           # レポート出力API
    │   ├── db/
    │   │   ├── base.py              # DBモデル定義
    │   │   └── session.py           # DB接続管理
    │   ├── exceptions.py            # カスタム例外
    │   └── main.py                  # FastAPIエントリポイント
    └── tests/
        ├── unit/                    # ユニットテスト (38件)
        ├── integration/             # API統合テスト (14件)
        └── fixtures/                # サンプルCSV
```
