"""
Aster DEX Toolkit - Complete implementation with HMAC SHA256 signing.

This toolkit provides full trading functionality for Aster DEX perpetual futures,
including account management, position handling, and order execution.

Based on nofx/trader/aster_trader.go implementation.
"""

import time
import json
import asyncio
from typing import Dict, List, Optional
from decimal import Decimal
import httpx
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_abi import encode
from web3 import Web3
from loguru import logger

from .base_dex import BaseDEXToolkit


class AsterToolkit(BaseDEXToolkit):
    """
    Aster DEX trading toolkit with Web3 wallet authentication.
    
    Features:
    - EIP-191 message signing
    - Automatic precision handling
    - Order retries on network errors
    - Full perpetual futures support
    """

    BASE_URL = "https://fapi.asterdex.com"
    RECV_WINDOW = "50000"  # milliseconds
    
    def __init__(self, user: str, signer: str, private_key: str, hedge_mode: bool = False):
        """
        Initialize Aster toolkit.
        
        Args:
            user: Main wallet address (ERC20)
            signer: API wallet address
            private_key: API wallet private key (without 0x prefix)
            hedge_mode: Whether account uses dual-position mode (default: False for one-way mode)
        """
        self.user = user
        self.signer = signer
        self.hedge_mode = hedge_mode
        
        # Initialize eth account
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        self.account = Account.from_key(private_key)
        
        # HTTP client with reasonable timeouts
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5)
        )
        
        # Cache for symbol precision
        self._precision_cache: Dict[str, Dict] = {}
        
        logger.info(f"Initialized AsterToolkit for user={user[:8]}..., signer={signer[:8]}...")

    def _gen_nonce(self) -> int:
        """Generate microsecond timestamp as nonce."""
        return int(time.time() * 1_000_000)

    async def _get_precision(self, symbol: str) -> Dict:
        """
        Get price and quantity precision for a symbol.
        
        Returns:
            Dict with price_precision, quantity_precision, tick_size, step_size
        """
        if symbol in self._precision_cache:
            return self._precision_cache[symbol]
        
        # Fetch exchange info
        response = await self.client.get(f"{self.BASE_URL}/fapi/v3/exchangeInfo")
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

    def _normalize_params(self, params: Dict) -> Dict:
        """
        Recursively normalize parameters (sort keys, convert to strings).
        
        This is required for consistent signature generation.
        """
        if isinstance(params, dict):
            return {k: self._normalize_params(v) for k, v in sorted(params.items())}
        elif isinstance(params, list):
            return [self._normalize_params(item) for item in params]
        elif isinstance(params, (int, float, bool)):
            return str(params)
        else:
            return params

    async def _sign_request(self, params: Dict, nonce: int) -> Dict:
        """
        Sign request parameters using EIP-191 signature.
        
        Based on Aster V3 API specification:
        1. Normalize params and convert to JSON string
        2. ABI encode (json_str, user, signer, nonce)
        3. Keccak256 hash
        4. Sign with EIP-191 (encode_defunct)
        
        Args:
            params: Request parameters
            nonce: Unique nonce (microsecond timestamp)
            
        Returns:
            Parameters with signature, nonce, user, signer added
        """
        # Add timestamp and recvWindow
        params["recvWindow"] = self.RECV_WINDOW
        params["timestamp"] = str(int(time.time() * 1000))
        
        # Normalize and serialize parameters
        normalized = self._normalize_params(params)
        json_str = json.dumps(normalized, separators=(',', ':'))
        
        # ABI encode: (string, address, address, uint256)
        encoded = encode(
            ['string', 'address', 'address', 'uint256'],
            [json_str, self.user, self.signer, nonce]
        )
        
        # Keccak256 hash
        keccak_hash = Web3.keccak(encoded)
        
        # Create EIP-191 signable message
        signable_message = encode_defunct(hexstr=keccak_hash.hex())
        
        # Sign with private key
        signed_message = Account.sign_message(signable_message, private_key=self.account.key)
        
        # Add signature params
        params["user"] = self.user
        params["signer"] = self.signer
        params["signature"] = '0x' + signed_message.signature.hex()
        params["nonce"] = nonce
        
        return params

    async def _request(
        self, method: str, endpoint: str, params: Dict, max_retries: int = 3
    ) -> Dict:
        """
        Make HTTP request with signing and retry logic.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            max_retries: Number of retries on network errors
            
        Returns:
            Response JSON
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                # Generate nonce and sign
                nonce = self._gen_nonce()
                signed_params = await self._sign_request(params.copy(), nonce)
                
                # Make request based on method
                if method == "POST":
                    response = await self.client.post(url, data=signed_params)
                elif method == "DELETE":
                    response = await self.client.delete(url, params=signed_params)
                else:  # GET
                    response = await self.client.get(url, params=signed_params)
                
                response.raise_for_status()
                return response.json()
                
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1.0
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts: {e}")
                    raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise

    async def get_account_balance(self) -> Dict:
        """Get account balance information."""
        data = await self._request("GET", "/fapi/v3/balance", {})
        
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
        # This gives the true account value including open positions
        total_balance = wallet_balance + unrealized_profit
        
        return {
            "total_wallet_balance": total_balance,
            "available_balance": available_balance,
            "total_unrealized_profit": unrealized_profit,
        }

    async def get_positions(self) -> List[Dict]:
        """Get current open positions."""
        data = await self._request("GET", "/fapi/v3/positionRisk", {})
        
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
            f"{self.BASE_URL}/fapi/v3/ticker/price",
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
            f"{self.BASE_URL}/fapi/v3/klines",
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
            "/fapi/v3/leverage",
            {"symbol": symbol, "leverage": leverage}
        )

    async def _cancel_all_orders(self, symbol: str) -> None:
        """Cancel all open orders for a symbol."""
        try:
            await self._request("DELETE", "/fapi/v3/allOpenOrders", {"symbol": symbol})
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
                    result = await self._request("POST", "/fapi/v3/order", params)
                    results["take_profit"] = result
                    logger.info(
                        f"Placed take-profit for {symbol} {side}: stopPrice={stop_price_str}, quantity={qty_str}"
                    )
                except Exception as exc:  # pragma: no cover - runtime safety
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
                    result = await self._request("POST", "/fapi/v3/order", params)
                    results["stop_loss"] = result
                    logger.info(
                        f"Placed stop-loss for {symbol} {side}: stopPrice={stop_price_str}, quantity={qty_str}"
                    )
                except Exception as exc:  # pragma: no cover - runtime safety
                    logger.error(f"Failed to place stop-loss order: {exc}")

        return results

    async def open_long(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """Open a long position."""
        # Cancel any existing orders
        await self._cancel_all_orders(symbol)
        
        # Set leverage
        await self._set_leverage(symbol, leverage)
        
        # Get current price and precision
        price = await self.get_market_price(symbol)
        precision = await self._get_precision(symbol)
        
        # Use limit order at slightly higher price to ensure fill
        limit_price = price * 1.01
        
        # Format price and quantity
        price_str = self._format_value(
            limit_price,
            precision["price_precision"],
            precision["tick_size"]
        )
        qty_str = self._format_value(
            quantity,
            precision["quantity_precision"],
            precision["step_size"]
        )
        
        logger.info(f"Opening LONG {symbol}: quantity={qty_str}, price={price_str}, leverage={leverage}x")
        
        # Prepare order parameters
        order_params = {
            "symbol": symbol,
            "type": "LIMIT",
            "side": "BUY",
            "timeInForce": "GTC",
            "quantity": qty_str,
            "price": price_str,
        }
        
        # Add positionSide only if hedge mode is enabled
        if self.hedge_mode:
            order_params["positionSide"] = "LONG"
        
        # Place order
        result = await self._request("POST", "/fapi/v3/order", order_params)
        
        return {
            "order_id": result.get("orderId"),
            "symbol": symbol,
            "side": "long",
            "quantity": qty_str,
            "price": price_str,
            "status": result.get("status"),
        }

    async def open_short(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """Open a short position."""
        await self._cancel_all_orders(symbol)
        await self._set_leverage(symbol, leverage)
        
        price = await self.get_market_price(symbol)
        precision = await self._get_precision(symbol)
        
        # Use limit order at slightly lower price
        limit_price = price * 0.99
        
        price_str = self._format_value(
            limit_price,
            precision["price_precision"],
            precision["tick_size"]
        )
        qty_str = self._format_value(
            quantity,
            precision["quantity_precision"],
            precision["step_size"]
        )
        
        logger.info(f"Opening SHORT {symbol}: quantity={qty_str}, price={price_str}, leverage={leverage}x")
        
        # Prepare order parameters
        order_params = {
            "symbol": symbol,
            "type": "LIMIT",
            "side": "SELL",
            "timeInForce": "GTC",
            "quantity": qty_str,
            "price": price_str,
        }
        
        # Add positionSide only if hedge mode is enabled
        if self.hedge_mode:
            order_params["positionSide"] = "SHORT"
        
        # Place order
        result = await self._request("POST", "/fapi/v3/order", order_params)
        
        return {
            "order_id": result.get("orderId"),
            "symbol": symbol,
            "side": "short",
            "quantity": qty_str,
            "price": price_str,
            "status": result.get("status"),
        }

    async def close_position(self, symbol: str, side: str, quantity: float | None = None) -> Dict:
        """Close an existing position. Optional partial quantity supported."""
        # Get current position
        positions = await self.get_positions()
        position = next((p for p in positions if p["symbol"] == symbol and p["side"] == side), None)
        
        if not position:
            raise ValueError(f"No {side} position found for {symbol}")
        
        position_amt = position["position_amt"]
        target_qty = position_amt if quantity is None else min(abs(quantity), position_amt)
        if target_qty <= 0:
            raise ValueError("Close quantity must be positive")
        price = await self.get_market_price(symbol)
        precision = await self._get_precision(symbol)
        
        # Opposite side to close
        order_side = "SELL" if side == "long" else "BUY"
        limit_price = price * 0.99 if side == "long" else price * 1.01
        
        price_str = self._format_value(
            limit_price,
            precision["price_precision"],
            precision["tick_size"]
        )
        qty_str = self._format_value(
            target_qty,
            precision["quantity_precision"],
            precision["step_size"]
        )
        
        logger.info(f"Closing {side.upper()} {symbol}: quantity={qty_str}")
        
        # Prepare order parameters
        order_params = {
            "symbol": symbol,
            "type": "LIMIT",
            "side": order_side,
            "timeInForce": "GTC",
            "quantity": qty_str,
            "price": price_str,
            "reduceOnly": "true",
        }
        
        # Add positionSide only if hedge mode is enabled
        if self.hedge_mode:
            position_side = "LONG" if side == "long" else "SHORT"
            order_params["positionSide"] = position_side
        
        # Place order
        result = await self._request("POST", "/fapi/v3/order", order_params)
        
        # Cancel remaining orders
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

    async def get_user_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict]:
        """
        Get account trade history from Aster DEX.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT"). If None, returns trades for all symbols.
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Max number of trades to return (max 1000)
            
        Returns:
            List of trade records with PnL, prices, quantities, etc.
            
        Note:
            - If start_time and end_time are not sent, returns last 7 days
            - Time range cannot exceed 7 days
        """
        # Build params
        params = {
            "limit": min(limit, 1000)
        }
        
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        # Fetch trades
        if symbol:
            # Single symbol query
            data = await self._request("GET", "/fapi/v1/userTrades", params)
        else:
            # Query all symbols (need to get from positions/balance)
            # For now, just query common symbols
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
                "side": t.get("side"),  # BUY or SELL
                "position_side": t.get("positionSide"),  # LONG or SHORT
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
        trades.sort(key=lambda x: x["time"], reverse=True)
        
        return trades

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

