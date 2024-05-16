from decimal import Decimal
import MetaTrader5 as mt5

from utils.utils import Utils
from data_provider.data_provider import DataProvider
from events.events import SignalEvent
from position_sizer.interfaces.position_sizer_interface import IPositionSizer
from position_sizer.properties.position_sizer_properties import RiskPctSizingProps


class RiskPctPositionSizer(IPositionSizer):
    def __init__(self, properties: RiskPctSizingProps):
        self.risk_pct = properties.risk_pct

    def size_signal(
        self, signal_event: SignalEvent, data_provider: DataProvider
    ) -> Decimal:
        # Return a fixed-size position
        # Check that the risk percentage is greater than 0
        if self.risk_pct <= Decimal(0.0):
            print(
                f"ERROR (FixedPctPositionSizer): The risk percentage {self.risk_pct} must be greater than 0"
            )
            return Decimal(0.0)
        # Check that the sl != 0
        if signal_event.sl <= Decimal(0.0):
            print(
                f"ERROR (FixedPctPositionSizer): The Stop Loss value {signal_event} is not valid"
            )
            return Decimal(0.0)
        # Access the account information (currency)
        account_info = mt5.account_info()  # type: ignore
        # Accces the symbol information (to be able to calculate the risk)
        symbol_info = mt5.symbol_info(signal_event.symbol)  # type: ignore

        # Retrieve the entry price (from the event type (MARKET or PENDING))

        if signal_event.target_order == "MARKET":
            # Get latest available market price (ASK or BID)
            last_tick = data_provider.get_lastest_tick(signal_event.symbol)  # type: ignore
            entry_price = (  # type: ignore
                last_tick["ask"] if signal_event.signal == "BUY" else last_tick["bid"]  # type: ignore
            )  # type: ignore
        # If LIMIT OR STOP, the entry price is the target price
        else:
            # Get the target price from the signal_event
            entry_price = signal_event.target_price

        # Get the values left for calculations
        equity = account_info.equity  # type: ignore
        # Get the minimum price change
        tick_size = symbol_info.trade_tick_size  # type: ignore
        # Get the minimum volume change
        volume_step = symbol_info.volume_step  # type: ignore
        # Get the account currency
        account_ccy = account_info.currency  # type: ignore
        # Get the symbol profit currency
        symbol_profit_ccy = symbol_info.currency_profit  # type: ignore
        # Contract amount for the current symbol (1 standard lot)
        contract_size = symbol_info.trade_contract_size  # type: ignore

        # Auxiliary calculations
        # Quantity earned or lost per lot and tick
        tick_value_profit_ccy = contract_size * tick_size  # type: ignore

        # Convert tick value in profit currency to account currency
        # Get the exchange rate between the account currency and the profit currency
        # If the account currency is the same as the profit currency, the exchange rate is 1
        tick_value_account_ccy: int = Utils.convert_currency_amount_to_another_currency(
            tick_value_profit_ccy,  # type: ignore
            symbol_profit_ccy,  # type: ignore
            account_ccy,  # type: ignore
        )

        # Calculate the position size
        # Get the distance in integer tick_size units
        try:
            price_distance_in_integer_ticksizes: int = int(
                abs((entry_price - signal_event.sl) / tick_size)  # type: ignore
            )  # type: ignore
            # Calculate the risk in the account currency
            monetary_risk = equity * self.risk_pct  # type: ignore

            # Calculate the position size
            volume = monetary_risk / (  # type: ignore
                price_distance_in_integer_ticksizes * tick_value_account_ccy
            )

            # Normalize the volume to the volume step
            volume = round(volume / volume_step) * volume_step  # type: ignore
        except ZeroDivisionError as e:
            print(
                f"ERROR (FixedPctPositionSizer): The position size could not be calculated. Exception: {e}"
            )
            return Decimal(0.0)

        return Decimal(volume)  # type: ignore
