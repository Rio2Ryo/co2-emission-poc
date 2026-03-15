"""UT-001〜009: 排出量算出ロジックのユニットテスト"""
import pytest
from app.core.emission import EmissionFactor, calculate_emission
from app.exceptions import EmissionFactorNotFoundError, InvalidActivityAmountError


class TestEmissionCalculation:

    def test_electricity_scope2(self):
        """UT-001: 電力100kWh → 45.3 kg-CO2e (100 × 0.453)"""
        f = EmissionFactor(value=0.453, unit="kg-CO2e/kWh", scope=2, activity_type="electricity")
        r = calculate_emission(100.0, "kWh", f)
        assert r.amount_kg_co2e == pytest.approx(45.3, rel=1e-3)
        assert r.scope == 2
        assert r.status == "calculated"

    def test_gasoline_scope1(self):
        """UT-002: ガソリン50L → 116.0 kg-CO2e (50 × 2.32)"""
        f = EmissionFactor(value=2.32, unit="kg-CO2e/L", scope=1)
        r = calculate_emission(50.0, "L", f)
        assert r.amount_kg_co2e == pytest.approx(116.0, rel=1e-3)
        assert r.scope == 1

    def test_natural_gas_scope1(self):
        """UT-003: 天然ガス150m³ → 331.5 kg-CO2e (150 × 2.21)"""
        f = EmissionFactor(value=2.21, unit="kg-CO2e/m3", scope=1)
        r = calculate_emission(150.0, "m3", f)
        assert r.amount_kg_co2e == pytest.approx(331.5, rel=1e-3)

    def test_none_factor_raises(self):
        """UT-004: factor=None → EmissionFactorNotFoundError"""
        with pytest.raises(EmissionFactorNotFoundError):
            calculate_emission(100.0, "unit", None)

    def test_zero_activity_returns_zero(self):
        """UT-005: 活動量0 → 排出量0"""
        f = EmissionFactor(value=0.453, unit="kg-CO2e/kWh", scope=2)
        r = calculate_emission(0.0, "kWh", f)
        assert r.amount_kg_co2e == 0.0

    def test_negative_amount_raises(self):
        """UT-006: 負の活動量 → InvalidActivityAmountError"""
        f = EmissionFactor(value=2.32, unit="kg-CO2e/L", scope=1)
        with pytest.raises(InvalidActivityAmountError) as exc:
            calculate_emission(-10.0, "L", f)
        assert exc.value.amount == -10.0

    def test_large_amount_precision(self):
        """UT-007: 大量データ精度 (1,000,000 × 0.453 = 453,000)"""
        f = EmissionFactor(value=0.453, unit="kg-CO2e/kWh", scope=2)
        r = calculate_emission(1_000_000.0, "kWh", f)
        assert r.amount_kg_co2e == pytest.approx(453_000.0, rel=1e-5)

    def test_fractional_precision(self):
        """UT-008: 小数点精度 (0.5 × 2.32 = 1.16)"""
        f = EmissionFactor(value=2.32, unit="kg-CO2e/L", scope=1)
        r = calculate_emission(0.5, "L", f)
        assert r.amount_kg_co2e == pytest.approx(1.16, rel=1e-3)

    @pytest.mark.parametrize("amount,fval,expected,scope", [
        (100.0, 0.453,  45.3,  2),
        (50.0,  2.32,  116.0,  1),
        (150.0, 2.21,  331.5,  1),
        (1.0,   0.001,   0.001, 3),
    ])
    def test_parametrized(self, amount, fval, expected, scope):
        """UT-009: パラメータ化テスト"""
        f = EmissionFactor(value=fval, unit="kg-CO2e/unit", scope=scope)
        r = calculate_emission(amount, "unit", f)
        assert r.amount_kg_co2e == pytest.approx(expected, rel=1e-3)
