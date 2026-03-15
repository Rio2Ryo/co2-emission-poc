"""UT-030〜036: 分類ロジックのユニットテスト"""
import pytest
from app.core.classification import classify_scope


class TestScopeClassification:

    def test_electricity_code(self):
        """UT-030: コード710 → Scope2/electricity"""
        r = classify_scope(account_code="710", account_name="電力費")
        assert r.scope == 2
        assert r.activity_type == "electricity"
        assert r.match_method == "code"

    def test_gasoline_code(self):
        """UT-031: コード730 → Scope1/gasoline"""
        r = classify_scope(account_code="730", account_name="燃料費")
        assert r.scope == 1
        assert r.activity_type == "gasoline"

    def test_business_travel_code(self):
        """UT-032: コード750 → Scope3/business_travel"""
        r = classify_scope(account_code="750", account_name="旅費交通費")
        assert r.scope == 3
        assert r.activity_type == "business_travel"

    def test_unclassifiable(self):
        """UT-033: 未定義コード・マッチなし → unclassified"""
        r = classify_scope(account_code="999", account_name="雑費")
        assert r.scope is None
        assert r.status == "unclassified"

    def test_code_priority_over_keyword(self):
        """UT-034: コードとキーワード競合 → コード優先"""
        # コード730=gasoline/Scope1。名称に"電力"を含めてもScope1のまま
        r = classify_scope(account_code="730", account_name="電力・燃料費")
        assert r.scope == 1
        assert r.activity_type == "gasoline"
        assert r.match_method == "code"

    def test_keyword_fallback(self):
        """UT-035: コードなし・キーワードマッチ → keyword分類"""
        r = classify_scope(account_code="999", account_name="電力購入費用")
        assert r.scope == 2
        assert r.match_method == "keyword"

    def test_gas_keyword(self):
        """UT-036: "ガス"キーワード → Scope1/natural_gas"""
        r = classify_scope(account_code=None, account_name="都市ガス代")
        assert r.scope == 1
        assert r.activity_type == "natural_gas"
