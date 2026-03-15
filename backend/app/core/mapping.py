"""列マッピング変換ロジック - 純粋関数"""
from typing import Any, Dict, List, Optional

from app.exceptions import ColumnTypeConversionError, MissingRequiredColumnError

NUMERIC_COLUMNS = {"amount", "quantity", "unit_price"}
REQUIRED_STANDARD_COLUMNS = {"account_name", "amount"}


def apply_column_mapping(
    raw_row: Dict[str, str],
    mapping: Dict[str, str],
    required: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """生CSV行データを標準列名に変換する純粋関数。"""
    required_cols = set(required) if required is not None else REQUIRED_STANDARD_COLUMNS
    optional_cols = set(optional) if optional is not None else set()
    result: Dict[str, Any] = {}

    for raw_col, std_col in mapping.items():
        raw_value = raw_row.get(raw_col)
        if raw_value is None:
            if std_col in required_cols:
                raise MissingRequiredColumnError(column=std_col)
            if std_col in optional_cols:
                result[std_col] = None
            continue

        raw_value = raw_value.strip()

        if std_col in NUMERIC_COLUMNS:
            if raw_value == "":
                if std_col in optional_cols:
                    result[std_col] = None
                    continue
                raise ColumnTypeConversionError(column=std_col, raw_value=raw_value)
            try:
                result[std_col] = float(raw_value.replace(",", ""))
            except ValueError:
                raise ColumnTypeConversionError(column=std_col, raw_value=raw_value)
        else:
            result[std_col] = raw_value

    for req_col in required_cols:
        if req_col not in result:
            raise MissingRequiredColumnError(column=req_col)

    return result
