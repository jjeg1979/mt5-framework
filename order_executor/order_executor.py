from queue import Queue
from typing import Any, Dict

import MetaTrader5 as mt5
import pandas as pd

from events.events import (
    ExecutionEvent,
    PlacePendingOrderEvent,
    OrderEvent,
    OrderType,
    SignalType,
)
from portfolio.portfolio import Portfolio


class OrderExecutor:
    def __init__(self, events_queue: Queue[Any], portfolio: Portfolio) -> None:
        self.events_queue = events_queue
        self.portfolio = portfolio

    def execute_order(self, order_event: OrderEvent) -> None:
        if order_event.target_order == "MARKET":
            # Call the method that executes a market order
            self._execute_market_order(order_event)
        elif order_event.target_order in (OrderType.LIMIT, OrderType.STOP):
            # Call the method that executes a limit order
            self._send_pending_order(order_event)
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
            "volume": float(order_event.volume),
            "sl": float(order_event.sl),
            "tp": float(order_event.tp),
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
                f"ORD EXEC: Market Order {order_event.signal} {order_event.target_order} for {order_event.symbol} with {order_event.volume} lots executed successfully"
            )
            # Generate execution event and add to queue
            self._create_and_put_execution_event(result)
        else:
            # Order was not executed
            print(
                f"ORD EXEC: Error while executing the Market Order {order_event.signal} for {order_event.symbol}: {result.comment}"
            )

    def _send_pending_order(self, order_event: OrderEvent) -> None:
        # Check if the order is STOP or LIMIT
        if order_event.target_order == OrderType.STOP:
            # Stop order
            order_type = (
                mt5.ORDER_TYPE_BUY_STOP
                if order_event.signal == "BUY"
                else mt5.ORDER_TYPE_SELL_STOP
            )
        elif order_event.target_order == OrderType.LIMIT:
            # Limit order
            order_type = (
                mt5.ORDER_TYPE_BUY_LIMIT
                if order_event.signal == "BUY"
                else mt5.ORDER_TYPE_SELL_LIMIT
            )
        else:
            raise ValueError(
                f"ORD EXEC: Order type not valid: {order_event.target_order}"
            )

        # Pending order request creation
        pending_order_request = {  # type: ignore
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": order_event.symbol,
            "volume": float(order_event.volume),
            "price": float(order_event.target_price),
            "sl": float(order_event.sl),
            "tp": float(order_event.tp),
            "type": order_type,
            "deviation": 0,
            "magic": order_event.magic_number,
            "comment": "FWK Pending Order",
            "type_filling": mt5.ORDER_FILLING_FOK,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        # Send the trade request to put the pending order
        result = mt5.order_send(pending_order_request)  # type: ignore

        # Check if the order was executed successfully
        if self._check_execution_status(result):
            print(
                f"ORD EXEC: Pending Order {order_event.signal} {order_event.target_order} for {order_event.symbol} with {order_event.volume} lots sent at {order_event.target_price} successfully"
            )
            # Place the specific pending order event in the queue
            self._create_and_put_placed_pending_order_event(order_event)
        else:
            # Order was not executed
            print(
                f"ORD EXEC: Error while executing the Pending Order {order_event.signal} for {order_event.symbol}: {result.comment}"
            )

    def close_position_by_ticket(self, ticket: int) -> None:
        # Access the position by its ticket
        position = mt5.positions_get(ticket=ticket)[0]  # type: ignore

        # Verifiy that the position exists
        if position is None:
            print(f"ORD EXEC: Position with ticket {ticket} not found")
            return

        # Create the trade request to close the position
        close_request: Dict[str, Any] = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL
            if position.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }

        # Send the trade request to close the position
        result = mt5.order_send(close_request)  # type: ignore

        # Check if the order was executed successfully
        if self._check_execution_status(result):
            print(
                f"ORD EXEC: Position with ticket {ticket} for {position.symbol} with volume {position.volume} closed successfully"
            )
            # Generate execution event and add to queue
            self._create_and_put_execution_event(result)
        else:
            # Order was not executed
            print(
                f"ORD EXEC: Error while closing the position {ticket} for {position.symbol} and volume {position.volume}: {result.comment}"
            )

    def close_strategy_long_positions_by_symbol(self, symbol: str) -> None:
        # Get the open positions for the strategy
        positions = self.portfolio.get_strategy_open_positions()  # type: ignore

        # Filter positions by symbol and direction and close
        for position in positions:  # type: ignore
            if position.symbol == symbol and position.signal == mt5.ORDER_TYPE_BUY:  # type: ignore
                self.close_position_by_ticket(position.ticket)  # type: ignore

    def close_strategy_short_positions_by_symbol(self, symbol: str) -> None:
        # Get the open positions for the strategy
        positions = self.portfolio.get_strategy_open_positions()  # type: ignore

        # Filter positions by symbol and direction and close
        for position in positions:  # type: ignore
            if position.symbol == symbol and position.signal == mt5.ORDER_TYPE_SELL:  # type: ignore
                self.close_position_by_ticket(position.ticket)  # type: ignore

    def _create_and_put_placed_pending_order_event(
        self, order_event: OrderEvent
    ) -> None:
        # Create the placed pending order event
        placed_pending_order_event = PlacePendingOrderEvent(
            symbol=order_event.symbol,
            signal=order_event.signal,
            target_order=order_event.target_order,
            target_price=order_event.target_price,
            magic_number=order_event.magic_number,
            sl=order_event.sl,
            tp=order_event.tp,
            volume=order_event.volume,
        )

        # Put the event in the queue
        self.events_queue.put(placed_pending_order_event)

    def cancel_pending_order_by_ticket(self, ticket: int) -> None:
        # Get the information of the pending order
        order = mt5.orders_get(ticket=ticket)[0]  # type: ignore

        # Check if the pending order exists
        if order is None:
            print(f"ORD EXEC: Pending order with ticket {ticket} not found")
            return

        # Create the trade request to cancel the pending order
        cancel_request: Dict[str, Any] = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": order.ticket,
            "symbol": order.symbol,
        }

        # Send the trade request to cancel the pending order
        result = mt5.order_send(cancel_request)  # type: ignore

        # Check if the order was executed successfully
        if self._check_execution_status(result):
            print(
                f"ORD EXEC: Pending order with ticket {ticket} for {order.symbol} and volume {order.volume_initial} cancelled successfully"
            )
        else:
            # Order was not executed
            print(
                f"ORD EXEC: Error while cancelling the pending order {ticket} for {order.symbol} and volume {order.volume_initial}: {result.comment}"
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
