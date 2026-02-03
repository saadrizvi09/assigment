# Trading Bot - Binance Futures Testnet

A simplified Python trading bot for placing orders on Binance Futures Testnet (USDT-M).

## Features

- ✅ Place **Market** and **Limit** orders
- ✅ Support for **BUY** and **SELL** sides
- ✅ **Stop-Market** orders (bonus feature)
- ✅ Clean CLI interface with argument validation
- ✅ Structured logging to file and console
- ✅ Comprehensive error handling
- ✅ Reusable modular architecture

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package initialization
│   ├── client.py             # Binance API client wrapper
│   ├── orders.py             # Order placement logic
│   ├── validators.py         # Input validation
│   └── logging_config.py     # Logging configuration
├── logs/                     # Log files (created automatically)
├── cli.py                    # CLI entry point
├── requirements.txt          # Dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Prerequisites

- Python 3.8 or higher
- Binance Futures Testnet account with API credentials

## Setup

### 1. Clone or extract the project

```bash
cd trading_bot
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Binance Futures Testnet API credentials

1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Register/login with your account
3. Navigate to API Management
4. Generate new API Key and Secret
5. **Important**: Save both the API Key and Secret immediately (Secret is shown only once)

### 5. Configure environment variables

Create a `.env` file in the `trading_bot` directory:

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
# Windows: notepad .env
# macOS/Linux: nano .env
```

Add your credentials:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

## Usage

### Basic Commands

```bash
# Get help
python cli.py --help

# Get help for a specific command
python cli.py order --help
```

### Place Orders

#### Market Order (BUY)

```bash
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

#### Market Order (SELL)

```bash
python cli.py order --symbol BTCUSDT --side SELL --type MARKET --quantity 0.001
```

#### Limit Order (BUY)

```bash
python cli.py order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000
```

#### Limit Order (SELL)

```bash
python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000
```

#### Stop-Market Order (Bonus)

```bash
python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 45000
```

### Other Commands

```bash
# Check current price
python cli.py price --symbol BTCUSDT

# Check account balance
python cli.py account

# Check open positions
python cli.py positions

# Check open orders
python cli.py open-orders

# Cancel an order
python cli.py cancel --symbol BTCUSDT --order-id 123456789
```

### Logging Options

```bash
# Enable debug logging
python cli.py --log-level DEBUG order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

## Example Output

### Market Order

```
==================================================
📋 ORDER REQUEST SUMMARY
==================================================
Symbol        : BTCUSDT
Side          : BUY
Type          : MARKET
Quantity      : 0.001
==================================================

==================================================
✅ ORDER PLACED SUCCESSFULLY
==================================================
Order ID      : 1234567890
Client ID     : abc123xyz
Symbol        : BTCUSDT
Side          : BUY
Type          : MARKET
Status        : FILLED
Quantity      : 0.001
Executed Qty  : 0.001
Price         : MARKET
Avg Price     : 97500.50
Time in Force : N/A
==================================================
```

### Limit Order

```
==================================================
📋 ORDER REQUEST SUMMARY
==================================================
Symbol        : BTCUSDT
Side          : SELL
Type          : LIMIT
Quantity      : 0.001
Price         : 100000
Time in Force : GTC
==================================================

==================================================
✅ ORDER PLACED SUCCESSFULLY
==================================================
Order ID      : 1234567891
Client ID     : def456uvw
Symbol        : BTCUSDT
Side          : SELL
Type          : LIMIT
Status        : NEW
Quantity      : 0.001
Executed Qty  : 0
Price         : 100000
Avg Price     : 0
Time in Force : GTC
==================================================
```

## Log Files

Log files are automatically created in the `logs/` directory with timestamps:

```
logs/
├── trading_bot_20260203_143022.log
├── trading_bot_20260203_150515.log
└── ...
```

Each log file contains:
- Timestamps
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Function names and line numbers
- API requests and responses (sensitive data masked)
- Error details and stack traces

## Error Handling

The bot handles various error scenarios:

- **Invalid input**: Validation errors with clear messages
- **API errors**: Binance API error codes and messages
- **Network errors**: Timeout and connection issues
- **Authentication errors**: Invalid or missing credentials

Example error output:

```
==================================================
❌ ORDER FAILED
==================================================
Error: Validation error: Price is required for LIMIT orders
==================================================
```

## Testing

The bot has been tested and verified working with:
- ✅ Price queries (BTCUSDT: $78,166.00 retrieved successfully)
- ✅ API authentication with Binance Futures Testnet
- ✅ Input validation and error handling
- ✅ Logging to file with timestamps
- ✅ All sample log files included in `logs/` directory

## Assumptions

1. **Testnet only**: This bot is designed for Binance Futures Testnet only. Do not use with production API keys.

2. **USDT-M Futures**: Designed for USDT-margined futures pairs (e.g., BTCUSDT, ETHUSDT).

3. **Minimum quantities**: Binance has minimum notional value requirements. For BTCUSDT, typical minimum is 0.001 BTC.

4. **No position management**: The bot places orders but does not implement automated trading strategies.

5. **Single orders**: The bot places one order at a time (no batch orders).

## Troubleshooting

### "API credentials not found"

Make sure you have:
1. Created a `.env` file in the project directory
2. Added both `BINANCE_API_KEY` and `BINANCE_API_SECRET`
3. No extra spaces around the `=` sign

### "Invalid symbol"

Check that:
1. Symbol exists on Binance Futures Testnet
2. Symbol is uppercase (e.g., `BTCUSDT` not `btcusdt`)
3. Symbol includes the quote currency (e.g., `BTCUSDT` not `BTC`)

### "Insufficient margin"

The testnet account may need funds:
1. Go to [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Request test funds from the faucet (if available)
3. Or reduce order quantity

### Network/Timeout errors

- Check your internet connection
- The testnet may be experiencing issues - try again later

## License

This project is provided for educational purposes as part of a technical assessment.
