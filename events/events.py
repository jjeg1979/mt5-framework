from enum import StrEnum
from decimal import Decimal

import pandas as pd
from pydantic import BaseModel
# from pandera.typing import Series


# Definition of the different type of events
class EventType(StrEnum):
    DATA = "DATA"
    SIGNAL = "SIGNAL"
    SIZING = "SIZING"
    ORDER = "ORDER"


class SignalType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class BaseEvent(BaseModel):
    event_type: EventType

    class Config:
        arbitrary_types_allowed = True


class DataEvent(BaseEvent):
    event_type: EventType = EventType.DATA
    symbol: str
    data: pd.Series  # type: ignore


class SignalEvent(BaseEvent):
    event_type: EventType = EventType.SIGNAL
    symbol: str
    signal: SignalType
    target_order: OrderType
    target_price: Decimal
    magic_number: int
    sl: Decimal
    tp: Decimal


class SizingEvent(BaseEvent):
    event_type: EventType = EventType.SIZING
    symbol: str
    signal: SignalType
    target_order: OrderType
    target_price: Decimal
    magic_number: int
    sl: Decimal
    tp: Decimal
    volume: Decimal


class OrderEvent(BaseEvent):
    event_type: EventType = EventType.ORDER
    symbol: str
    signal: SignalType
    target_order: OrderType
    target_price: Decimal
    magic_number: int
    sl: Decimal
    tp: Decimal
    volume: Decimal
