"""UT-010〜015: Scope集計ロジックのユニットテスト"""
import pytest
from app.core.aggregation import aggregate_by_scope
from app.core.emission import EmissionResult


class TestScopeAggregation:

    def test_basic_aggregation(self):
        """UT-010: Scope1/2/3の基本集計"""
        results = [
            EmissionResult(scope=1, amount_kg_co2e=100.0, row_id="r1"),
            EmissionResult(scope=2, amount_kg_co2e=200.0, row_id="r2"),
            EmissionResult(scope=3, amount_kg_co2e=50.0,  row_id="r3"),
            EmissionResult(scope=1, amount_kg_co2e=150.0, row_id="r4"),
        ]
        s = aggregate_by_scope(results)
        assert s.scope1_total == pytest.approx(250.0, rel=1e-5)
        assert s.scope2_total == pytest.approx(200.0, rel=1e-5)
        assert s.scope3_total == pytest.approx(50.0,  rel=1e-5)
        assert s.grand_total  == pytest.approx(500.0, rel=1e-5)

    def test_empty_list(self):
        """UT-011: 空リスト → 全ゼロ"""
        s = aggregate_by_scope([])
        assert s.grand_total == 0.0
        assert s.total_row_count == 0

    def test_scope1_only(self):
        """UT-012: Scope1のみ"""
        results = [
            EmissionResult(scope=1, amount_kg_co2e=300.0, row_id="r1"),
            EmissionResult(scope=1, amount_kg_co2e=200.0, row_id="r2"),
        ]
        s = aggregate_by_scope(results)
        assert s.scope1_total == pytest.approx(500.0)
        assert s.scope2_total == 0.0
        assert s.grand_total  == pytest.approx(500.0)

    def test_unclassified_excluded(self):
        """UT-013: 分類不能は合計に含まれない"""
        results = [
            EmissionResult(scope=1, amount_kg_co2e=100.0, row_id="r1"),
            EmissionResult(scope=None, amount_kg_co2e=None, row_id="r2", status="unclassified"),
        ]
        s = aggregate_by_scope(results)
        assert s.grand_total == pytest.approx(100.0)
        assert s.unclassified_count == 1

    def test_grand_total_identity(self):
        """UT-014: grand_total == scope1 + scope2 + scope3"""
        results = [
            EmissionResult(scope=1, amount_kg_co2e=111.1, row_id="r1"),
            EmissionResult(scope=2, amount_kg_co2e=222.2, row_id="r2"),
            EmissionResult(scope=3, amount_kg_co2e=333.3, row_id="r3"),
        ]
        s = aggregate_by_scope(results)
        assert s.grand_total == pytest.approx(
            s.scope1_total + s.scope2_total + s.scope3_total, rel=1e-10
        )

    def test_row_counts(self):
        """UT-015: 行数の追跡"""
        results = [
            EmissionResult(scope=1, amount_kg_co2e=100.0, row_id="r1"),
            EmissionResult(scope=2, amount_kg_co2e=200.0, row_id="r2"),
        ]
        s = aggregate_by_scope(results)
        assert s.total_row_count == 2
        assert s.calculated_row_count == 2
