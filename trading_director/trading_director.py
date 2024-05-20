import queue
import time
from typing import Any, Callable, Dict, Union

from data_provider.data_provider import DataProvider
from notifications.notifications import NotificationService
from order_executor.order_executor import OrderExecutor
from position_sizer.position_sizer import PositionSizer
from risk_manager.risk_manager import RiskManager
from signal_generator.interfaces.signal_generator_interface import ISignalGenerator

from events.events import (
    DataEvent,
    ExecutionEvent,
    OrderEvent,
    PlacePendingOrderEvent,
    SignalEvent,
    SizingEvent,
)
from utils.utils import Utils


T = Union[DataEvent, SignalEvent]


class TradingDirector:
    def __init__(
        self,
        events_queue: queue.Queue[Any],
        data_provider: DataProvider,
        signal_generator: ISignalGenerator,
        position_sizer: PositionSizer,
        risk_manager: RiskManager,
        order_executor: OrderExecutor,
        notification_service: NotificationService,
    ) -> None:
        self.events_queue = events_queue

        # References from the different modules
        self.data_provider = data_provider
        self.signal_generator = signal_generator
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.order_executor = order_executor
        self.notifications = notification_service

        # Trading controller
        self.continue_trading: bool = True

        # Creación del event handler
        self.event_handler: Dict[str, Callable[[T], None]] = {  # type: ignore
            "DATA": self._handle_data_event,
            "SIGNAL": self._handle_signal_event,
            "SIZING": self._handle_sizing_event,
            "ORDER": self._handle_order_event,
            "EXECUTION": self._handle_execution_event,
            "PENDING": self._handle_pending_order_event,
        }

    def _handle_data_event(self, event: DataEvent) -> None:
        """
        Handle the data event
        """
        print(
            f"[{Utils.dateprint()}] - DATA EVENT received for symbol: {event.symbol} - Last close price: {event.data.close}"  # type: ignore
        )
        self.signal_generator.generate_signal(event)  # type: ignore

    def _handle_signal_event(self, event: SignalEvent) -> None:
        """
        Handle the signal event
        """
        print(
            f"[{Utils.dateprint()}] - SIGNAL EVENT received for symbol: {event.symbol} - Signal: {event.signal} - Order: {event.target_order} - Price: {event.target_price}"
        )
        self.position_sizer.size_signal(event)

    def _handle_sizing_event(self, event: SizingEvent) -> None:
        """
        Handle the sizing event
        """
        print(
            f"[{Utils.dateprint()}] - SIZING EVENT received with volume {event.volume:.2f} for symbol: {event.symbol}"  # type: ignore
        )
        self.risk_manager.assess_order(event)

    def _handle_order_event(self, event: OrderEvent) -> None:
        """
        Handle the order event
        """
        print(
            f"[{Utils.dateprint()}] - ORDER EVENT for {event.signal} with volume {event.volume:.2f} for symbol: {event.symbol}"
        )
        self.order_executor.execute_order(event)

    def _handle_execution_event(self, event: ExecutionEvent) -> None:
        """_handle_execution_event _summary_

        Args:
            event (ExecutionEvent): _description_
        """
        print(
            f"[{Utils.dateprint()}] - Received EXECUTION EVENT for {event.signal} on {event.symbol} with volume {event.volume} at price {event.fill_price}"
        )
        self._process_execution_or_pending_events(event)

    def _handle_pending_order_event(self, event: PlacePendingOrderEvent) -> None:
        """_handle_pending_order_event _summary_

        Args:
            event (PlacePendingOrderEvent): _description_
        """
        print(
            f"[{Utils.dateprint()}] - Received PLACED PENDING ORDER EVENT with volume {event.volume} for {event.signal} {event.target_order} on {event.symbol} at price {event.target_price}"
        )
        self._process_execution_or_pending_events(event)

    def _process_execution_or_pending_events(
        self, event: Union[ExecutionEvent, PlacePendingOrderEvent]
    ) -> None:
        """
        Process the execution or pending order event
        """
        if isinstance(event, ExecutionEvent):
            self.notifications.send_notification(
                title=f"{event.symbol} - MARKET ORDER",
                message=f"Executed MARKET ORDER {event.signal} on {event.symbol} with volume {event.volume} at price {event.fill_price}",
            )
        elif isinstance(event, PlacePendingOrderEvent):  # type: ignore
            self.notifications.send_notification(
                title=f"{event.symbol} PENDING ORDER",
                message=f"PENDING ORDER placed {event.signal} on {event.symbol} with volume {event.volume} at price {event.target_price}",
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
