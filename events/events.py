from enum import StrEnum
import pandas as pd
from pydantic import BaseModel


# Definition of the different type of events
class EventType(StrEnum):
    DATA = "DATA"


class BaseEvent(BaseModel):
    event_type: EventType

    class Config:
        arbitrary_types_allowed = True


class DataEvent(BaseEvent):
    event_type: EventType = EventType.DATA
    symbol: str
    data: pd.Series
