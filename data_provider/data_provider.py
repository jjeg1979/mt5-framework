from datetime import datetime
from queue import Queue
from typing import Dict, Union, List
from pandera.typing import Series
import pandas as pd
import MetaTrader5 as mt5

from events.events import DataEvent


class DataProvider:
    def __init__(
        self, events_queue: Queue[pd.DataFrame], symbol_list: List[str], timeframe: str
    ) -> None:
        self.events_queue = events_queue
        self.symbols = symbol_list
        self.timeframe = timeframe

        # Create a dict to store the time of the last bar seen of each symbol
        self.last_bar_datetime = {symbol: datetime.min for symbol in symbol_list}

    def _map_timeframes(self, timeframe: str) -> int:
        """
        Define a mapping to match the string timeframe
        with a valid MT5 TimeFrame
        """

        timeframe_mapping: Dict[str, int] = {
            "1min": mt5.TIMEFRAME_M1,
            "2min": mt5.TIMEFRAME_M2,
            "3min": mt5.TIMEFRAME_M3,
            "4min": mt5.TIMEFRAME_M4,
            "5min": mt5.TIMEFRAME_M5,
            "6min": mt5.TIMEFRAME_M6,
            "10min": mt5.TIMEFRAME_M10,
            "12min": mt5.TIMEFRAME_M12,
            "15min": mt5.TIMEFRAME_M15,
            "20min": mt5.TIMEFRAME_M20,
            "30min": mt5.TIMEFRAME_M30,
            "1h": mt5.TIMEFRAME_H1,
            "2h": mt5.TIMEFRAME_H2,
            "3h": mt5.TIMEFRAME_H3,
            "4h": mt5.TIMEFRAME_H4,
            "6h": mt5.TIMEFRAME_H6,
            "8h": mt5.TIMEFRAME_H8,
            "12h": mt5.TIMEFRAME_H12,
            "1d": mt5.TIMEFRAME_D1,
            "1w": mt5.TIMEFRAME_W1,
            "1M": mt5.TIMEFRAME_MN1,
        }
        try:
            return timeframe_mapping[timeframe]
        except Exception as e:
            print(f"INVALID TIMEFRAME {timeframe}! - Exception: {e}")
            return 0

    def get_latest_closed_bar(
        self, symbol: str, timeframe: str
    ) -> Union[Series[str], Series[int], Series[float], None]:
        """
            Get the data of the last closed bar/candle

        Args:
            symbol: str ->
            timeframe: str ->

        Returns:
            pd.Series ->

        """
        # Define parameters
        tf = self._map_timeframes(timeframe)
        from_position = 1
        num_bars = 1

        # Retrieve data from last candle
        try:
            bars_np_array = mt5.copy_rates_from_pos(symbol, tf, from_position, num_bars)  # type: ignore
            if bars_np_array is None:
                print(
                    f"Symbol {symbol} does not exist or its data cannot be retrieved!"
                )

                # Return empty series
                return pd.Series()  # type: ignore

            bars = pd.DataFrame(bars_np_array)  # type: ignore
            # Convert the time column to datetime format
            bars["time"] = pd.to_datetime(bars["time"], unit="s")
            bars.set_index("time", inplace=True)

            # Change col names and reorganize
            bars.rename(
                columns={"tick_volume": "tickvol", "real_volume": "vol"},
                inplace=True,
            )
            bars = bars[["open", "high", "low", "close", "tickvol", "vol", "spread"]]
        except Exception as e:
            print(
                f"Unable to retrieve the last candle data from {symbol} {timeframe} - MT5 Error: {mt5.last_error()}, exception: {e}"  # type: ignore
            )
            return pd.Series()  # type: ignore
        else:
            if bars.empty:
                # Return empty series
                return pd.Series()  # type: ignore
            return bars.iloc[-1]  # type: ignore

    def get_latest_closed_bars(
        self, symbol: str, timeframe: str, num_bars: int = 1
    ) -> pd.DataFrame:
        """
            Get the data of the last closed bars/candles

        Args:
            symbol: str ->
            timeframe: str ->
            num_bars: int ->

        Returns:
            pd.DataFrame ->

        """
        # Define parameters
        tf = self._map_timeframes(timeframe)
        from_position = 1
        bars_count = num_bars if num_bars > 0 else 1

        # Retrieve data from last candle
        try:
            bars_np_array = mt5.copy_rates_from_pos(  # type: ignore
                symbol, tf, from_position, bars_count
            )
            if bars_np_array is None:
                print(
                    f"Symbol {symbol} does not exist or its data cannot be retrieved!"
                )

                # Return empty DataFrame
                return pd.DataFrame()

            bars = pd.DataFrame(bars_np_array)  # type: ignore
            # Convert the time column to datetime format
            bars["time"] = pd.to_datetime(bars["time"], unit="s")
            bars.set_index("time", inplace=True)

            # Change col names and reorganize
            bars.rename(
                columns={"tick_volume": "tickvol", "real_volume": "vol"},
                inplace=True,
            )
            bars = bars[["open", "high", "low", "close", "tickvol", "vol", "spread"]]
        except Exception as e:
            print(
                f"Unable to retrieve the last {num_bars} candles data from {symbol} {timeframe} - MT5 Error: {mt5.last_error()}, exception: {e}"  # type: ignore
            )
            return pd.DataFrame()
        else:
            if bars.empty:
                # Return empty DataFrame
                return pd.DataFrame()
            # If everything ok, return the datarame with eh num_bars
            return bars

    def get_latest_tick(self, symbol: str) -> Dict[str, Union[int, float]]:
        """
        Gets the data from the last tick for symbol
        """
        try:
            tick = mt5.symbol_info_tick(symbol)  # type: ignore
            if tick is None:
                print(
                    f"Unable to retrieve last tick data of {symbol}! - MT5 error: {mt5.last_error()}"  # type: ignore
                )
                return {}
        except Exception as e:
            print(
                f"Something went wrong retrieving data from {symbol} - MT5 error: {mt5.last_error()}, exception: {e}"  # type: ignore
            )
            return {}

        else:
            return tick._asdict()  # type: ignore

    def check_for_new_data(self) -> None:
        # 1) Check if there is new data

        for symbol in self.symbols:
            # Acceder últimos datos disponibles
            latest_bar = self.get_latest_closed_bar(symbol, self.timeframe)  # type: ignore

            if latest_bar is None:
                continue

            # 2) If new data, create DataEvent
            if (
                not latest_bar.empty
                and latest_bar.name > self.last_bar_datetime[symbol]  # type: ignore
            ):
                # Update the last retrieved candle
                self.last_bar_datetime[symbol] = latest_bar.name  # type: ignore

                # Create DataEvent
                data_event = DataEvent(symbol=symbol, data=latest_bar)

                # 3) Add event to EventQueue
                self.events_queue.put(data_event)  # type: ignore
