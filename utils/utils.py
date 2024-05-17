from decimal import Decimal

import MetaTrader5 as mt5


# Create a static method to convert currencies between each other
class Utils:
    def __init__(self):
        pass

    # Static method using @staticmethod decorator
    @staticmethod
    def convert_currency_amount_to_another_currency(
        amount: Decimal, from_currency: str, to_currency: str
    ) -> Decimal:
        all_fx_symbol = (
            "AUDCAD",
            "AUDCHF",
            "AUDJPY",
            "AUDNZD",
            "AUDUSD",
            "CADCHF",
            "CADJPY",
            "CHFJPY",
            "EURAUD",
            "EURCAD",
            "EURCHF",
            "EURGBP",
            "EURJPY",
            "EURNZD",
            "EURUSD",
            "EURSEK",
            "GBPAUD",
            "GBPCAD",
            "GBPCHF",
            "GBPJPY",
            "GBPNZD",
            "GBPUSD",
            "NZDCAD",
            "NZDCHF",
            "NZDJPY",
            "NZDUSD",
            "USDCAD",
            "USDCHF",
            "USDJPY",
            "USDSEK",
            "USDNOK",
            "SGDUSD",
            "SGDEUR",
            "SGDJPY",
            "XTIUSD",
            "SPA500",
        )

        # Convert currecies to uppercase (just in case)
        from_ccy = from_currency.upper()
        to_ccy = to_currency.upper()

        fx_symbol = [
            symbol
            for symbol in all_fx_symbol
            if from_ccy in symbol and to_ccy in symbol
        ][0]

        fx_symbol_base = fx_symbol[:3]

        # Retrieve the last data for the fx_symbol
        try:
            tick = mt5.symbol_info_tick(fx_symbol)  # type: ignore

            if tick is None:
                raise ValueError(
                    f"ERROR (Utils.convert_currency): Unable to retrieve the tick for {fx_symbol}. Please check available broker symbols"
                )
        except ValueError as e:
            print(
                f"ERROR (Utils.convert_currency): The latest tick from {fx_symbol} could not be retrieved. MT5 error: {mt5.last_error()}, Exception: {e}"  # type: ignore
            )  # type: ignore
            return Decimal(0.0)

        # Retrieve last available bid price for symbol
        last_price = Decimal(tick.bid)  # type: ignore

        # Convert the amount from the origin currency to the target currency
        converted_amount = (  # type: ignore
            amount / last_price if fx_symbol_base == to_ccy else amount * last_price
        )
        return Decimal(converted_amount)  # type: ignore
