from datetime import datetime
import queue
import time
from typing import Any, Callable, Dict, Union

from data_provider.data_provider import DataProvider
from position_sizer.position_sizer import PositionSizer
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator

from events.events import DataEvent, SignalEvent, SizingEvent


T = Union[DataEvent, SignalEvent]


class TradingDirector:
    def __init__(
        self,
        events_queue: queue.Queue[Any],
        data_provider: DataProvider,
        signal_generator: ISignalGenerator,
        position_sizer: PositionSizer,
    ) -> None:
        self.events_queue = events_queue

        # References from the different modules
        self.data_provider = data_provider
        self.signal_generator = signal_generator
        self.position_sizer = position_sizer

        # Trading controller
        self.continue_trading: bool = True

        # Creación del event handler
        self.event_handler: Dict[str, Callable[[T], None]] = {  # type: ignore
            "DATA": self._handle_data_event,
            "SIGNAL": self._handle_signal_event,
            "SIZING": self._handle_sizing_event,
        }

    def _dateprint(self) -> str:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

    def _handle_data_event(self, event: DataEvent) -> None:
        """
        Handle the data event
        """
        print(
            f"[{event.data.name}] - DATA EVENT received for symbol: {event.symbol} - Last close price: {event.data.close}"  # type: ignore
        )
        self.signal_generator.generate_signals(event)

    def _handle_signal_event(self, event: SignalEvent) -> None:
        """
        Handle the signal event
        """
        print(
            f"[{self._dateprint()}] - SIGNAL EVENT received for symbol: {event.symbol} - Signal: {event.signal} - Order: {event.target_order} - Price: {event.target_price}"
        )
        self.position_sizer.size_signal(event)

    def _handle_sizing_event(self, event: SizingEvent) -> None:
        """
        Handle the sizing event
        """
        print(
            f"[{self._dateprint()}] - SIZING EVENT received with volume {event.volume:.2f} for symbol: {event.symbol}"  # type: ignore
        )

    def execute(self) -> None:
        """
        Execute the main loop of the trading director
        """

        # Main loop definition
        while self.continue_trading:
            try:
                event = self.events_queue.get(block=False)
            except queue.Empty:
                self.data_provider.check_for_new_data()
            else:
                if event is not None:
                    handler = self.event_handler.get(event.event_type)
                    handler(event)  # type: ignore
                else:
                    self.continue_trading = False
                    print(
                        "ERROR: Null event received! Stopping the framework execution."
                    )

            time.sleep(0.01)

        print("END")
