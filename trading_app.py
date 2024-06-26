from decimal import Decimal
from queue import Queue
from typing import Any

from decouple import config

from data_provider.data_provider import DataProvider
from notifications.notifications import (
    NotificationService,
    TelegramNotificationProperties,
)
from order_executor.order_executor import OrderExecutor
from platform_connector.platform_connector import PlatformConnector
from portfolio.portfolio import Portfolio
from position_sizer.position_sizer import PositionSizer
from position_sizer.properties.position_sizer_properties import (
    FixedSizingProps,
    # MinSizingProps,
)


from risk_manager.properties.risk_manager_properties import MaxLeverageFactorRiskProps
from risk_manager.risk_manager import RiskManager
from signal_generator.properties.signal_generator_properties import MACrossoverProps
from signal_generator.signal_generator import SignalGenerator
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
    magic_number = 12345
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

    portfolio = Portfolio(magic_number=magic_number)
    order_executor = OrderExecutor(events_queue=events_queue, portfolio=portfolio)

    signal_generator = SignalGenerator(
        events_queue=events_queue,
        data_provider=data_provider,
        portfolio=portfolio,
        order_executor=order_executor,
        signal_properties=MACrossoverProps(
            timeframe=timeframe,
            fast_period=fast_ma_pd,
            slow_period=slow_ma_pd,
        ),
    )

    sizing_properties = FixedSizingProps(volume=Decimal(1.0))

    position_sizer = PositionSizer(
        events_queue=events_queue,
        data_provider=data_provider,
        sizing_properties=sizing_properties,
    )

    risk_properties = MaxLeverageFactorRiskProps(max_leverage_factor=Decimal(5))

    risk_manager = RiskManager(
        events_queue=events_queue,
        data_provider=data_provider,
        portfolio=portfolio,
        risk_properties=risk_properties,
    )

    notifications = NotificationService(
        properties=TelegramNotificationProperties(
            token=config("TELEGRAM_API_TOKEN"),  # type: ignore
            chat_id=config("TELEGRAM_CHAT_ID"),  # type: ignore
        )
    )

    # Create the trading director and start the main loop
    trading_director: TradingDirector = TradingDirector(
        events_queue=events_queue,
        data_provider=data_provider,
        signal_generator=signal_generator,
        position_sizer=position_sizer,
        risk_manager=risk_manager,
        order_executor=order_executor,
        notification_service=notifications,
    )
    trading_director.execute()


if __name__ == "__main__":
    main()
