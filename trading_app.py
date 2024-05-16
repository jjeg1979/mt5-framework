from queue import Queue
from typing import Any

from platform_connector.platform_connector import PlatformConnector
from data_provider.data_provider import DataProvider
from position_sizer.position_sizer import PositionSizer
from position_sizer.properties.position_sizer_properties import (
    MinSizingProps,
)
from trading_director.trading_director import TradingDirector

from signal_generator.signals.signal_ma_crossover import SignalMACrossover


def main() -> None:
    # Definición de variables necesarias para la estrategia
    symbols = [
        "EURUSD",
        "USDJPY",
        "USDSGD",
        "EURGBP",
        "XAUUSD",
        "SP500",
        "XTIUSD",
        "GBPUSD",
        "USDCHF",
        "GBPJPY",
        "NDX",
        "SPA35",
    ]
    timeframe = "1min"
    slow_ma_pd = 50
    fast_ma_pd = 25

    # Create main events queue
    events_queue: Queue[Any] = Queue()

    # Create main modules for the framework
    # connect: PlatformConnector = PlatformConnector(symbol_list=symbols)
    PlatformConnector(symbol_list=symbols)

    data_provider: DataProvider = DataProvider(
        events_queue=events_queue, symbol_list=symbols, timeframe=timeframe
    )

    signal_generator = SignalMACrossover(
        events_queue, data_provider, timeframe, fast_ma_pd, slow_ma_pd
    )

    sizing_properties = MinSizingProps()

    position_sizer = PositionSizer(
        events_queue=events_queue,
        data_provider=data_provider,
        sizing_properties=sizing_properties,
    )

    # Create the trading director and start the main loop
    trading_director: TradingDirector = TradingDirector(
        events_queue=events_queue,
        data_provider=data_provider,
        signal_generator=signal_generator,
        position_sizer=position_sizer,
    )
    trading_director.execute()


if __name__ == "__main__":
    main()
