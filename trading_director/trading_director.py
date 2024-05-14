from datetime import datetime
import queue
import time
from typing import Any, Callable, Dict, Union
from data_provider.data_provider import DataProvider
from events.events import DataEvent


class TradingDirector:
    def __init__(
        self, events_queue: queue.Queue[Any], data_provider: DataProvider
    ) -> None:
        self.events_queue = events_queue

        # References from the different modules
        self.data_provider = data_provider

        # Trading controller
        self.continue_trading: bool = True

        # Creación del event handler
        self.event_handler: Dict[str, Callable[[Union[DataEvent, Any]], None]] = {
            "DATA": self._handle_data_event,
        }

    def _dateprint(self) -> str:
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")[:-3]

    def _handle_data_event(self, event: DataEvent) -> None:
        """
        Handle the data event
        """
        print(
            f"[{event.data.name}] - Data event received for symbol: {event.symbol} - Last close price: {event.data.close}"  # type: ignore
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

            time.sleep(1)

        print("END")
