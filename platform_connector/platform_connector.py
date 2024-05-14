from typing import List, Dict
from decouple import config
import MetaTrader5 as mt5


class PlatformConnector:
    def __init__(self, symbol_list: List[str]) -> None:
        # Cargamos los valores del archivo .env
        self.path: str = config("MT5_PATH")  # type: ignore
        self.login: int = int(config("MT5_LOGIN"))  # type: ignore
        self.password: str = config("MT5_PASSWORD")  # type: ignore
        self.server: str = config("MT5_SERVER")  # type: ignore
        self.timeout: int = int(config("MT5_TIMEOUT"))  # type: ignore
        self.portable: bool = True if config("MT5_PORTABLE") == "True" else False

        # Initialize the platform
        self._initialize_platform()

        # Check the account type
        self._live_account_warning()

        # Print accout info
        self._print_account_info()

        # Check algorithmic trading
        self._check_algo_trading_enabled()

        # Add symbols to MarketWatch
        self._add_symbols_to_marketwatch(symbol_list)

    def _initialize_platform(self) -> None:
        """
        Initializes the MT5 platform.

        Raises:
            Exception: If there is any error while initializing the platform.

        Returns:
            None
        """

        if mt5.initialize(  # type: ignore
            path=self.path,
            login=self.login,
            password=self.password,
            server=self.server,
            timeout=self.timeout,
            portable=self.portable,
        ):
            print("La plataforma MT5 se ha lanzado con éxito!!!!")
        else:
            raise ValueError(
                f"Ha ocurrido un error al inicializar la plataforma MT5: {mt5.last_error()}"  # type: ignore
            )

    def _live_account_warning(self) -> None:
        """
        Checks the account type launched

        Raises:
            Exception: If the user aborts the execution

        Returns:
            None
        """
        # Recuperamos el objeto de tipo AccountInfo
        account_info = mt5.account_info()  # type: ignore
        if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO:
            print("Cuenta de tipo DEMO detectada")
        elif account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_REAL:
            if (
                not input(
                    "ALERTA! Cuenta de tipo REAL detectada. Capital en riesgo. ¿Deseas continuar? (y/n): "
                ).lower()
                == "y"
            ):
                mt5.shutdown()  # type: ignore
                raise ValueError("Usuario ha decidido DETENER el programa")  # type: ignore
        else:
            print("Cuenta de tipo CONCURSO detectada")

    def _check_algo_trading_enabled(self) -> None:
        """
        Checks whether the algorithmic trading is enabled

        Raises:
            ValueError: If the algo trading is not enabled

        Returns:
            None
        """
        terminal_info = mt5.terminal_info()  # type: ignore
        if not terminal_info.trade_allowed:
            raise ValueError(
                "El trading algoritmico está desactivado. Por favor, actívalo MANUALMENTE!"
            )

    def _add_symbols_to_marketwatch(self, symbols: List[str]) -> None:
        """
        Adds the symbols to market watch

        Args:
            symbols: List[str] List of symbols to add to market watch

        Returns:
            None
        """

        # 1) Check if the symbol is already visible in the Market Watch
        # 2) If it is not, we will add it to the Market Watch
        for symbol in symbols:
            if mt5.symbol_info(symbol) is None:  # type: ignore
                print(
                    f"No se ha podido añadir el símbol {symbol} al MarketWatch: {mt5.last_error()}"  # type: ignore
                )
                continue

            if not mt5.symbol_info(symbol).visible:  # type: ignore
                if not mt5.symbol_select(symbol, True):  # type: ignore
                    print(
                        f"No se ha podido añadir el símbol {symbol} al MarketWatch: {mt5.last_error()}"  # type: ignore
                    )
                else:
                    print(f"Símbolo {symbol} se ha añadido con éxito al MarketWatch!")
            else:
                print(f"El símbolo {symbol} ya estaba en el MarketWatch.")

    def _print_account_info(self) -> None:
        """
        Print information of the trading account
        """

        # Retrieve an object of account info type
        account_info: Dict[str, str] = mt5.account_info()._asdict()  # type: ignore
        # spacing: int = 35
        # fill_line: str = "-" * spacing
        # end_line: str = "|"
        header = "+--------------- Trading Account information ---------------+"
        footer = "+-----------------------------------------------------------+"

        print(header)
        print(f"| - Account ID: {account_info['login']}")
        print(f"| - Trader name: {account_info['name']}")
        print(f"| - Broker: {account_info['company']}")
        print(f"| - Server: {account_info['server']}")
        print(f"| - Leverage: {account_info['leverage']}")
        print(f"| - Account currency: {account_info['currency']}")
        print(f"| - Account balance: {account_info['balance']}")
        print(footer)
