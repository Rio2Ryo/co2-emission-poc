"""Custom exceptions for CO2 emission calculation system."""
from typing import Optional


class CO2SystemError(Exception):
    pass


class EmissionFactorNotFoundError(CO2SystemError):
    def __init__(self, activity_type: str, version: Optional[str] = None):
        self.activity_type = activity_type
        self.version = version
        msg = f"Emission factor not found: activity_type={activity_type}"
        if version:
            msg += f", version={version}"
        super().__init__(msg)


class InvalidActivityAmountError(CO2SystemError):
    def __init__(self, amount: float):
        self.amount = amount
        super().__init__(f"Invalid activity amount: {amount}. Must be >= 0.")


class MissingRequiredColumnError(CO2SystemError):
    def __init__(self, column: str):
        self.column = column
        super().__init__(f"Missing required column: {column}")


class ColumnTypeConversionError(CO2SystemError):
    def __init__(self, column: str, raw_value: str):
        self.column = column
        self.raw_value = raw_value
        super().__init__(
            f"Cannot convert '{raw_value}' in column '{column}' to number"
        )
