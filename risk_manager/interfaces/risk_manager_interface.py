from decimal import Decimal
from typing import Protocol, Union

from events.events import SizingEvent


class IRiskManager(Protocol):
    def assess_order(self, sizing_event: SizingEvent) -> Union[Decimal, None]:
        ...
