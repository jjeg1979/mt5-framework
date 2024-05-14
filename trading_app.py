from queue import Queue
import pandas as pd

from platform_connector.platform_connector import PlatformConnector
from data_provider.data_provider import DataProvider
from trading_director.trading_director import TradingDirector


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

    # Create main events queue
    events_queue: Queue[pd.DataFrame] = Queue()

    # Create main modules for the framework
    # connect: PlatformConnector = PlatformConnector(symbol_list=symbols)
    PlatformConnector(symbol_list=symbols)
    data_provider: DataProvider = DataProvider(
        events_queue=events_queue, symbol_list=symbols, timeframe=timeframe
    )

    # Create the trading director and start the main loop
    trading_director: TradingDirector = TradingDirector(
        events_queue=events_queue, data_provider=data_provider
    )
    trading_director.execute()


if __name__ == "__main__":
    main()
