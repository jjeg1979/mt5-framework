from decimal import Decimal
from queue import Queue
from typing import Any
import MetaTrader5 as mt5
from data_provider.data_provider import DataProvider
from events.events import SignalEvent, SizingEvent

from position_sizer.interfaces.position_sizer_interface import IPositionSizer
from position_sizer.position_sizers.fixed_size_position_sizer import (
    FixedSizePositionSizer,
)
from position_sizer.position_sizers.min_size_position_sizer import MinSizePositionSizer
from position_sizer.position_sizers.risk_pct_position_sizer import RiskPctPositionSizer
from position_sizer.properties.position_sizer_properties import (
    BaseSizerProps,
    FixedSizingProps,
    MinSizingProps,
    RiskPctSizingProps,
)


class PositionSizer(IPositionSizer):
    def __init__(
        self,
        events_queue: Queue[Any],
        data_provider: DataProvider,
        sizing_properties: BaseSizerProps,
    ) -> None:  # type: ignore
        self.events_queue = events_queue
        self.data_provider = data_provider

        self.position_sizing_method = self._get_position_sizing_method(
            sizing_properties
        )

    def _get_position_sizing_method(
        self, sizing_properties: BaseSizerProps
    ) -> IPositionSizer:
        """
        Returns an instance of the adecuate PositionSizer as a function
        of the properties object passed

        Args:
            sizing_properties (Any): _description_

        Returns:
            IPositionSizer: _description_
        """
        if isinstance(sizing_properties, MinSizingProps):
            return MinSizePositionSizer()
        elif isinstance(sizing_properties, FixedSizingProps):
            return FixedSizePositionSizer(sizing_properties)
        elif isinstance(sizing_properties, RiskPctSizingProps):
            return RiskPctPositionSizer(sizing_properties)

        raise ValueError(
            f"Position sizer method not recognized. Please check the properties passed {sizing_properties}"
        )

    def _create_and_put_sizing_event(
        self, signal_event: SignalEvent, volume: Decimal
    ) -> None:
        """_create_and_put_sizing_event _summary_

        Args:
            signal_event (SignalEvent): _description_
            volume (Decimal): _description_
        """
        # Create sizing event from signal event and volume
        sizing_event: SizingEvent = SizingEvent(
            symbol=signal_event.symbol,
            signal=signal_event.signal,
            target_order=signal_event.target_order,
            target_price=signal_event.target_price,
            magic_number=signal_event.magic_number,
            sl=signal_event.sl,
            tp=signal_event.tp,
            volume=volume,
        )

        # Put sizing event in the events queue
        self.events_queue.put(sizing_event)

    def size_signal(self, signal_event: SignalEvent) -> None:  # type: ignore
        # Get the volume according to the sizing method
        volume = self.position_sizing_method.size_signal(
            signal_event, self.data_provider
        )  # Use the appropiate position sizing metho

        # Safety controls
        if volume < mt5.symbol_info(signal_event.symbol).volume_min:  # type: ignore
            print(
                f"ERROR. Volume calculated {volume} is lower than the minimum volume allowed {mt5.symbol_info(signal_event.symbol).volume_min} by symbol {signal_event.symbol}"  # type: ignore
            )  # type: ignore
            return
        # Put volume in a sizing event and add event to the events queue
        self._create_and_put_sizing_event(signal_event, volume)
