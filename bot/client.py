"""
Binance Futures Testnet API Client.

Provides a clean wrapper for interacting with the Binance Futures Testnet API.
Handles authentication, request signing, and error handling.
"""

import hashlib
import hmac
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

from .logging_config import get_logger

logger = get_logger()

# Load environment variables
load_dotenv()


class BinanceClientError(Exception):
    """Base exception for Binance client errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class BinanceAPIError(BinanceClientError):
    """Raised when Binance API returns an error."""
    pass


class BinanceNetworkError(BinanceClientError):
    """Raised when a network error occurs."""
    pass


class BinanceAuthError(BinanceClientError):
    """Raised when authentication fails."""
    pass


class BinanceFuturesClient:
    """
    Client for interacting with Binance Futures Testnet API.
    
    Handles request signing, authentication, and provides methods for
    common API operations.
    """
    
    # Binance Futures Testnet base URL
    BASE_URL = "https://testnet.binancefuture.com"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize the Binance Futures client.
        
        Args:
            api_key: Binance API key (uses BINANCE_API_KEY env var if not provided)
            api_secret: Binance API secret (uses BINANCE_API_SECRET env var if not provided)
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        
        if not self.api_key or not self.api_secret:
            raise BinanceAuthError(
                "API credentials not found. Set BINANCE_API_KEY and BINANCE_API_SECRET "
                "environment variables or pass them to the constructor."
            )
        
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=30.0,
            headers={
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        logger.info(f"Binance Futures client initialized (Testnet: {self.BASE_URL})")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC SHA256 signature for request.
        
        Args:
            params: Request parameters to sign
        
        Returns:
            Hex-encoded signature string
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True
    ) -> Dict[str, Any]:
        """
        Make an API request to Binance.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
        
        Returns:
            JSON response from API
        
        Raises:
            BinanceAPIError: If API returns an error
            BinanceNetworkError: If network error occurs
        """
        params = params or {}
        
        if signed:
            params["timestamp"] = self._get_timestamp()
            params["signature"] = self._generate_signature(params)
        
        # Log request (masking sensitive data)
        safe_params = {k: v for k, v in params.items() if k not in ["signature"]}
        logger.debug(f"API Request: {method} {endpoint}")
        logger.debug(f"Parameters: {safe_params}")
        
        try:
            if method == "GET":
                response = self.client.get(endpoint, params=params)
            elif method == "POST":
                response = self.client.post(endpoint, data=params)
            elif method == "DELETE":
                response = self.client.delete(endpoint, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response body: {response.text[:500]}...")
            
            # Parse response
            data = response.json()
            
            # Check for API errors
            if response.status_code >= 400:
                error_code = data.get("code", -1)
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"API Error: [{error_code}] {error_msg}")
                raise BinanceAPIError(
                    f"Binance API error: [{error_code}] {error_msg}",
                    status_code=response.status_code,
                    error_code=error_code
                )
            
            return data
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {e}")
            raise BinanceNetworkError(f"Request timed out: {e}")
        except httpx.NetworkError as e:
            logger.error(f"Network error: {e}")
            raise BinanceNetworkError(f"Network error: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise BinanceAPIError(f"HTTP error: {e}", status_code=e.response.status_code)
    
    def get_server_time(self) -> Dict[str, Any]:
        """
        Get Binance server time.
        
        Returns:
            Server time response
        """
        return self._make_request("GET", "/fapi/v1/time", signed=False)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        Get exchange trading rules and symbol information.
        
        Returns:
            Exchange info response
        """
        return self._make_request("GET", "/fapi/v1/exchangeInfo", signed=False)
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get trading rules for a specific symbol.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Symbol info or None if not found
        """
        exchange_info = self.get_exchange_info()
        for s in exchange_info.get("symbols", []):
            if s["symbol"] == symbol:
                return s
        return None
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information including balances.
        
        Returns:
            Account info response
        """
        return self._make_request("GET", "/fapi/v2/account")
    
    def get_position_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get position information.
        
        Args:
            symbol: Optional symbol to filter positions
        
        Returns:
            Position info response
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", "/fapi/v2/positionRisk", params=params)
    
    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Ticker price response
        """
        return self._make_request(
            "GET", "/fapi/v1/ticker/price",
            params={"symbol": symbol},
            signed=False
        )
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        stop_price: Optional[str] = None,
        time_in_force: Optional[str] = None,
        reduce_only: bool = False,
        new_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            order_type: Order type (MARKET/LIMIT/etc.)
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            stop_price: Stop price (for stop orders)
            time_in_force: Time in force (GTC/IOC/FOK/GTX)
            reduce_only: Whether order should only reduce position
            new_client_order_id: Custom order ID
        
        Returns:
            Order response from API
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        
        if price:
            params["price"] = price
        
        if stop_price:
            params["stopPrice"] = stop_price
        
        if time_in_force:
            params["timeInForce"] = time_in_force
        
        if reduce_only:
            params["reduceOnly"] = "true"
        
        if new_client_order_id:
            params["newClientOrderId"] = new_client_order_id
        
        logger.info(f"Placing {order_type} {side} order for {quantity} {symbol}")
        
        return self._make_request("POST", "/fapi/v1/order", params=params)
    
    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Binance order ID
            client_order_id: Custom client order ID
        
        Returns:
            Cancel response from API
        """
        if not order_id and not client_order_id:
            raise ValueError("Either order_id or client_order_id must be provided")
        
        params = {"symbol": symbol}
        
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        
        logger.info(f"Cancelling order for {symbol}")
        
        return self._make_request("DELETE", "/fapi/v1/order", params=params)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Get all open orders.
        
        Args:
            symbol: Optional symbol to filter orders
        
        Returns:
            List of open orders
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return self._make_request("GET", "/fapi/v1/openOrders", params=params)
    
    def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get order details.
        
        Args:
            symbol: Trading pair symbol
            order_id: Binance order ID
            client_order_id: Custom client order ID
        
        Returns:
            Order details
        """
        if not order_id and not client_order_id:
            raise ValueError("Either order_id or client_order_id must be provided")
        
        params = {"symbol": symbol}
        
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        
        return self._make_request("GET", "/fapi/v1/order", params=params)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
        logger.info("Binance client closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
