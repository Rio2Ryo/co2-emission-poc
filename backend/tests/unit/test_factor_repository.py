"""UT-040〜045: 排出係数リポジトリのユニットテスト"""
import pytest
from app.core.factor_repository import InMemoryFactorRepository, get_emission_factor
from app.exceptions import EmissionFactorNotFoundError


@pytest.fixture
def repo():
    return InMemoryFactorRepository()


class TestFactorRepository:

    def test_get_with_explicit_version(self, repo):
        """UT-040: バージョン明示取得"""
        f = get_emission_factor("electricity", "2022", repo)
        assert f.version == "2022"
        assert f.value > 0

    def test_get_default_latest(self, repo):
        """UT-041: バージョン未指定 → 2023(最新)"""
        f = get_emission_factor("electricity", None, repo)
        assert f.version == "2023"

    def test_unknown_activity_raises(self, repo):
        """UT-042: 未登録活動種別 → EmissionFactorNotFoundError"""
        with pytest.raises(EmissionFactorNotFoundError):
            get_emission_factor("unknown_xyz", "2023", repo)

    def test_unknown_version_raises(self, repo):
        """UT-043: 存在しないバージョン → EmissionFactorNotFoundError"""
        with pytest.raises(EmissionFactorNotFoundError):
            get_emission_factor("electricity", "1999", repo)

    def test_version_values_differ(self, repo):
        """UT-044: バージョン間で係数値が異なること（再計算の意味を担保）"""
        f2022 = get_emission_factor("electricity", "2022", repo)
        f2023 = get_emission_factor("electricity", "2023", repo)
        assert f2022.value != f2023.value

    def test_all_standard_types_available(self, repo):
        """UT-045: 標準活動種別が全て取得できること"""
        for at in ["electricity", "natural_gas", "gasoline", "diesel"]:
            f = get_emission_factor(at, "2023", repo)
            assert f.value > 0
            assert f.scope in [1, 2, 3]
