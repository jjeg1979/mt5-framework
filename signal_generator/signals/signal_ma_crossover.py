from decimal import Decimal
from typing import Any

from events.events import DataEvent, OrderType, SignalEvent, SignalType
from data_provider.data_provider import DataProvider
from order_executor.order_executor import OrderExecutor
from portfolio.portfolio import Portfolio
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator
from signal_generator.properties.signal_generator_properties import MACrossoverProps


class SignalMACrossover(ISignalGenerator):
    def __init__(
        self,
        properties: MACrossoverProps,
    ):
        self.timeframe = properties.timeframe
        self.fast_period = properties.fast_period if properties.fast_period > 1 else 2
        self.slow_period = properties.slow_period if properties.slow_period > 2 else 3

        if self.fast_period >= self.slow_period:
            raise ValueError(
                f"ERROR: The fast moving average {self.fast_period} should be lower than the slow moving average {self.slow_period}."
            )

    def generate_signals(
        self,
        data_event: DataEvent,
        data_provider: DataProvider,
        portfolio: Portfolio,
        order_executor: OrderExecutor,
    ) -> SignalEvent | None:  # type: ignore
        """
        Generate signals based on moving average crossover.
        """

        # We need data
        symbol: str = data_event.symbol

        # Retrieve the needed data to calculate the moving averages
        bars = data_provider.get_latest_closed_bars(
            symbol, self.timeframe, self.slow_period
        )

        # Retrieve the open positions by this strategy in the symbol
        open_positions = portfolio.get_number_of_strategy_open_positions_by_symbol(
            symbol
        )

        # Calculate the moving averages
        fast_ma: Any = (
            # bars.close.rolling(window=self.fast_period).mean().iloc[-1].values
            bars["close"][-self.fast_period :].mean()  # noqa: E203
        )  # type: ignore
        slow_ma: Any = (
            # bars.close.rolling(window=self.slow_period).mean().iloc[-1]
            bars["close"].mean()
        )  # type: ignore

        # Detect a buying singal
        if open_positions["LONG"] == 0 and fast_ma > slow_ma:
            # Check if there are short positions open
            # TODO: Send a closing event so Trading Director handles it and closes the position (FIFO queue allows for correct order execution of events)
            if open_positions["SHORT"] > 0:
                # We have a buying signal, but we have sell option. We must close the sell before opening a buy
                order_executor.close_strategy_short_positions_by_symbol(symbol)
            signal = "BUY"

        # Detect a selling signal
        elif open_positions["SHORT"] == 0 and slow_ma > fast_ma:
            # Check if there are long positions open
            if open_positions["LONG"] > 0:
                # We have a selling signal, but we have buy option. We must close the buy before opening a sell
                order_executor.close_strategy_long_positions_by_symbol(symbol)
            signal = "SELL"
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
                sl=Decimal(0.0),
                tp=Decimal(0.0),
            )
            return signal_event
        return None
