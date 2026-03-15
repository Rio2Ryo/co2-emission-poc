"""排出係数リポジトリ - バージョン管理付き（環境省2023年度版ベース、仮値）"""
from typing import Dict, List, Optional, Tuple

from app.core.emission import EmissionFactor
from app.exceptions import EmissionFactorNotFoundError

# (activity_type, version) → factor data
DEFAULT_FACTORS: Dict[Tuple[str, str], Dict] = {
    ("electricity",     "2023"): {"value": 0.453, "unit": "kg-CO2e/kWh", "scope": 2},
    ("electricity",     "2022"): {"value": 0.457, "unit": "kg-CO2e/kWh", "scope": 2},
    ("electricity",     "2021"): {"value": 0.462, "unit": "kg-CO2e/kWh", "scope": 2},
    ("natural_gas",     "2023"): {"value": 2.21,  "unit": "kg-CO2e/m3",  "scope": 1},
    ("natural_gas",     "2022"): {"value": 2.23,  "unit": "kg-CO2e/m3",  "scope": 1},
    ("gasoline",        "2023"): {"value": 2.32,  "unit": "kg-CO2e/L",   "scope": 1},
    ("gasoline",        "2022"): {"value": 2.32,  "unit": "kg-CO2e/L",   "scope": 1},
    ("diesel",          "2023"): {"value": 2.58,  "unit": "kg-CO2e/L",   "scope": 1},
    ("diesel",          "2022"): {"value": 2.58,  "unit": "kg-CO2e/L",   "scope": 1},
    ("kerosene",        "2023"): {"value": 2.49,  "unit": "kg-CO2e/L",   "scope": 1},
    ("lpg",             "2023"): {"value": 3.00,  "unit": "kg-CO2e/kg",  "scope": 1},
    ("business_travel", "2023"): {"value": 0.115, "unit": "kg-CO2e/km",  "scope": 3},
    ("freight",         "2023"): {"value": 0.190, "unit": "kg-CO2e/tkm", "scope": 3},
}

LATEST_VERSION = "2023"
AVAILABLE_VERSIONS = ["2021", "2022", "2023"]


class InMemoryFactorRepository:
    """インメモリ排出係数リポジトリ（テスト用・PoC用）"""

    def __init__(self):
        self._factors: Dict[Tuple[str, str], Dict] = dict(DEFAULT_FACTORS)

    def seed(self, factors: List[Dict]) -> None:
        for f in factors:
            self._factors[(f["activity_type"], f["version"])] = {
                "value": f["value"], "unit": f["unit"], "scope": f["scope"],
            }

    def get(self, activity_type: str, version: Optional[str] = None) -> EmissionFactor:
        v = version or LATEST_VERSION
        key = (activity_type, v)
        if key not in self._factors:
            raise EmissionFactorNotFoundError(activity_type=activity_type, version=v)
        d = self._factors[key]
        return EmissionFactor(
            value=d["value"], unit=d["unit"], scope=d["scope"],
            activity_type=activity_type, version=v,
        )


def get_emission_factor(
    activity_type: str,
    version: Optional[str],
    db: InMemoryFactorRepository,
) -> EmissionFactor:
    return db.get(activity_type, version)
