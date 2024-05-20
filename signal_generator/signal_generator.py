from queue import Queue
from typing import Any
from data_provider.data_provider import DataProvider
from events.events import DataEvent
from order_executor.order_executor import OrderExecutor
from portfolio.portfolio import Portfolio
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator
from signal_generator.properties.signal_generator_properties import (
    BaseSignalProps,
    MACrossoverProps,
)
from signal_generator.signals.signal_ma_crossover import SignalMACrossover


class SignalGenerator(ISignalGenerator):
    def __init__(
        self,
        events_queue: Queue[Any],
        data_provider: DataProvider,
        portfolio: Portfolio,
        order_executor: OrderExecutor,
        signal_properties: BaseSignalProps,
    ):
        self.events_queue = events_queue
        self.data_provider = data_provider
        self.portfolio = portfolio
        self.order_executor = order_executor

        self.signal_generator_method = self._get_signal_generator(
            signal_props=signal_properties
        )

    def _get_signal_generator(self, signal_props: BaseSignalProps) -> ISignalGenerator:
        """_get_signal_generator

        Args:
            signal_props (BaseSignalProps): _description_

        Returns:
            ISignalGenerator: _description_
        """
        if isinstance(signal_props, MACrossoverProps):
            return SignalMACrossover(
                properties=signal_props,
            )
        else:
            raise ValueError(f"ERROR: props type not supported: {signal_props}")

    def generate_signal(  # type: ignore
        self,
        data_event: DataEvent,
    ) -> None:
        """generate_signal

        Args:
            data_event (DataEvent): _description_

        """
        # Retrieve el SignalEvent using the adequate entry logic
        signal_event = self.signal_generator_method.generate_signal(  # noqa: E1111
            data_event=data_event,
            data_provider=self.data_provider,
            portfolio=self.portfolio,
            order_executor=self.order_executor,
        )

        if signal_event is not None:
            self.events_queue.put(signal_event)
