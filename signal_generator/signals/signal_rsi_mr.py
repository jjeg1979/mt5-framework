from decimal import Decimal

import pandas as pd
import numpy as np

import MetaTrader5 as mt5

from events.events import DataEvent, OrderType, SignalEvent, SignalType
from data_provider.data_provider import DataProvider
from order_executor.order_executor import OrderExecutor
from portfolio.portfolio import Portfolio
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator
from signal_generator.properties.signal_generator_properties import RSIProps


class SignalRSI(ISignalGenerator):
    def __init__(
        self,
        properties: RSIProps,
    ):
        """Initializes the RSI Mean Reversion object.

        Args:
            properties (RSIMProps): The properties object containing the RSI Mean Reversion parameters.

        Raises:
            ValueError: If the RSI period is less than 2.
        """
        self.timeframe = properties.timeframe
        self.rsi_period = properties.rsi_period if properties.rsi_period > 2 else 2

        if properties.rsi_upper > 100 or properties.rsi_upper < 0:
            self.rsi_upper = 70
        else:
            self.rsi_upper = properties.rsi_upper

        if properties.rsi_lower > 100 or properties.rsi_lower < 0:
            self.rsi_lower = 30
        else:
            self.rsi_lower = properties.rsi_lower

        if self.rsi_lower >= self.rsi_upper:
            raise ValueError(
                f"ERROR: The upper level {self.rsi_upper} must be greater than the lower level {self.rsi_lower} for the entry signals calculation."
            )

        if properties.sl_points > 0:
            self.sl_points = properties.sl_points
        else:
            self.sl_points = 0

        if properties.tp_points > 0:
            self.tp_points = properties.tp_points
        else:
            self.tp_points = 0

    def compute_rsi(self, prices: pd.Series) -> float:  # type: ignore
        """Computes the Relative Strength Index (RSI) of the given prices.

        Args:
            prices (pd.Series): The prices to calculate the RSI.

        Returns:
            float: The RSI value.
        """
        deltas = pd.Series(np.diff(prices))  # type: ignore
        gains = pd.Series(np.where(deltas > 0, deltas, 0))  # type: ignore
        losses = pd.Series(np.where(deltas < 0, -deltas, 0))  # type: ignore

        average_gain = np.mean(gains[-self.rsi_period :])  # type: ignore  # noqa: E203
        average_loss = np.mean(losses[self.rsi_period :])  # type: ignore  # noqa: E203

        rs = average_gain / average_loss if average_loss > 0 else 0
        rsi = 100 - (100 / (1 + rs))
        return rsi  # type: ignore

    def generate_signal(
        self,
        data_event: DataEvent,
        data_provider: DataProvider,
        portfolio: Portfolio,
        order_executor: OrderExecutor,
    ) -> SignalEvent | None:  # type: ignore
        """
        Generate signals based on the RSI Mean Reversion strategy.

        Args:
            data_event (DataEvent): The data event.
            data_provider (DataProvider): The data provider.
            portfolio (Portfolio): The portfolio.
            order_executor (OrderExecutor): The order executor.
        """

        # We need data
        symbol: str = data_event.symbol

        # Retrieve the needed data to calculate the RSI
        bars = data_provider.get_latest_closed_bars(
            symbol, self.timeframe, self.rsi_period + 1
        )

        # Calculate the RSI for the last bars
        rsi = self.compute_rsi(bars["close"])  # type: ignore

        # Retrieve the open positions by this strategy in the symbol
        open_positions = portfolio.get_number_of_strategy_open_positions_by_symbol(
            symbol
        )

        # Take last price to calculate SL and TP
        last_tick = data_provider.get_latest_tick(symbol)
        points = mt5.symbol_info(symbol).point  # type: ignore

        # Detect a buying singal
        if open_positions["LONG"] == 0 and rsi < self.rsi_lower:
            # Check if there are short positions open
            # TODO: Send a closing event so Trading Director handles it and closes the position (FIFO queue allows for correct order execution of events)
            if open_positions["SHORT"] > 0:
                # We have a buying signal, but we have sell option. We must close the sell before opening a buy
                order_executor.close_strategy_short_positions_by_symbol(symbol)
            signal = "BUY"
            sl = (
                float(last_tick["ask"] - self.sl_points * points)  # type: ignore
                if self.sl_points > 0
                else 0
            )
            tp = (
                float(last_tick["ask"] + self.tp_points * points)  # type: ignore
                if self.tp_points > 0
                else 0
            )

        # Detect a selling signal
        elif open_positions["SHORT"] == 0 and rsi > self.rsi_upper:
            # Check if there are long positions open
            if open_positions["LONG"] > 0:
                # We have a selling signal, but we have buy option. We must close the buy before opening a sell
                order_executor.close_strategy_long_positions_by_symbol(symbol)
            signal = "SELL"
            sl = (
                float(last_tick["bid"] + self.sl_points * points)  # type: ignore
                if self.sl_points > 0
                else 0
            )
            tp = (
                float(last_tick["bid"] - self.tp_points * points)  # type: ignore
                if self.tp_points > 0
                else 0
            )
        else:
            signal = ""

        # if there is signal, genrate SignalEvent and
        # put it in the events_queue
        if signal != "":
            signal_event: SignalEvent = SignalEvent(
                symbol=symbol,
                signal=SignalType.BUY if signal == "BUY" else SignalType.SELL,
                target_order=OrderType.MARKET,
                target_price=Decimal(0.0),
                magic_number=portfolio.magic,
                sl=Decimal(sl),
                tp=Decimal(tp),
            )
            return signal_event
        return None
