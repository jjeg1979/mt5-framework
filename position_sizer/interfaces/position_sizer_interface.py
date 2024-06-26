from decimal import Decimal
from typing import Protocol, Union

from data_provider.data_provider import DataProvider
from events.events import SignalEvent


class IPositionSizer(Protocol):
    def size_signal(
        self, signal_event: SignalEvent, data_provider: DataProvider
    ) -> Union[Decimal, None]:
        ...
