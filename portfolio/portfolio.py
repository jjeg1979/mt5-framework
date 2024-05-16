from typing import Tuple, Dict
import MetaTrader5 as mt5


class Portfolio:
    def __init__(self, magic_number: int):
        self.magic = magic_number

    def get_open_positions(self) -> Tuple[str, int]:
        return mt5.positions_get()  # type: ignore

    def get_strategy_open_positions(self) -> Tuple[str, int]:
        positions = []
        for position in self.get_open_positions():
            if position.magic == self.magic:  # type: ignore
                positions.append(position)

        return tuple(positions)  # type: ignore

    def get_number_of_open_positions_by_symbol(self, symbol: str) -> Dict[str, int]:
        positions_tuple = mt5.positions_get(symbol=symbol)  # type: ignore

        longs = 0
        shorts = 0

        for position in positions_tuple:  # type: ignore
            if position.type == mt5.ORDER_TYPE_BUY:
                longs += 1
            elif position.type == mt5.ORDER_TYPE_SELL:
                shorts += 1

        return {"LONG": longs, "SHORT": shorts, "TOTAL": longs + shorts}

    def get_number_of_strategy_open_positions_by_symbol(
        self, symbol: str
    ) -> Dict[str, int]:
        positions_tuple = mt5.positions_get(symbol=symbol)  # type: ignore

        longs = 0
        shorts = 0

        for position in positions_tuple:  # type: ignore
            if position.symbol == symbol:  # type: ignore
                if position.type == mt5.ORDER_TYPE_BUY:
                    longs += 1
                elif position.type == mt5.ORDER_TYPE_SELL:
                    shorts += 1

        return {"LONG": longs, "SHORT": shorts, "TOTAL": longs + shorts}
