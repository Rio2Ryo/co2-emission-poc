"""
算出パイプライン: CSV行データ → EmissionResult のオーケストレーション

責務:
  1. マッピング適用 (mapping.py)
  2. Scope/活動種別分類 (classification.py)
  3. 排出係数取得 (factor_repository.py)
  4. 排出量算出 (emission.py)
"""
import csv
import io
from typing import List, Dict, Any, Optional

from app.core.classification import classify_scope
from app.core.emission import EmissionResult, calculate_emission
from app.core.factor_repository import InMemoryFactorRepository
from app.exceptions import (
    CO2SystemError, EmissionFactorNotFoundError, MissingRequiredColumnError
)

# デフォルトの列マッピング（会計CSV用）
DEFAULT_ACCOUNTING_MAPPING = {
    "勘定科目コード": "account_code",
    "勘定科目名":     "account_name",
    "数量":           "quantity",
    "単位":           "unit",
    "金額":           "amount",
}

FACTOR_REPO = InMemoryFactorRepository()


def process_accounting_row(
    row: Dict[str, str],
    column_mapping: Dict[str, str],
    factor_version: str = "2023",
) -> EmissionResult:
    """
    会計CSV1行を処理して EmissionResult を返す。

    1. 列マッピング適用
    2. Scope分類
    3. 係数取得
    4. 排出量算出
    """
    # --- 1. 列マッピング ---
    mapped: Dict[str, Any] = {}
    for raw_col, std_col in column_mapping.items():
        val = row.get(raw_col, "")
        mapped[std_col] = val.strip() if val else ""

    account_code = mapped.get("account_code", "") or None
    account_name = mapped.get("account_name", "") or None

    # --- 2. Scope分類 ---
    classification = classify_scope(account_code=account_code, account_name=account_name)

    if classification.status == "unclassified":
        return EmissionResult(
            amount_kg_co2e=0.0,
            scope=None,
            activity_type=None,
            status="unclassified",
        )

    # --- 3. 活動量の取得 ---
    qty_str = mapped.get("quantity", "").replace(",", "")
    try:
        activity_amount = float(qty_str) if qty_str else 0.0
    except ValueError:
        return EmissionResult(
            amount_kg_co2e=0.0,
            scope=classification.scope,
            activity_type=classification.activity_type,
            status="error",
            error_message=f"Invalid quantity: {qty_str!r}",
        )

    # --- 4. 係数取得 & 算出 ---
    try:
        factor = FACTOR_REPO.get(
            activity_type=classification.activity_type,
            version=factor_version,
        )
        result = calculate_emission(
            activity_amount=activity_amount,
            unit=mapped.get("unit", ""),
            factor=factor,
        )
        result.activity_type = classification.activity_type
        return result
    except EmissionFactorNotFoundError:
        return EmissionResult(
            amount_kg_co2e=0.0,
            scope=classification.scope,
            activity_type=classification.activity_type,
            status="unclassified",
            error_message=f"Factor not found: {classification.activity_type}",
        )
    except CO2SystemError as e:
        return EmissionResult(
            amount_kg_co2e=0.0,
            scope=classification.scope,
            activity_type=classification.activity_type,
            status="error",
            error_message=str(e),
        )


def process_csv_content(
    csv_content: str,
    column_mapping: Optional[Dict[str, str]] = None,
    factor_version: str = "2023",
) -> List[EmissionResult]:
    """CSVテキストを処理して全行の EmissionResult リストを返す。"""
    mapping = column_mapping or DEFAULT_ACCOUNTING_MAPPING
    reader = csv.DictReader(io.StringIO(csv_content))
    results = []
    for row in reader:
        r = process_accounting_row(row, mapping, factor_version)
        results.append(r)
    return results
