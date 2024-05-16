from decimal import Decimal
import MetaTrader5 as mt5

from data_provider.data_provider import DataProvider
from events.events import SignalEvent
from position_sizer.interfaces.position_sizer_interface import IPositionSizer


class MinSizePositionSizer(IPositionSizer):
    def size_signal(
        self, signal_event: SignalEvent, data_provider: DataProvider
    ) -> Decimal:
        symbol = signal_event.symbol
        volume: float = mt5.symbol_info(symbol).volume_min  # type: ignore

        if volume is not None:
            return Decimal(volume)  # type: ignore

        print(
            f"ERROR (MinSizePositionSizer): Could not determine minimum volume for {symbol}"
        )
        return Decimal("0.0")
