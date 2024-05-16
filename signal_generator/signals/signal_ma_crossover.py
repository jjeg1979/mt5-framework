from decimal import Decimal
from queue import Queue
from typing import Any

from events.events import DataEvent, OrderType, SignalEvent, SignalType
from data_provider.data_provider import DataProvider
from portfolio.portfolio import Portfolio
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator


class SignalMACrossover(ISignalGenerator):
    def __init__(
        self,
        events_queue: Queue[Any],
        data_provider: DataProvider,
        portfolio: Portfolio,
        timeframe: str,
        fast_period: int,
        slow_period: int,
    ):
        self.events_queue = events_queue
        self.data_provider = data_provider
        self.portfolio = portfolio
        self.timeframe = timeframe
        self.fast_period = fast_period if fast_period > 1 else 2
        self.slow_period = slow_period if slow_period > 2 else 3

        if self.fast_period >= self.slow_period:
            raise ValueError(
                f"ERROR: The fast moving average {self.fast_period} should be lower than the slow moving average {self.slow_period}."
            )

    def _create_and_put_signal_event(
        self,
        symbol: str,
        signal: SignalType,
        target_order: OrderType,
        target_price: Decimal,
        magic_number: int,
        sl: Decimal,
        tp: Decimal,
    ) -> None:
        """
        Create and put a SignalEvent in the events_queue.
        """
        signal_event: SignalEvent = SignalEvent(
            symbol=symbol,
            signal=signal,
            target_order=target_order,
            target_price=target_price,
            magic_number=magic_number,
            sl=sl,
            tp=tp,
        )
        # Put signal event in the events_queue
        self.events_queue.put(signal_event)

    def generate_signals(self, data_event: DataEvent) -> None:
        """
        Generate signals based on moving average crossover.
        """

        # We need data
        symbol: str = data_event.symbol

        # Retrieve the needed data to calculate the moving averages
        bars = self.data_provider.get_latest_closed_bars(
            symbol, self.timeframe, self.slow_period
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

        if fast_ma > slow_ma:
            signal = "BUY"

        # Detect a selling signal
        elif slow_ma > fast_ma:
            signal = "SELL"
        else:
            signal = ""
        # if there is signal, genrate SignalEvent and
        # put it in the events_queue
        if signal != "":
            self._create_and_put_signal_event(
                symbol=symbol,
                signal=SignalType.BUY if signal.upper() == "BUY" else SignalType.SELL,
                target_order=OrderType.MARKET,
                target_price=Decimal("0.0"),
                magic_number=self.portfolio.magic,
                sl=Decimal("0.0"),
                tp=Decimal("0.0"),
            )

        print(signal)
