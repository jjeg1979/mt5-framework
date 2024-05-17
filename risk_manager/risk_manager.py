from queue import Queue
from typing import Any
from data_provider.data_provider import DataProvider
from portfolio.portfolio import Portfolio
from risk_manager.interfaces.risk_manager_interface import IRiskManager
from risk_manager.properties.risk_manager_properties import (
    BaseRiskProps,
    MaxLeverageFactorRiskProps,
)
from risk_manager.risk_managers.max_leverage_factor_risk_manager import (
    MaxLeverageFactorRiskManager,
)


class RiskManager(IRiskManager):
    def __init__(
        self,
        events_queue: Queue[Any],
        data_provider: DataProvider,
        portfolio: Portfolio,
        risk_properties: BaseRiskProps,
    ) -> None:
        self.events_queue = events_queue
        self.data_provider = data_provider
        self.portfolio = portfolio

        self.risk_manager_method = self._get_risk_manager_method(risk_properties)

    def _get_risk_manager_method(self, risk_properties: BaseRiskProps) -> IRiskManager:
        """
        Returns an instance of the adecuate RiskManager as a function
        of the properties object passed

        Args:
            risk_properties (BaseRiskProperties): _description_

        Returns:
            IRiskManager: _description_
        """
        if isinstance(risk_properties, MaxLeverageFactorRiskProps):
            return MaxLeverageFactorRiskManager(risk_properties)

        raise ValueError(
            f"ERROR: Risk manager method not recognized. Please check the properties passed {risk_properties}"
        )
