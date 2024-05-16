from decimal import Decimal
from pydantic import BaseModel


class BaseSizerProps(BaseModel):
    pass


class MinSizingProps(BaseSizerProps):
    pass


class FixedSizingProps(BaseSizerProps):
    volume: Decimal


class RiskPctSizingProps(BaseSizerProps):
    risk_pct: Decimal
