from queue import Queue
from typing import Any

import MetaTrader5 as mt5
import pandas as pd

from events.events import ExecutionEvent, OrderEvent, OrderType, SignalType
from portfolio.portfolio import Portfolio


class OrderExecutor:
    def __init__(self, events_queue: Queue[Any], portfolio: Portfolio) -> None:
        self.events_queue = events_queue
        self.portfolio = portfolio

    def execute_order(self, order_event: OrderEvent) -> None:
        if order_event.target_order == "MARKET":
            # Call the method that executes a market order
            pass
        elif order_event.target_order in (OrderType.LIMIT, OrderType.STOP):
            # Call the method that executes a limit order
            pass
        else:
            raise ValueError(f"Order type not supported: {order_event.target_order}")

    def _execute_market_order(self, order_event: OrderEvent) -> None:
        # Check if the order is BUY or SELL
        if order_event.signal == "BUY":
            # Buy order
            order_type = mt5.ORDER_TYPE_BUY
        elif order_event.signal == "SELL":
            # Sell order
            order_type = mt5.ORDER_TYPE_SELL
        else:
            raise ValueError(f"ORD EXEC: Order signal not valid: {order_event.signal}")

        # Market order request creation
        market_order_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_event.symbol,
            "volume": order_event.volume,
            "sl": order_event.sl,
            "tp": order_event.tp,
            "type": order_type,
            "deviation": 0,
            "magic": order_event.magic_number,
            "comment": "FWK Market Order",
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        # Send the trade request to be executed
        result = mt5.order_send(market_order_request)  # type: ignore

        # Check if the order was executed successfully
        if self._check_execution_status(result):
            print(
                f"ORD EXEC: Market Order {order_event.symbol} for {order_event.symbol} with {order_event.volume} lots executed successfully"
            )
            # Generate execution event and add to queue
            self._create_and_put_execution_event(result)
        else:
            # Order was not executed
            print(
                f"ORD EXEC: Error while executing the Market Order {order_event.signal} for {order_event.symbol}: {result.comment}"
            )

    def _create_and_put_execution_event(self, order_result: Any) -> None:
        # Get deal info, result of the order execution
        deal_code = order_result.deal
        deal = mt5.history_deals_get(ticket=deal_code)[0]  # type: ignore

        # Create the execution event
        execution_event = ExecutionEvent(
            symbol=order_result.request.symbol,
            signal=SignalType.BUY
            if deal.type == mt5.DEAL_TYPE_BUY
            else SignalType.SELL,  # type: ignore
            fill_price=deal.price,  # type: ignore
            fill_time=pd.to_datetime(deal.time_msc, unit="ms"),  # type: ignore
            volume=deal.volume,  # type: ignore
        )

        # Put the execution event in the queue
        self.events_queue.put(execution_event)

    def _check_execution_status(self, order_result: Any) -> bool:
        if order_result.retcode in (
            mt5.TRADE_RETCODE_DONE,
            mt5.TRADE_RETCODE_DONE_PARTIAL,
        ):
            return True
        return False
