"""
Order placement logic for the trading bot.

Provides high-level functions for placing and managing orders,
with proper validation, logging, and error handling.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceFuturesClient, BinanceAPIError, BinanceClientError
from .logging_config import get_logger
from .validators import (
    OrderParams, OrderSide, OrderType, TimeInForce,
    validate_order_params, ValidationError
)

logger = get_logger()


@dataclass
class OrderResult:
    """Result of an order operation."""
    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    quantity: Optional[str] = None
    executed_qty: Optional[str] = None
    price: Optional[str] = None
    avg_price: Optional[str] = None
    time_in_force: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    def __str__(self) -> str:
        if self.success:
            return (
                f"\n{'='*50}\n"
                f"✅ ORDER PLACED SUCCESSFULLY\n"
                f"{'='*50}\n"
                f"Order ID      : {self.order_id}\n"
                f"Client ID     : {self.client_order_id}\n"
                f"Symbol        : {self.symbol}\n"
                f"Side          : {self.side}\n"
                f"Type          : {self.order_type}\n"
                f"Status        : {self.status}\n"
                f"Quantity      : {self.quantity}\n"
                f"Executed Qty  : {self.executed_qty}\n"
                f"Price         : {self.price or 'MARKET'}\n"
                f"Avg Price     : {self.avg_price or 'N/A'}\n"
                f"Time in Force : {self.time_in_force or 'N/A'}\n"
                f"{'='*50}"
            )
        else:
            return (
                f"\n{'='*50}\n"
                f"❌ ORDER FAILED\n"
                f"{'='*50}\n"
                f"Error: {self.error_message}\n"
                f"{'='*50}"
            )


def format_order_request_summary(params: OrderParams) -> str:
    """
    Format order request summary for display.
    
    Args:
        params: Validated order parameters
    
    Returns:
        Formatted summary string
    """
    summary = (
        f"\n{'='*50}\n"
        f"📋 ORDER REQUEST SUMMARY\n"
        f"{'='*50}\n"
        f"Symbol        : {params.symbol}\n"
        f"Side          : {params.side.value}\n"
        f"Type          : {params.order_type.value}\n"
        f"Quantity      : {params.quantity}\n"
    )
    
    if params.price:
        summary += f"Price         : {params.price}\n"
    
    if params.stop_price:
        summary += f"Stop Price    : {params.stop_price}\n"
    
    if params.time_in_force:
        summary += f"Time in Force : {params.time_in_force.value}\n"
    
    summary += f"{'='*50}"
    
    return summary


def place_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
    time_in_force: Optional[str] = None
) -> OrderResult:
    """
    Place an order with full validation and error handling.
    
    Args:
        client: Binance Futures client instance
        symbol: Trading pair symbol (e.g., BTCUSDT)
        side: Order side (BUY/SELL)
        order_type: Order type (MARKET/LIMIT)
        quantity: Order quantity
        price: Order price (required for LIMIT orders)
        stop_price: Stop price (for stop orders)
        time_in_force: Time in force (GTC/IOC/FOK/GTX)
    
    Returns:
        OrderResult with success/failure details
    """
    try:
        # Validate parameters
        logger.info("Validating order parameters...")
        params = validate_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force
        )
        
        # Print request summary
        summary = format_order_request_summary(params)
        print(summary)
        logger.info(f"Order request: {params}")
        
        # Place the order
        logger.info("Sending order to Binance...")
        response = client.place_order(
            symbol=params.symbol,
            side=params.side.value,
            order_type=params.order_type.value,
            quantity=str(params.quantity),
            price=str(params.price) if params.price else None,
            stop_price=str(params.stop_price) if params.stop_price else None,
            time_in_force=params.time_in_force.value if params.time_in_force else None
        )
        
        logger.info(f"Order response received: {response}")
        
        # Build result
        result = OrderResult(
            success=True,
            order_id=response.get("orderId"),
            client_order_id=response.get("clientOrderId"),
            symbol=response.get("symbol"),
            side=response.get("side"),
            order_type=response.get("type"),
            status=response.get("status"),
            quantity=response.get("origQty"),
            executed_qty=response.get("executedQty"),
            price=response.get("price"),
            avg_price=response.get("avgPrice"),
            time_in_force=response.get("timeInForce"),
            raw_response=response
        )
        
        logger.info(f"Order placed successfully: ID={result.order_id}, Status={result.status}")
        return result
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return OrderResult(
            success=False,
            error_message=f"Validation error: {str(e)}"
        )
    except BinanceAPIError as e:
        logger.error(f"Binance API error: {e}")
        return OrderResult(
            success=False,
            error_message=f"Binance API error: {str(e)}"
        )
    except BinanceClientError as e:
        logger.error(f"Client error: {e}")
        return OrderResult(
            success=False,
            error_message=f"Client error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected error placing order: {e}")
        return OrderResult(
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )


def place_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: str
) -> OrderResult:
    """
    Place a market order (convenience function).
    
    Args:
        client: Binance Futures client instance
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        quantity: Order quantity
    
    Returns:
        OrderResult with success/failure details
    """
    return place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type="MARKET",
        quantity=quantity
    )


def place_limit_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: str,
    price: str,
    time_in_force: str = "GTC"
) -> OrderResult:
    """
    Place a limit order (convenience function).
    
    Args:
        client: Binance Futures client instance
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        quantity: Order quantity
        price: Order price
        time_in_force: Time in force (default: GTC)
    
    Returns:
        OrderResult with success/failure details
    """
    return place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type="LIMIT",
        quantity=quantity,
        price=price,
        time_in_force=time_in_force
    )


def place_stop_market_order(
    client: BinanceFuturesClient,
    symbol: str,
    side: str,
    quantity: str,
    stop_price: str
) -> OrderResult:
    """
    Place a stop market order (bonus feature).
    
    Args:
        client: Binance Futures client instance
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        quantity: Order quantity
        stop_price: Stop trigger price
    
    Returns:
        OrderResult with success/failure details
    """
    return place_order(
        client=client,
        symbol=symbol,
        side=side,
        order_type="STOP_MARKET",
        quantity=quantity,
        stop_price=stop_price
    )


def cancel_order(
    client: BinanceFuturesClient,
    symbol: str,
    order_id: Optional[int] = None,
    client_order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel an existing order.
    
    Args:
        client: Binance Futures client instance
        symbol: Trading pair symbol
        order_id: Binance order ID
        client_order_id: Client order ID
    
    Returns:
        Cancel response from API
    """
    try:
        logger.info(f"Cancelling order: symbol={symbol}, order_id={order_id}")
        response = client.cancel_order(
            symbol=symbol,
            order_id=order_id,
            client_order_id=client_order_id
        )
        logger.info(f"Order cancelled successfully: {response}")
        return {"success": True, "response": response}
    except BinanceClientError as e:
        logger.error(f"Failed to cancel order: {e}")
        return {"success": False, "error": str(e)}


def get_current_price(client: BinanceFuturesClient, symbol: str) -> Optional[Decimal]:
    """
    Get current price for a symbol.
    
    Args:
        client: Binance Futures client instance
        symbol: Trading pair symbol
    
    Returns:
        Current price as Decimal, or None if error
    """
    try:
        ticker = client.get_ticker_price(symbol)
        price = Decimal(ticker.get("price", "0"))
        logger.info(f"Current price for {symbol}: {price}")
        return price
    except Exception as e:
        logger.error(f"Failed to get price for {symbol}: {e}")
        return None
