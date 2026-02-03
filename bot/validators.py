"""
Input validation for trading bot parameters.

Provides validation functions for symbols, order types, sides, quantities, and prices.
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional

from .logging_config import get_logger

logger = get_logger()


class OrderSide(Enum):
    """Valid order sides."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Valid order types."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


class TimeInForce(Enum):
    """Valid time in force options."""
    GTC = "GTC"  # Good Till Cancel
    IOC = "IOC"  # Immediate or Cancel
    FOK = "FOK"  # Fill or Kill
    GTX = "GTX"  # Post Only


@dataclass
class OrderParams:
    """Validated order parameters."""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[TimeInForce] = None


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol format.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
    
    Returns:
        Uppercase validated symbol
    
    Raises:
        ValidationError: If symbol format is invalid
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty")
    
    symbol = symbol.upper().strip()
    
    # Basic format validation: letters only, reasonable length
    if not re.match(r'^[A-Z]{5,12}$', symbol):
        raise ValidationError(
            f"Invalid symbol format: '{symbol}'. "
            "Symbol should be 5-12 uppercase letters (e.g., BTCUSDT)"
        )
    
    # Common USDT-M futures pairs end with USDT
    if not symbol.endswith(("USDT", "BUSD")):
        logger.warning(f"Symbol '{symbol}' doesn't end with USDT/BUSD. Make sure it's a valid USDT-M pair.")
    
    logger.debug(f"Symbol validated: {symbol}")
    return symbol


def validate_side(side: str) -> OrderSide:
    """
    Validate order side.
    
    Args:
        side: Order side (BUY or SELL)
    
    Returns:
        OrderSide enum value
    
    Raises:
        ValidationError: If side is invalid
    """
    if not side:
        raise ValidationError("Order side cannot be empty")
    
    side = side.upper().strip()
    
    try:
        return OrderSide(side)
    except ValueError:
        raise ValidationError(
            f"Invalid order side: '{side}'. Must be BUY or SELL"
        )


def validate_order_type(order_type: str) -> OrderType:
    """
    Validate order type.
    
    Args:
        order_type: Type of order (MARKET, LIMIT, etc.)
    
    Returns:
        OrderType enum value
    
    Raises:
        ValidationError: If order type is invalid
    """
    if not order_type:
        raise ValidationError("Order type cannot be empty")
    
    order_type = order_type.upper().strip()
    
    try:
        return OrderType(order_type)
    except ValueError:
        valid_types = ", ".join([t.value for t in OrderType])
        raise ValidationError(
            f"Invalid order type: '{order_type}'. Valid types: {valid_types}"
        )


def validate_quantity(quantity: str) -> Decimal:
    """
    Validate order quantity.
    
    Args:
        quantity: Order quantity as string
    
    Returns:
        Validated quantity as Decimal
    
    Raises:
        ValidationError: If quantity is invalid
    """
    if not quantity:
        raise ValidationError("Quantity cannot be empty")
    
    try:
        qty = Decimal(str(quantity).strip())
    except InvalidOperation:
        raise ValidationError(f"Invalid quantity format: '{quantity}'")
    
    if qty <= 0:
        raise ValidationError(f"Quantity must be positive, got: {qty}")
    
    # Binance has minimum notional value requirements
    # This is a basic check; actual minimums depend on the symbol
    if qty < Decimal("0.00001"):
        raise ValidationError(f"Quantity too small: {qty}")
    
    logger.debug(f"Quantity validated: {qty}")
    return qty


def validate_price(price: Optional[str], order_type: OrderType) -> Optional[Decimal]:
    """
    Validate order price.
    
    Args:
        price: Order price as string (optional for MARKET orders)
        order_type: Type of order
    
    Returns:
        Validated price as Decimal, or None for MARKET orders
    
    Raises:
        ValidationError: If price is invalid or missing when required
    """
    # Price required for LIMIT orders
    if order_type == OrderType.LIMIT:
        if not price:
            raise ValidationError("Price is required for LIMIT orders")
    
    # Price not needed for MARKET orders
    if order_type == OrderType.MARKET:
        if price:
            logger.warning("Price provided for MARKET order will be ignored")
        return None
    
    if not price:
        return None
    
    try:
        p = Decimal(str(price).strip())
    except InvalidOperation:
        raise ValidationError(f"Invalid price format: '{price}'")
    
    if p <= 0:
        raise ValidationError(f"Price must be positive, got: {p}")
    
    logger.debug(f"Price validated: {p}")
    return p


def validate_stop_price(stop_price: Optional[str]) -> Optional[Decimal]:
    """
    Validate stop price for stop orders.
    
    Args:
        stop_price: Stop price as string (optional)
    
    Returns:
        Validated stop price as Decimal, or None
    
    Raises:
        ValidationError: If stop price is invalid
    """
    if not stop_price:
        return None
    
    try:
        sp = Decimal(str(stop_price).strip())
    except InvalidOperation:
        raise ValidationError(f"Invalid stop price format: '{stop_price}'")
    
    if sp <= 0:
        raise ValidationError(f"Stop price must be positive, got: {sp}")
    
    logger.debug(f"Stop price validated: {sp}")
    return sp


def validate_time_in_force(tif: Optional[str], order_type: OrderType) -> Optional[TimeInForce]:
    """
    Validate time in force parameter.
    
    Args:
        tif: Time in force value (optional)
        order_type: Type of order
    
    Returns:
        TimeInForce enum value or default based on order type
    
    Raises:
        ValidationError: If time in force is invalid
    """
    # MARKET orders don't use time in force
    if order_type == OrderType.MARKET:
        return None
    
    # Default to GTC for LIMIT orders
    if not tif and order_type == OrderType.LIMIT:
        return TimeInForce.GTC
    
    if not tif:
        return None
    
    tif = tif.upper().strip()
    
    try:
        return TimeInForce(tif)
    except ValueError:
        valid_tif = ", ".join([t.value for t in TimeInForce])
        raise ValidationError(
            f"Invalid time in force: '{tif}'. Valid values: {valid_tif}"
        )


def validate_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
    time_in_force: Optional[str] = None
) -> OrderParams:
    """
    Validate all order parameters.
    
    Args:
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        order_type: Order type (MARKET/LIMIT)
        quantity: Order quantity
        price: Order price (required for LIMIT)
        stop_price: Stop price (for stop orders)
        time_in_force: Time in force (GTC/IOC/FOK/GTX)
    
    Returns:
        Validated OrderParams object
    
    Raises:
        ValidationError: If any validation fails
    """
    logger.info("Validating order parameters...")
    
    validated_symbol = validate_symbol(symbol)
    validated_side = validate_side(side)
    validated_type = validate_order_type(order_type)
    validated_qty = validate_quantity(quantity)
    validated_price = validate_price(price, validated_type)
    validated_stop = validate_stop_price(stop_price)
    validated_tif = validate_time_in_force(time_in_force, validated_type)
    
    params = OrderParams(
        symbol=validated_symbol,
        side=validated_side,
        order_type=validated_type,
        quantity=validated_qty,
        price=validated_price,
        stop_price=validated_stop,
        time_in_force=validated_tif
    )
    
    logger.info(f"Order parameters validated: {params}")
    return params
