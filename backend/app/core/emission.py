"""排出量算出コアロジック - 純粋関数（テスト容易性重視）"""
from dataclasses import dataclass
from typing import Optional

from app.exceptions import EmissionFactorNotFoundError, InvalidActivityAmountError


@dataclass
class EmissionFactor:
    value: float        # kg-CO2e/単位
    unit: str           # e.g. "kg-CO2e/kWh"
    scope: int          # 1, 2, or 3
    activity_type: str = ""
    version: str = "2023"


@dataclass
class EmissionResult:
    amount_kg_co2e: float
    scope: int
    activity_type: str = ""
    row_id: str = ""
    status: str = "calculated"   # "calculated" | "unclassified" | "error"
    factor_version: str = "2023"
    error_message: Optional[str] = None


def calculate_emission(
    activity_amount: float,
    unit: str,
    factor: Optional[EmissionFactor],
) -> EmissionResult:
    """活動量 × 排出係数 = 排出量 (kg-CO2e)

    Raises:
        EmissionFactorNotFoundError: factor is None
        InvalidActivityAmountError: activity_amount < 0
    """
    if factor is None:
        raise EmissionFactorNotFoundError(activity_type="unknown")
    if activity_amount < 0:
        raise InvalidActivityAmountError(amount=activity_amount)

    amount_kg_co2e = round(activity_amount * factor.value, 6)

    return EmissionResult(
        amount_kg_co2e=amount_kg_co2e,
        scope=factor.scope,
        activity_type=factor.activity_type,
        factor_version=factor.version,
        status="calculated",
    )
