"""UT-020〜026: 列マッピング変換のユニットテスト"""
import pytest
from app.core.mapping import apply_column_mapping
from app.exceptions import ColumnTypeConversionError, MissingRequiredColumnError


class TestColumnMapping:

    def test_basic_mapping(self):
        """UT-020: 基本的な列名変換・型変換"""
        row = {"科目名": "電気料金", "金額": "50000", "数量": "1000"}
        mapping = {"科目名": "account_name", "金額": "amount", "数量": "quantity"}
        r = apply_column_mapping(row, mapping)
        assert r["account_name"] == "電気料金"
        assert r["amount"] == pytest.approx(50000.0)
        assert r["quantity"] == pytest.approx(1000.0)

    def test_missing_required_column(self):
        """UT-021: 必須列欠落 → MissingRequiredColumnError"""
        row = {"金額": "50000"}
        mapping = {"金額": "amount"}
        with pytest.raises(MissingRequiredColumnError) as exc:
            apply_column_mapping(row, mapping, required=["account_name", "amount"])
        assert "account_name" in str(exc.value)

    def test_non_numeric_raises(self):
        """UT-022: 数値列に文字列 → ColumnTypeConversionError"""
        row = {"金額": "abc", "科目名": "電気"}
        mapping = {"金額": "amount", "科目名": "account_name"}
        with pytest.raises(ColumnTypeConversionError) as exc:
            apply_column_mapping(row, mapping)
        assert exc.value.column == "amount"
        assert exc.value.raw_value == "abc"

    def test_optional_missing_returns_none(self):
        """UT-023: オプション列欠落 → None"""
        row = {"科目名": "電気料金", "金額": "50000"}
        mapping = {"科目名": "account_name", "金額": "amount"}
        r = apply_column_mapping(row, mapping, optional=["quantity"])
        assert r.get("quantity") is None

    def test_whitespace_stripped(self):
        """UT-024: 前後空白除去"""
        row = {"科目名": "  電気料金  ", "金額": " 50000 "}
        mapping = {"科目名": "account_name", "金額": "amount"}
        r = apply_column_mapping(row, mapping)
        assert r["account_name"] == "電気料金"
        assert r["amount"] == pytest.approx(50000.0)

    def test_optional_empty_numeric_returns_none(self):
        """UT-025: 空文字のオプション数値列 → None"""
        row = {"科目名": "旅費", "金額": "80000", "数量": ""}
        mapping = {"科目名": "account_name", "金額": "amount", "数量": "quantity"}
        r = apply_column_mapping(row, mapping, optional=["quantity"])
        assert r["quantity"] is None

    def test_comma_in_numeric(self):
        """UT-026: カンマ区切り数値 (1,000,000 → 1000000.0)"""
        row = {"科目名": "電力費", "金額": "1,000,000"}
        mapping = {"科目名": "account_name", "金額": "amount"}
        r = apply_column_mapping(row, mapping)
        assert r["amount"] == pytest.approx(1_000_000.0)
