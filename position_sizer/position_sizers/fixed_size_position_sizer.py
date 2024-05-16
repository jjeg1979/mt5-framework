from decimal import Decimal

from data_provider.data_provider import DataProvider
from events.events import SignalEvent
from position_sizer.interfaces.position_sizer_interface import IPositionSizer
from position_sizer.properties.position_sizer_properties import FixedSizingProps


class FixedSizePositionSizer(IPositionSizer):
    def __init__(self, properties: FixedSizingProps):
        self.fixed_volume = properties.volume

    def size_signal(
        self, signal_event: SignalEvent, data_provider: DataProvider
    ) -> Decimal:
        # Return a fixed-size position
        if self.fixed_volume > Decimal(0.0):
            return Decimal(self.fixed_volume)  # type: ignore)
        return Decimal(0.0)
