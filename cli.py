#!/usr/bin/env python3
"""
Trading Bot CLI - Command-line interface for Binance Futures Testnet trading.

This module provides a user-friendly CLI for placing orders on Binance Futures Testnet.
Supports MARKET and LIMIT orders with proper validation and error handling.

Usage:
    python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 50000
    python cli.py price --symbol BTCUSDT
    python cli.py account
"""

import argparse
import sys
from typing import Optional

from bot.client import BinanceFuturesClient, BinanceClientError
from bot.logging_config import setup_logging, get_logger
from bot.orders import (
    place_order, place_market_order, place_limit_order,
    place_stop_market_order, get_current_price
)
from bot.validators import ValidationError


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Place a MARKET BUY order:
    python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  Place a LIMIT SELL order:
    python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

  Place a STOP_MARKET order:
    python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 45000

  Get current price:
    python cli.py price --symbol BTCUSDT

  Check account info:
    python cli.py account

  Check open positions:
    python cli.py positions

Environment Variables:
  BINANCE_API_KEY     - Your Binance Testnet API key
  BINANCE_API_SECRET  - Your Binance Testnet API secret
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Order command
    order_parser = subparsers.add_parser(
        "order",
        help="Place a new order",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    order_parser.add_argument(
        "--symbol", "-s",
        required=True,
        help="Trading pair symbol (e.g., BTCUSDT)"
    )
    order_parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL"
    )
    order_parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET", "market", "limit", "stop_market"],
        dest="order_type",
        help="Order type: MARKET, LIMIT, or STOP_MARKET"
    )
    order_parser.add_argument(
        "--quantity", "-q",
        required=True,
        help="Order quantity"
    )
    order_parser.add_argument(
        "--price", "-p",
        help="Order price (required for LIMIT orders)"
    )
    order_parser.add_argument(
        "--stop-price",
        help="Stop price (for STOP_MARKET orders)"
    )
    order_parser.add_argument(
        "--time-in-force", "-tif",
        choices=["GTC", "IOC", "FOK", "GTX"],
        default="GTC",
        help="Time in force (default: GTC)"
    )
    
    # Price command
    price_parser = subparsers.add_parser(
        "price",
        help="Get current price for a symbol"
    )
    price_parser.add_argument(
        "--symbol", "-s",
        required=True,
        help="Trading pair symbol (e.g., BTCUSDT)"
    )
    
    # Account command
    subparsers.add_parser(
        "account",
        help="Get account information"
    )
    
    # Positions command
    positions_parser = subparsers.add_parser(
        "positions",
        help="Get open positions"
    )
    positions_parser.add_argument(
        "--symbol", "-s",
        help="Filter by symbol (optional)"
    )
    
    # Open orders command
    orders_parser = subparsers.add_parser(
        "open-orders",
        help="Get open orders"
    )
    orders_parser.add_argument(
        "--symbol", "-s",
        help="Filter by symbol (optional)"
    )
    
    # Cancel order command
    cancel_parser = subparsers.add_parser(
        "cancel",
        help="Cancel an order"
    )
    cancel_parser.add_argument(
        "--symbol", "-s",
        required=True,
        help="Trading pair symbol"
    )
    cancel_parser.add_argument(
        "--order-id",
        type=int,
        help="Order ID to cancel"
    )
    cancel_parser.add_argument(
        "--client-order-id",
        help="Client order ID to cancel"
    )
    
    return parser


def handle_order_command(args, client: BinanceFuturesClient, logger) -> int:
    """Handle the order placement command."""
    logger.info(f"Processing order command: {args}")
    
    result = place_order(
        client=client,
        symbol=args.symbol,
        side=args.side.upper(),
        order_type=args.order_type.upper(),
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
        time_in_force=args.time_in_force
    )
    
    # Print result
    print(result)
    
    if result.success:
        logger.info("Order command completed successfully")
        return 0
    else:
        logger.error(f"Order command failed: {result.error_message}")
        return 1


def handle_price_command(args, client: BinanceFuturesClient, logger) -> int:
    """Handle the price check command."""
    logger.info(f"Getting price for {args.symbol}")
    
    price = get_current_price(client, args.symbol.upper())
    
    if price:
        print(f"\n{'='*40}")
        print(f"📈 Current Price: {args.symbol.upper()}")
        print(f"{'='*40}")
        print(f"Price: {price}")
        print(f"{'='*40}\n")
        return 0
    else:
        print(f"Failed to get price for {args.symbol}")
        return 1


def handle_account_command(client: BinanceFuturesClient, logger) -> int:
    """Handle the account info command."""
    logger.info("Getting account information")
    
    try:
        account = client.get_account_info()
        
        print(f"\n{'='*50}")
        print("💰 ACCOUNT INFORMATION")
        print(f"{'='*50}")
        print(f"Total Wallet Balance: {account.get('totalWalletBalance', 'N/A')} USDT")
        print(f"Available Balance   : {account.get('availableBalance', 'N/A')} USDT")
        print(f"Total Unrealized PnL: {account.get('totalUnrealizedProfit', 'N/A')} USDT")
        print(f"Total Margin Balance: {account.get('totalMarginBalance', 'N/A')} USDT")
        print(f"{'='*50}")
        
        # Show non-zero asset balances
        assets = account.get("assets", [])
        non_zero_assets = [a for a in assets if float(a.get("walletBalance", 0)) > 0]
        
        if non_zero_assets:
            print("\n📊 Asset Balances:")
            for asset in non_zero_assets:
                print(f"  {asset['asset']}: {asset['walletBalance']} (Available: {asset['availableBalance']})")
        
        print()
        return 0
        
    except BinanceClientError as e:
        logger.error(f"Failed to get account info: {e}")
        print(f"Error: {e}")
        return 1


def handle_positions_command(args, client: BinanceFuturesClient, logger) -> int:
    """Handle the positions command."""
    logger.info("Getting position information")
    
    try:
        positions = client.get_position_info(
            symbol=args.symbol.upper() if hasattr(args, 'symbol') and args.symbol else None
        )
        
        # Filter for positions with non-zero amounts
        active_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
        
        print(f"\n{'='*60}")
        print("📊 POSITIONS")
        print(f"{'='*60}")
        
        if not active_positions:
            print("No open positions")
        else:
            for pos in active_positions:
                print(f"\nSymbol: {pos['symbol']}")
                print(f"  Side: {'LONG' if float(pos['positionAmt']) > 0 else 'SHORT'}")
                print(f"  Amount: {pos['positionAmt']}")
                print(f"  Entry Price: {pos['entryPrice']}")
                print(f"  Mark Price: {pos['markPrice']}")
                print(f"  Unrealized PnL: {pos['unRealizedProfit']}")
                print(f"  Leverage: {pos['leverage']}x")
        
        print(f"\n{'='*60}\n")
        return 0
        
    except BinanceClientError as e:
        logger.error(f"Failed to get positions: {e}")
        print(f"Error: {e}")
        return 1


def handle_open_orders_command(args, client: BinanceFuturesClient, logger) -> int:
    """Handle the open orders command."""
    logger.info("Getting open orders")
    
    try:
        orders = client.get_open_orders(
            symbol=args.symbol.upper() if hasattr(args, 'symbol') and args.symbol else None
        )
        
        print(f"\n{'='*70}")
        print("📋 OPEN ORDERS")
        print(f"{'='*70}")
        
        if not orders:
            print("No open orders")
        else:
            for order in orders:
                print(f"\nOrder ID: {order['orderId']}")
                print(f"  Symbol: {order['symbol']}")
                print(f"  Side: {order['side']}")
                print(f"  Type: {order['type']}")
                print(f"  Quantity: {order['origQty']}")
                print(f"  Price: {order['price']}")
                print(f"  Status: {order['status']}")
                print(f"  Time: {order['time']}")
        
        print(f"\n{'='*70}\n")
        return 0
        
    except BinanceClientError as e:
        logger.error(f"Failed to get open orders: {e}")
        print(f"Error: {e}")
        return 1


def handle_cancel_command(args, client: BinanceFuturesClient, logger) -> int:
    """Handle the cancel order command."""
    if not args.order_id and not args.client_order_id:
        print("Error: Either --order-id or --client-order-id must be provided")
        return 1
    
    logger.info(f"Cancelling order: symbol={args.symbol}, order_id={args.order_id}")
    
    try:
        response = client.cancel_order(
            symbol=args.symbol.upper(),
            order_id=args.order_id,
            client_order_id=args.client_order_id
        )
        
        print(f"\n{'='*50}")
        print("✅ ORDER CANCELLED")
        print(f"{'='*50}")
        print(f"Order ID: {response.get('orderId')}")
        print(f"Symbol: {response.get('symbol')}")
        print(f"Status: {response.get('status')}")
        print(f"{'='*50}\n")
        return 0
        
    except BinanceClientError as e:
        logger.error(f"Failed to cancel order: {e}")
        print(f"Error: {e}")
        return 1


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return 0
    
    # Setup logging
    logger = setup_logging(args.log_level)
    logger.info("="*50)
    logger.info("Trading Bot CLI Started")
    logger.info("="*50)
    
    try:
        # Initialize client
        client = BinanceFuturesClient()
        
        # Route to appropriate handler
        if args.command == "order":
            return handle_order_command(args, client, logger)
        elif args.command == "price":
            return handle_price_command(args, client, logger)
        elif args.command == "account":
            return handle_account_command(client, logger)
        elif args.command == "positions":
            return handle_positions_command(args, client, logger)
        elif args.command == "open-orders":
            return handle_open_orders_command(args, client, logger)
        elif args.command == "cancel":
            return handle_cancel_command(args, client, logger)
        else:
            parser.print_help()
            return 1
            
    except BinanceClientError as e:
        logger.error(f"Binance client error: {e}")
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have set the following environment variables:")
        print("  BINANCE_API_KEY")
        print("  BINANCE_API_SECRET")
        print("\nSee README.md for setup instructions.\n")
        return 1
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        print("\n\nOperation cancelled.")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 1
    finally:
        logger.info("Trading Bot CLI Finished")
        logger.info("="*50)


if __name__ == "__main__":
    sys.exit(main())
