from decimal import Decimal
from queue import Queue
from typing import Any
import MetaTrader5 as mt5
from data_provider.data_provider import DataProvider
from events.events import OrderEvent, SizingEvent
from portfolio.portfolio import Portfolio
from risk_manager.interfaces.risk_manager_interface import IRiskManager
from risk_manager.properties.risk_manager_properties import (
    BaseRiskProps,
    MaxLeverageFactorRiskProps,
)
from risk_manager.risk_managers.max_leverage_factor_risk_manager import (
    MaxLeverageFactorRiskManager,
)
from utils.utils import Utils


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

    def _compute_current_value_of_position_in_account_currency(self) -> Decimal:
        """
        Compute the current value of the positions in the account currency

        Returns:
            Decimal: _description_
        """
        # Gather current positions by the strategy
        current_positions = self.portfolio.get_strategy_open_positions()  # type: ignore

        # Calculate value of open positions
        total_value = Decimal(0)

        for position in current_positions:
            total_value += self._compute_value_of_position_in_account_currency(
                position.symbol,  # type: ignore
                position.volume,  # type: ignore
                position.position_type,  # type: ignore
            )

        return total_value  # type: ignore

    def _compute_value_of_position_in_account_currency(
        self, symbol: str, volume: Decimal, position_type: int
    ) -> Decimal:
        """
        Compute the value of the position in the account currency

        Returns:
            Decimal: _description_
        """
        # Get the symbol info
        symbol_info = mt5.symbol_info(symbol)  # type: ignore

        # Units operated volume in symbol units (base currency, barrels of oil, ounces of gold, etc)
        traded_units = volume * Decimal(str(symbol_info.trade_contract_size))  # type: ignore

        # Convert traded units to profit or quoted currency (USD for gold, oil, CHF for GBPCHF, EUR for DAX,....)
        value_traded_in_profit_ccy = traded_units * Decimal(
            self.data_provider.get_latest_tick(symbol)["bid"]
        )  # type: ignore

        # Convert value_traded_in_profit_ccy to account currency (MT5 broker account currency, USD, EUR, CHF, ...)
        value_traded_in_account_ccy = Utils.convert_currency_amount_to_another_currency(
            value_traded_in_profit_ccy,
            symbol_info.currency_profit,  # type: ignore
            mt5.account_info().currency,  # type: ignore
        )

        # Evaluate if the position is a buy or a sell
        if position_type == mt5.ORDER_TYPE_SELL:
            return -Decimal(value_traded_in_account_ccy)

        return Decimal(value_traded_in_account_ccy)

    def _create_and_put_order_event(
        self, sizing_event: SizingEvent, volume: Decimal
    ) -> None:
        """
        Create an OrderEvent and put it in the events queue

        Args:
            sizing_event (SizingEvent): _description_
            volume (Decimal): _description_
        """
        # Create the order event from sizing_event and volume
        order_event = OrderEvent(
            symbol=sizing_event.symbol,
            signal=sizing_event.signal,
            target_order=sizing_event.target_order,
            target_price=sizing_event.target_price,
            magic_number=sizing_event.magic_number,
            sl=sizing_event.sl,
            tp=sizing_event.tp,
            volume=volume,
        )

        # Put order event in the events queue
        self.events_queue.put(order_event)

    def assess_order(self, sizing_event: SizingEvent) -> None:
        """
        Assess if the order is compliant with the risk management
        strategy in place

        Args:
            sizing_event (SizingEvent): _description_
        """

        # Get value for all positions opened by the strategy in account currency
        current_position_value = (
            self._compute_current_value_of_position_in_account_currency()
        )

        # Get value of the new position in account currency
        position_type = (
            mt5.ORDER_TYPE_BUY if sizing_event.signal == "LONG" else mt5.ORDER_TYPE_SELL
        )  # type: ignore
        new_position_value = self._compute_value_of_position_in_account_currency(
            symbol=sizing_event.symbol,
            volume=sizing_event.volume,
            position_type=position_type,
        )

        # Get the new operation volume to be executed after being assessed by risk manager
        new_volume = self.risk_manager_method.assess_order(  # type: ignore
            sizing_event=sizing_event,
            current_positions_value_acc_ccy=current_position_value,  # type: ignore
            new_position_value_acc_ccy=new_position_value,  # type: ignore
        )

        # Evaluate new volume
        if new_volume > Decimal(0):
            # Put the new sizing event in the events queue
            self._create_and_put_order_event(sizing_event, new_volume)  # type: ignore
