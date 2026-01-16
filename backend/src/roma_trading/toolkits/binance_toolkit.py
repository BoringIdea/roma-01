"""
Binance Futures Toolkit - Implementation for Binance USDⓈ-M Futures.

This toolkit provides trading functionality for Binance perpetual futures,
including account management, position handling, and order execution.

Uses HMAC-SHA256 signing for API authentication.
"""

import time
import hmac
import hashlib
import asyncio
from typing import Dict, List, Optional
from urllib.parse import urlencode
import httpx
from loguru import logger

from .base_dex import BaseDEXToolkit


class BinanceToolkit(BaseDEXToolkit):
    """
    Binance Futures trading toolkit with HMAC-SHA256 authentication.

    Features:
    - HMAC-SHA256 request signing
    - Automatic precision handling
    - Order retries on network errors
    - Full perpetual futures support
    - Testnet support
    """

    BASE_URL = "https://fapi.binance.com"
    TESTNET_URL = "https://testnet.binancefuture.com"
    RECV_WINDOW = 5000  # milliseconds

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        hedge_mode: bool = False,
    ):
        """
        Initialize Binance Futures toolkit.

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet (default: False)
            hedge_mode: Whether account uses dual-position mode (default: False)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.hedge_mode = hedge_mode
        self.base_url = self.TESTNET_URL if testnet else self.BASE_URL

        # HTTP client with reasonable timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5),
            headers={"X-MBX-APIKEY": api_key},
        )

        # Cache for symbol precision
        self._precision_cache: Dict[str, Dict] = {}

        logger.info(
            f"Initialized BinanceToolkit (testnet={testnet}, hedge_mode={hedge_mode})"
        )

    def _generate_signature(self, params: Dict) -> str:
        """
        Generate HMAC-SHA256 signature for request parameters.

        Args:
            params: Request parameters

        Returns:
            Hex-encoded signature string
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _add_signature(self, params: Dict) -> Dict:
        """
        Add timestamp and signature to request parameters.

        Args:
            params: Request parameters

        Returns:
            Parameters with timestamp and signature added
        """
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = self.RECV_WINDOW
        params["signature"] = self._generate_signature(params)
        return params

    async def _get_precision(self, symbol: str) -> Dict:
        """
        Get price and quantity precision for a symbol.

        Returns:
            Dict with price_precision, quantity_precision, tick_size, step_size
        """
        if symbol in self._precision_cache:
            return self._precision_cache[symbol]

        # Fetch exchange info
        response = await self.client.get(f"{self.base_url}/fapi/v1/exchangeInfo")
        response.raise_for_status()
        data = response.json()

        # Parse precision for all symbols
        for s in data.get("symbols", []):
            if s["symbol"] == symbol:
                precision_info = {
                    "price_precision": s["pricePrecision"],
                    "quantity_precision": s["quantityPrecision"],
                    "tick_size": 0.0,
                    "step_size": 0.0,
                }

                # Extract tick_size and step_size from filters
                for f in s.get("filters", []):
                    if f["filterType"] == "PRICE_FILTER":
                        precision_info["tick_size"] = float(f.get("tickSize", 0))
                    elif f["filterType"] == "LOT_SIZE":
                        precision_info["step_size"] = float(f.get("stepSize", 0))

                self._precision_cache[symbol] = precision_info
                return precision_info

        raise ValueError(f"Symbol {symbol} not found in exchange info")

    def _format_value(self, value: float, precision: int, step: float = 0.0) -> str:
        """
        Format a value to the correct precision.

        Args:
            value: Value to format
            precision: Number of decimal places
            step: Step size (if provided, rounds to nearest step)

        Returns:
            Formatted string without trailing zeros
        """
        if step > 0:
            # Round to nearest step
            value = round(value / step) * step

        # Format to precision
        formatted = f"{value:.{precision}f}"

        # Remove trailing zeros and decimal point if not needed
        formatted = formatted.rstrip('0').rstrip('.')

        return formatted

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict,
        signed: bool = True,
        max_retries: int = 3,
    ) -> Dict:
        """
        Make HTTP request with optional signing and retry logic.

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether to sign the request
            max_retries: Number of retries on network errors

        Returns:
            Response JSON
        """
        for attempt in range(max_retries):
            try:
                request_params = params.copy()
                if signed:
                    request_params = self._add_signature(request_params)

                # Build full URL with query string to ensure signature matches
                query_string = urlencode(request_params)
                full_url = f"{self.base_url}{endpoint}?{query_string}"

                # Make request based on method (no params, already in URL)
                if method == "POST":
                    response = await self.client.post(full_url)
                elif method == "DELETE":
                    response = await self.client.delete(full_url)
                else:  # GET
                    response = await self.client.get(full_url)

                response.raise_for_status()
                return response.json()

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1.0
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries}): {e}, "
                        f"retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise

    async def get_account_balance(self) -> Dict:
        """Get account balance information."""
        data = await self._request("GET", "/fapi/v2/balance", {})

        # Find USDT balance
        wallet_balance = 0.0
        available_balance = 0.0
        unrealized_profit = 0.0

        for asset in data:
            if asset.get("asset") == "USDT":
                wallet_balance = float(asset.get("balance", 0))
                available_balance = float(asset.get("availableBalance", 0))
                unrealized_profit = float(asset.get("crossUnPnl", 0))
                break

        # Total balance = wallet balance + unrealized profit
        total_balance = wallet_balance + unrealized_profit

        return {
            "total_wallet_balance": total_balance,
            "available_balance": available_balance,
            "total_unrealized_profit": unrealized_profit,
        }

    async def get_positions(self) -> List[Dict]:
        """Get current open positions."""
        data = await self._request("GET", "/fapi/v2/positionRisk", {})

        positions = []
        for pos in data:
            position_amt = float(pos.get("positionAmt", 0))

            # Skip empty positions
            if position_amt == 0:
                continue

            # Determine side
            side = "long" if position_amt > 0 else "short"

            positions.append({
                "symbol": pos["symbol"],
                "side": side,
                "position_amt": abs(position_amt),
                "entry_price": float(pos.get("entryPrice", 0)),
                "mark_price": float(pos.get("markPrice", 0)),
                "unrealized_profit": float(pos.get("unRealizedProfit", 0)),
                "leverage": int(float(pos.get("leverage", 1))),
                "liquidation_price": float(pos.get("liquidationPrice", 0)),
            })

        return positions

    async def get_market_price(self, symbol: str) -> float:
        """Get current market price."""
        response = await self.client.get(
            f"{self.base_url}/fapi/v1/ticker/price",
            params={"symbol": symbol}
        )
        response.raise_for_status()
        data = response.json()
        return float(data["price"])

    async def get_klines(
        self, symbol: str, interval: str = "3m", limit: int = 100
    ) -> List[Dict]:
        """Get historical kline data."""
        response = await self.client.get(
            f"{self.base_url}/fapi/v1/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()

        # Convert to standardized format
        klines = []
        for k in data:
            klines.append({
                "open_time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": k[6],
            })

        return klines

    async def _set_leverage(self, symbol: str, leverage: int) -> None:
        """Set leverage for a symbol."""
        await self._request(
            "POST",
            "/fapi/v1/leverage",
            {"symbol": symbol, "leverage": leverage}
        )

    async def _cancel_all_orders(self, symbol: str) -> None:
        """Cancel all open orders for a symbol."""
        try:
            await self._request("DELETE", "/fapi/v1/allOpenOrders", {"symbol": symbol})
        except Exception as e:
            logger.warning(f"Failed to cancel orders for {symbol}: {e}")

    async def place_take_profit_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        take_profit_pct: float | None,
        stop_loss_pct: float | None,
    ) -> Dict:
        """Place take-profit and stop-loss orders for the given position."""
        results: Dict[str, Dict] = {}

        if quantity <= 0 or entry_price <= 0:
            logger.warning("Cannot place TP/SL orders due to non-positive quantity or entry price")
            return results

        precision = await self._get_precision(symbol)
        qty_str = self._format_value(
            quantity,
            precision["quantity_precision"],
            precision["step_size"],
        )

        def _position_side() -> str:
            if not self.hedge_mode:
                return "BOTH"
            return "LONG" if side == "long" else "SHORT"

        # Take-profit order
        if take_profit_pct and take_profit_pct > 0:
            if side == "long":
                tp_price = entry_price * (1 + take_profit_pct / 100)
                order_side = "SELL"
            else:
                tp_price = entry_price * (1 - take_profit_pct / 100)
                order_side = "BUY"

            if tp_price > 0:
                stop_price_str = self._format_value(
                    tp_price,
                    precision["price_precision"],
                    precision["tick_size"],
                )
                params = {
                    "symbol": symbol,
                    "side": order_side,
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": stop_price_str,
                    "quantity": qty_str,
                    "reduceOnly": "true",
                }
                if self.hedge_mode:
                    params["positionSide"] = _position_side()

                try:
                    result = await self._request("POST", "/fapi/v1/order", params)
                    results["take_profit"] = result
                    logger.info(
                        f"Placed take-profit for {symbol} {side}: "
                        f"stopPrice={stop_price_str}, quantity={qty_str}"
                    )
                except Exception as exc:
                    logger.error(f"Failed to place take-profit order: {exc}")

        # Stop-loss order
        if stop_loss_pct and stop_loss_pct > 0:
            if side == "long":
                sl_price = entry_price * (1 - stop_loss_pct / 100)
                order_side = "SELL"
            else:
                sl_price = entry_price * (1 + stop_loss_pct / 100)
                order_side = "BUY"

            if sl_price > 0:
                stop_price_str = self._format_value(
                    sl_price,
                    precision["price_precision"],
                    precision["tick_size"],
                )
                params = {
                    "symbol": symbol,
                    "side": order_side,
                    "type": "STOP_MARKET",
                    "stopPrice": stop_price_str,
                    "quantity": qty_str,
                    "reduceOnly": "true",
                }
                if self.hedge_mode:
                    params["positionSide"] = _position_side()

                try:
                    result = await self._request("POST", "/fapi/v1/order", params)
                    results["stop_loss"] = result
                    logger.info(
                        f"Placed stop-loss for {symbol} {side}: "
                        f"stopPrice={stop_price_str}, quantity={qty_str}"
                    )
                except Exception as exc:
                    logger.error(f"Failed to place stop-loss order: {exc}")

        return results

    async def open_long(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """Open a long position."""
        # Cancel any existing orders
        await self._cancel_all_orders(symbol)

        # Set leverage
        await self._set_leverage(symbol, leverage)

        # Get precision
        precision = await self._get_precision(symbol)

        # Format quantity
        qty_str = self._format_value(
            quantity,
            precision["quantity_precision"],
            precision["step_size"]
        )

        logger.info(f"Opening LONG {symbol}: quantity={qty_str}, leverage={leverage}x")

        # Prepare order parameters - use MARKET order for immediate fill
        order_params = {
            "symbol": symbol,
            "type": "MARKET",
            "side": "BUY",
            "quantity": qty_str,
        }

        # Add positionSide only if hedge mode is enabled
        if self.hedge_mode:
            order_params["positionSide"] = "LONG"

        # Place order
        result = await self._request("POST", "/fapi/v1/order", order_params)

        return {
            "order_id": result.get("orderId"),
            "symbol": symbol,
            "side": "long",
            "quantity": qty_str,
            "price": result.get("avgPrice", "0"),
            "status": result.get("status"),
        }

    async def open_short(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """Open a short position."""
        await self._cancel_all_orders(symbol)
        await self._set_leverage(symbol, leverage)

        precision = await self._get_precision(symbol)

        qty_str = self._format_value(
            quantity,
            precision["quantity_precision"],
            precision["step_size"]
        )

        logger.info(f"Opening SHORT {symbol}: quantity={qty_str}, leverage={leverage}x")

        # Prepare order parameters - use MARKET order for immediate fill
        order_params = {
            "symbol": symbol,
            "type": "MARKET",
            "side": "SELL",
            "quantity": qty_str,
        }

        # Add positionSide only if hedge mode is enabled
        if self.hedge_mode:
            order_params["positionSide"] = "SHORT"

        # Place order
        result = await self._request("POST", "/fapi/v1/order", order_params)

        return {
            "order_id": result.get("orderId"),
            "symbol": symbol,
            "side": "short",
            "quantity": qty_str,
            "price": result.get("avgPrice", "0"),
            "status": result.get("status"),
        }

    async def close_position(self, symbol: str, side: str, quantity: float | None = None) -> Dict:
        """Close an existing position. Optional partial quantity supported."""
        # Get current position
        positions = await self.get_positions()
        position = next(
            (p for p in positions if p["symbol"] == symbol and p["side"] == side),
            None
        )

        if not position:
            raise ValueError(f"No {side} position found for {symbol}")

        position_amt = position["position_amt"]
        target_qty = position_amt if quantity is None else min(abs(quantity), position_amt)
        if target_qty <= 0:
            raise ValueError("Close quantity must be positive")

        precision = await self._get_precision(symbol)

        # Opposite side to close
        order_side = "SELL" if side == "long" else "BUY"

        qty_str = self._format_value(
            target_qty,
            precision["quantity_precision"],
            precision["step_size"]
        )

        logger.info(f"Closing {side.upper()} {symbol}: quantity={qty_str}")

        # Prepare order parameters - use MARKET order for immediate fill
        order_params = {
            "symbol": symbol,
            "type": "MARKET",
            "side": order_side,
            "quantity": qty_str,
            "reduceOnly": "true",
        }

        # Add positionSide only if hedge mode is enabled
        if self.hedge_mode:
            position_side = "LONG" if side == "long" else "SHORT"
            order_params["positionSide"] = position_side

        # Place order
        result = await self._request("POST", "/fapi/v1/order", order_params)

        # Cancel remaining orders if fully closed
        if abs(target_qty - position_amt) < 1e-9:
            await self._cancel_all_orders(symbol)

        return {
            "order_id": result.get("orderId"),
            "symbol": symbol,
            "closed_side": side,
            "quantity": qty_str,
            "closed_quantity": target_qty,
            "fully_closed": abs(target_qty - position_amt) < 1e-9,
            "status": result.get("status"),
        }

    async def get_premium_index(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get premium index and funding rate.

        Args:
            symbol: Trading pair (optional, if None returns all symbols)

        Returns:
            List of premium index data
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        response = await self.client.get(
            f"{self.base_url}/fapi/v1/premiumIndex",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def get_funding_rate_history(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get funding rate history.

        Args:
            symbol: Trading pair
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Max number of records (max 1000)

        Returns:
            List of funding rate history records
        """
        params = {
            "symbol": symbol,
            "limit": min(limit, 1000)
        }

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        response = await self.client.get(
            f"{self.base_url}/fapi/v1/fundingRate",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_depth(self, symbol: str, limit: int = 100) -> Dict:
        """
        Get order book depth.

        Args:
            symbol: Trading pair
            limit: Depth limit (5, 10, 20, 50, 100, 500, 1000)

        Returns:
            Order book depth data
        """
        response = await self.client.get(
            f"{self.base_url}/fapi/v1/depth",
            params={"symbol": symbol, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def get_ticker_24hr(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get 24hr ticker statistics.

        Args:
            symbol: Trading pair (optional, if None returns all symbols)

        Returns:
            List of ticker data
        """
        params = {}
        if symbol:
            params["symbol"] = symbol

        response = await self.client.get(
            f"{self.base_url}/fapi/v1/ticker/24hr",
            params=params
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def get_user_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict]:
        """
        Get account trade history.

        Args:
            symbol: Trading pair. If None, queries common symbols.
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Max number of trades to return (max 1000)

        Returns:
            List of trade records with PnL, prices, quantities, etc.
        """
        params = {"limit": min(limit, 1000)}

        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        if symbol:
            params["symbol"] = symbol
            data = await self._request("GET", "/fapi/v1/userTrades", params)
        else:
            all_trades = []
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"]

            for sym in symbols:
                try:
                    params["symbol"] = sym
                    trades = await self._request("GET", "/fapi/v1/userTrades", params)
                    all_trades.extend(trades)
                except Exception as e:
                    logger.debug(f"No trades found for {sym}: {e}")
                    continue

            data = all_trades

        # Convert to standard format
        trades = []
        for t in data:
            trades.append({
                "id": t.get("id"),
                "order_id": t.get("orderId"),
                "symbol": t.get("symbol"),
                "side": t.get("side"),
                "position_side": t.get("positionSide"),
                "price": float(t.get("price", 0)),
                "quantity": float(t.get("qty", 0)),
                "quote_quantity": float(t.get("quoteQty", 0)),
                "realized_pnl": float(t.get("realizedPnl", 0)),
                "commission": float(t.get("commission", 0)),
                "commission_asset": t.get("commissionAsset"),
                "time": t.get("time"),
                "buyer": t.get("buyer"),
                "maker": t.get("maker"),
            })

        # Sort by time (newest first)
        trades.sort(key=lambda x: x["time"] or 0, reverse=True)

        return trades

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
