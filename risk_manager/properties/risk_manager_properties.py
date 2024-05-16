from decimal import Decimal
from pydantic import BaseModel


class BaseRiskProps(BaseModel):
    pass


class MaxLeverageRiskProps(BaseRiskProps):
    max_leverage_factor: Decimal
