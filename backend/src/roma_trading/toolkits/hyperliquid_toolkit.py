"""
Hyperliquid DEX Toolkit - Complete implementation with BaseDEXToolkit interface.

This toolkit provides full trading functionality for Hyperliquid perpetual futures,
mapping SDK responses to normalized internal format compatible with Aster toolkit.
"""

import time
import asyncio
from typing import Dict, List, Optional
from loguru import logger

try:
    import eth_account
    from eth_account.signers.local import LocalAccount
    from hyperliquid.info import Info
    from hyperliquid.exchange import Exchange
    from hyperliquid.utils import constants
    HYPERLIQUID_AVAILABLE = True
except ImportError:
    HYPERLIQUID_AVAILABLE = False
    logger.warning("hyperliquid-python-sdk not installed. HyperliquidToolkit will not work.")

from .base_dex import BaseDEXToolkit


# Symbol mapping: internal format (BTCUSDT) -> Hyperliquid format (BTC)
SYMBOL_MAP = {
    "BTCUSDT": "BTC",
    "ETHUSDT": "ETH",
    "SOLUSDT": "SOL",
    "BNBUSDT": "BNB",
    "DOGEUSDT": "DOGE",
    "XRPUSDT": "XRP",
}

REVERSE_SYMBOL_MAP = {v: k for k, v in SYMBOL_MAP.items()}


class HyperliquidToolkit(BaseDEXToolkit):
    """
    Hyperliquid trading toolkit with Web3 wallet authentication.
    
    Features:
    - EIP-191 message signing via SDK
    - Automatic symbol mapping
    - Full perpetual futures support
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        account_id: Optional[str] = None,
        testnet: bool = False,
        hedge_mode: bool = False
    ):
        """
        Initialize Hyperliquid toolkit.
        
        Args:
            api_key: Not used directly (Hyperliquid uses account_address)
            api_secret: API wallet private key for signing transactions (without 0x prefix).
                       This is the private key of the API wallet, NOT the main wallet.
            account_id: Main wallet address (for querying balance and state).
                       This should be your MAIN wallet address that holds funds,
                       NOT the API wallet address.
                       If None, will use wallet address derived from api_secret (not recommended).
            testnet: Whether to use testnet
            hedge_mode: Whether account uses hedge mode (default: False)
        
        Note:
            Hyperliquid uses two addresses:
            1. Main Wallet Address: Your actual wallet that holds funds (use for account_id)
            2. API Wallet Address: Derived from api_secret, authorized for trading (used for signing)
            
            Always set account_id to your MAIN wallet address to query correct balance.
        """
        if not HYPERLIQUID_AVAILABLE:
            raise ImportError("hyperliquid-python-sdk is required. Install with: pip install hyperliquid-python-sdk")
        
        self.testnet = testnet
        self.hedge_mode = hedge_mode
        
        # Determine base URL
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        
        # Initialize wallet from private key
        if api_secret.startswith("0x"):
            secret_key = api_secret
        else:
            secret_key = "0x" + api_secret
        
        self.wallet: LocalAccount = eth_account.Account.from_key(secret_key)
        
        # Use account_id if provided, otherwise use wallet address
        self.account_address = account_id or self.wallet.address
        
        # Initialize Info and Exchange
        self.info = Info(base_url, skip_ws=True)
        self.exchange = Exchange(
            self.wallet,
            base_url,
            account_address=self.account_address
        )
        
        logger.info(
            f"Initialized HyperliquidToolkit: account_address={self.account_address}, "
            f"wallet_address={self.wallet.address}, "
            f"account_id_provided={account_id is not None}, "
            f"testnet={testnet}, hedge_mode={hedge_mode}"
        )
        if account_id and account_id != self.wallet.address:
            logger.info(f"Using provided account_id: {account_id} (different from wallet address)")
        else:
            logger.info(f"Using wallet address as account address: {self.wallet.address}")
        
        # Cache for symbol precision (Hyperliquid uses szDecimals)
        self._precision_cache: Dict[str, int] = {}
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Convert internal symbol (BTCUSDT) to Hyperliquid format (BTC)."""
        return SYMBOL_MAP.get(symbol, symbol.replace("USDT", ""))
    
    def _denormalize_symbol(self, symbol: str) -> str:
        """Convert Hyperliquid symbol (BTC) to internal format (BTCUSDT)."""
        return REVERSE_SYMBOL_MAP.get(symbol, symbol + "USDT")
    
    def _get_precision(self, symbol: str) -> int:
        """Get size decimals for a symbol (cached)."""
        normalized = self._normalize_symbol(symbol)
        if normalized in self._precision_cache:
            return self._precision_cache[normalized]
        
        # Get precision from meta
        try:
            coin = self.info.name_to_coin.get(normalized, normalized)
            asset = self.info.coin_to_asset.get(coin)
            if asset is not None:
                decimals = self.info.asset_to_sz_decimals.get(asset, 8)
                self._precision_cache[normalized] = decimals
                return decimals
        except Exception as e:
            logger.warning(f"Failed to get precision for {symbol}: {e}")
        
        # Default precision
        return 8
    
    def _format_price(self, symbol: str, price: float) -> float:
        """
        Format price according to Hyperliquid rules.
        
        Rules (from Hyperliquid SDK examples):
        - If price > 100,000: round to integer
        - Otherwise: format to 5 significant figures, then round to (max_decimals - szDecimals) decimals
        - For perps: max_decimals = 6
        - For spot: max_decimals = 8
        - Integer prices are always allowed regardless of significant figures
        
        Returns formatted price that Hyperliquid will accept.
        """
        try:
            normalized = self._normalize_symbol(symbol)
            coin = self.info.name_to_coin.get(normalized, normalized)
            asset = self.info.coin_to_asset.get(coin)
            
            if asset is None:
                # Fallback: if price > 100k, round to integer; otherwise 5 sig figs, max 6 decimals
                if price > 100_000:
                    return round(price)
                return round(float(f"{price:.5g}"), 6)
            
            # Check if spot (spot assets start at 10000)
            is_spot = asset >= 10_000
            max_decimals = 8 if is_spot else 6
            
            sz_decimals = self.info.asset_to_sz_decimals.get(asset, 0)
            price_decimals = max_decimals - sz_decimals
            
            # If price > 100,000, round to integer (always allowed)
            if price > 100_000:
                return round(price)
            
            # Format to 5 significant figures first, then round to price_decimals
            formatted = round(float(f"{price:.5g}"), price_decimals)
            
            return formatted
            
        except Exception as e:
            logger.warning(f"Failed to format price for {symbol}: {e}, using fallback")
            # Fallback: if price > 100k, round to integer; otherwise 5 sig figs, max 6 decimals
            if price > 100_000:
                return round(price)
            return round(float(f"{price:.5g}"), 6)
    
    async def get_account_balance(self) -> Dict:
        """Get account balance information."""
        try:
            logger.debug(f"Fetching account balance for address: {self.account_address}")
            user_state = self.info.user_state(self.account_address)
            
            # Debug: log the raw response structure
            logger.debug(f"User state keys: {list(user_state.keys()) if isinstance(user_state, dict) else 'Not a dict'}")
            
            # Hyperliquid user_state structure may vary
            # Try different possible structures
            margin_summary = user_state.get("marginSummary", {})
            if not margin_summary:
                # Alternative structure: check if marginSummary is at top level
                margin_summary = user_state if isinstance(user_state, dict) else {}
            
            # Account value - Hyperliquid returns as string
            account_value_str = (
                margin_summary.get("accountValue") or 
                margin_summary.get("account_value") or 
                user_state.get("accountValue") or 
                "0"
            )
            try:
                account_value = float(str(account_value_str)) if account_value_str else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse accountValue: {account_value_str}")
                account_value = 0.0
            
            # Total margin used - Hyperliquid returns as string
            total_margin_used_str = (
                margin_summary.get("totalMarginUsed") or
                margin_summary.get("total_margin_used") or
                margin_summary.get("marginUsed") or
                "0"
            )
            try:
                total_margin_used = float(str(total_margin_used_str)) if total_margin_used_str else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse totalMarginUsed: {total_margin_used_str}")
                total_margin_used = 0.0
            
            # Withdrawable balance - Hyperliquid returns as string
            withdrawable_str = (
                user_state.get("withdrawable") or
                margin_summary.get("withdrawable") or
                "0"
            )
            try:
                withdrawable = float(str(withdrawable_str)) if withdrawable_str else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Failed to parse withdrawable: {withdrawable_str}")
                withdrawable = 0.0
            
            # Calculate unrealized PnL from positions
            unrealized_profit = 0.0
            asset_positions = user_state.get("assetPositions", [])
            if not asset_positions:
                asset_positions = user_state.get("asset_positions", [])
            
            for asset_pos in asset_positions:
                pos = asset_pos.get("position", {}) if isinstance(asset_pos, dict) else asset_pos
                if isinstance(pos, dict):
                    unrealized_pnl_str = pos.get("unrealizedPnl") or pos.get("unrealized_pnl") or "0"
                    unrealized_profit += float(unrealized_pnl_str) if unrealized_pnl_str else 0.0
            
            # If account_value is 0 but we have withdrawable, use withdrawable as base
            if account_value == 0.0 and withdrawable > 0.0:
                account_value = withdrawable + total_margin_used
                logger.debug(f"Account value was 0, using withdrawable + margin_used: {account_value}")
            
            # Available balance = account value - margin used
            available_balance = account_value - total_margin_used
            
            logger.info(
                f"Hyperliquid balance for {self.account_address}: "
                f"account_value={account_value}, "
                f"margin_used={total_margin_used}, "
                f"withdrawable={withdrawable}, "
                f"available={available_balance}, "
                f"unrealized_pnl={unrealized_profit}, "
                f"positions_count={len(asset_positions)}"
            )
            
            # Warn if account value is 0 but we expect balance
            if account_value == 0.0 and withdrawable == 0.0:
                logger.warning(
                    f"Account balance is 0.0 for address {self.account_address}. "
                    f"Please verify: 1) The account address is correct, "
                    f"2) The account has funds, 3) You're using the correct network (testnet/mainnet)"
                )
            
            return {
                "total_wallet_balance": account_value,  # Includes unrealized PnL
                "available_balance": max(0.0, available_balance),  # Ensure non-negative
                "total_unrealized_profit": unrealized_profit,
            }
        except Exception as e:
            logger.error(f"Failed to get account balance for {self.account_address}: {e}", exc_info=True)
            # Log the raw response for debugging
            try:
                user_state = self.info.user_state(self.account_address)
                logger.error(f"User state response: {user_state}")
            except:
                pass
            raise
    
    async def get_positions(self) -> List[Dict]:
        """Get current open positions."""
        try:
            user_state = self.info.user_state(self.account_address)
            positions = []
            
            for asset_pos in user_state.get("assetPositions", []):
                pos = asset_pos.get("position", {})
                szi = float(pos.get("szi", "0"))
                
                # Skip empty positions
                if abs(szi) < 1e-10:
                    continue
                
                # Determine side
                side = "long" if szi > 0 else "short"
                
                coin = pos.get("coin", "")
                symbol = self._denormalize_symbol(coin)
                
                entry_px = float(pos.get("entryPx", "0")) if pos.get("entryPx") else 0.0
                leverage_obj = pos.get("leverage", {})
                leverage_value = int(float(leverage_obj.get("value", "1")))
                
                liquidation_px = float(pos.get("liquidationPx", "0")) if pos.get("liquidationPx") else 0.0
                unrealized_pnl = float(pos.get("unrealizedPnl", "0"))
                position_value = float(pos.get("positionValue", "0"))
                
                # Calculate mark price from position value and size
                if abs(szi) > 1e-10:
                    mark_price = abs(position_value / szi)
                else:
                    # Fallback: get from all_mids
                    mids = self.info.all_mids()
                    coin_key = self.info.name_to_coin.get(coin, coin)
                    mark_price = float(mids.get(coin_key, "0"))
                
                positions.append({
                    "symbol": symbol,
                    "side": side,
                    "position_amt": abs(szi),
                    "entry_price": entry_px,
                    "mark_price": mark_price,
                    "unrealized_profit": unrealized_pnl,
                    "leverage": leverage_value,
                    "liquidation_price": liquidation_px,
                })
            
            return positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}", exc_info=True)
            raise
    
    async def get_market_price(self, symbol: str) -> float:
        """Get current market price."""
        try:
            normalized = self._normalize_symbol(symbol)
            coin_key = self.info.name_to_coin.get(normalized, normalized)
            mids = self.info.all_mids()
            price = float(mids.get(coin_key, "0"))
            if price == 0:
                raise ValueError(f"Price not found for {symbol}")
            return price
        except Exception as e:
            logger.error(f"Failed to get market price for {symbol}: {e}", exc_info=True)
            raise
    
    async def get_klines(
        self, symbol: str, interval: str = "3m", limit: int = 100
    ) -> List[Dict]:
        """Get historical kline data."""
        try:
            normalized = self._normalize_symbol(symbol)
            
            # Map interval format (3m -> 3m, 1h -> 1h, etc.)
            # Hyperliquid supports: 1m, 5m, 15m, 1h, 4h, 1d
            hl_interval = interval
            
            # Calculate time range
            end_time = int(time.time() * 1000)
            # Estimate start time based on interval
            interval_ms_map = {
                "1m": 60 * 1000,
                "3m": 3 * 60 * 1000,
                "5m": 5 * 60 * 1000,
                "15m": 15 * 60 * 1000,
                "1h": 60 * 60 * 1000,
                "4h": 4 * 60 * 60 * 1000,
                "1d": 24 * 60 * 60 * 1000,
            }
            interval_ms = interval_ms_map.get(hl_interval, 3 * 60 * 1000)
            start_time = end_time - (interval_ms * limit)
            
            candles = self.info.candles_snapshot(normalized, hl_interval, start_time, end_time)
            
            # Convert to standardized format
            klines = []
            for candle in candles:
                klines.append({
                    "open_time": candle.get("t", candle.get("T", 0)),
                    "open": float(candle.get("o", "0")),
                    "high": float(candle.get("h", "0")),
                    "low": float(candle.get("l", "0")),
                    "close": float(candle.get("c", "0")),
                    "volume": float(candle.get("v", "0")),
                    "close_time": candle.get("t", candle.get("T", 0)) + interval_ms - 1,
                })
            
            # Sort by time (oldest first)
            klines.sort(key=lambda x: x["open_time"])
            
            # Return last N candles
            return klines[-limit:] if len(klines) > limit else klines
            
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}", exc_info=True)
            raise
    
    async def _set_leverage(self, symbol: str, leverage: int) -> None:
        """Set leverage for a symbol."""
        try:
            normalized = self._normalize_symbol(symbol)
            # Hyperliquid uses update_leverage method
            # Note: This might need to be implemented based on SDK version
            # For now, leverage is set per-order in Hyperliquid
            # TODO: Implement leverage setting per order
            logger.debug(f"Leverage {leverage}x for {symbol} will be set per order")
        except Exception as e:
            logger.warning(f"Failed to set leverage for {symbol}: {e}")
    
    async def place_take_profit_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        take_profit_pct: float | None,
        stop_loss_pct: float | None,
    ) -> Dict:
        """Place take-profit and stop-loss trigger orders on Hyperliquid."""
        results: Dict[str, Dict] = {}

        if quantity <= 0 or entry_price <= 0:
            logger.warning("Cannot place TP/SL orders due to non-positive quantity or entry price")
            return results

        normalized = self._normalize_symbol(symbol)
        precision = self._get_precision(symbol)
        formatted_qty = round(quantity, precision)

        if formatted_qty <= 0:
            logger.warning("Formatted quantity is zero after precision adjustment; skipping TP/SL placement")
            return results

        def _place_trigger(
            label: str,
            trigger_px: float,
            is_buy: bool,
            tpsl: str,
        ) -> None:
            if trigger_px <= 0:
                logger.warning(f"Skipping {label} for {symbol}: trigger price non-positive")
                return

            formatted_px = self._format_price(symbol, trigger_px)
            order_result = self.exchange.order(
                normalized,
                is_buy=is_buy,
                sz=formatted_qty,
                limit_px=formatted_px,
                order_type={
                    "trigger": {
                        "triggerPx": formatted_px,
                        "isMarket": True,
                        "tpsl": tpsl,
                    }
                },
                reduce_only=True,
            )
            results[label] = order_result
            logger.info(
                f"Placed {label} for {symbol} {side}: triggerPx={formatted_px}, quantity={formatted_qty}"
            )

        if take_profit_pct and take_profit_pct > 0:
            if side == "long":
                tp_price = entry_price * (1 + take_profit_pct / 100)
                _place_trigger("take_profit", tp_price, is_buy=False, tpsl="tp")
            else:
                tp_price = entry_price * (1 - take_profit_pct / 100)
                _place_trigger("take_profit", tp_price, is_buy=True, tpsl="tp")

        if stop_loss_pct and stop_loss_pct > 0:
            if side == "long":
                sl_price = entry_price * (1 - stop_loss_pct / 100)
                _place_trigger("stop_loss", sl_price, is_buy=False, tpsl="sl")
            else:
                sl_price = entry_price * (1 + stop_loss_pct / 100)
                _place_trigger("stop_loss", sl_price, is_buy=True, tpsl="sl")

        return results

    async def open_long(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """Open a long position."""
        try:
            normalized = self._normalize_symbol(symbol)
            
            # Set leverage before placing order (cross margin mode)
            try:
                leverage_result = self.exchange.update_leverage(leverage, normalized, is_cross=True)
                if leverage_result.get("status") != "ok":
                    logger.warning(f"Failed to set leverage for {symbol}: {leverage_result}")
                else:
                    logger.debug(f"Set leverage to {leverage}x for {symbol}")
            except Exception as e:
                logger.warning(f"Could not set leverage for {symbol}: {e}. Using existing leverage.")
            
            # Get current price
            price = await self.get_market_price(symbol)
            
            # Use limit order at slightly higher price to ensure fill
            limit_price_raw = price * 1.01
            
            # Format price according to Hyperliquid rules
            limit_price = self._format_price(symbol, limit_price_raw)
            
            # Format quantity to precision
            precision = self._get_precision(symbol)
            formatted_qty = round(quantity, precision)
            
            # Validate minimum order size
            # Hyperliquid typically requires minimum order value of $1 USD
            min_order_value = formatted_qty * limit_price
            if min_order_value < 1.0:
                logger.warning(
                    f"Order value ${min_order_value:.2f} is below minimum $1. "
                    f"Increasing quantity to meet minimum..."
                )
                # Increase to minimum $1 order value
                formatted_qty = max(formatted_qty, round(1.0 / limit_price, precision))
                min_order_value = formatted_qty * limit_price
                logger.info(f"Adjusted quantity to {formatted_qty} (value: ${min_order_value:.2f})")
            
            logger.info(
                f"Opening LONG {symbol} ({normalized}): "
                f"quantity={formatted_qty}, price={limit_price}, leverage={leverage}x, "
                f"order_value=${formatted_qty * limit_price:.2f}, precision={precision}"
            )
            
            # Place order (is_buy=True for long)
            # Order type: limit with GTC (Good Till Cancel)
            order_result = self.exchange.order(
                normalized,
                is_buy=True,
                sz=formatted_qty,
                limit_px=limit_price,
                order_type={"limit": {"tif": "Gtc"}}
            )
            
            # Parse response
            logger.debug(f"Order result: {order_result}")
            
            if order_result.get("status") == "ok":
                response_data = order_result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])
                if statuses:
                    status = statuses[0]
                    if "resting" in status:
                        oid = status["resting"].get("oid")
                        return {
                            "order_id": oid,
                            "symbol": symbol,
                            "side": "long",
                            "quantity": str(formatted_qty),
                            "price": str(limit_price),
                            "status": "resting",
                        }
                    elif "filled" in status:
                        return {
                            "order_id": None,
                            "symbol": symbol,
                            "side": "long",
                            "quantity": str(formatted_qty),
                            "price": str(limit_price),
                            "status": "filled",
                        }
                    elif "error" in status:
                        error_info = status["error"]
                        error_msg = error_info if isinstance(error_info, str) else str(error_info)
                        logger.error(f"Order error in status: {error_info}")
                        raise Exception(f"Order failed: {error_msg}")
            
            # Error case - try to extract error message from various locations
            error_msg = None
            if "response" in order_result:
                response = order_result["response"]
                if isinstance(response, dict):
                    error_msg = (
                        response.get("error") or 
                        response.get("data", {}).get("error") or
                        str(response)
                    )
            
            if not error_msg:
                error_msg = f"Unknown error. Full response: {order_result}"
            
            logger.error(f"Order failed for {symbol}: {error_msg}")
            logger.error(f"Order parameters: symbol={normalized}, is_buy=True, sz={formatted_qty}, limit_px={limit_price}, leverage={leverage}")
            raise Exception(f"Order failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"Failed to open long position for {symbol}: {e}", exc_info=True)
            raise
    
    async def open_short(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """Open a short position."""
        try:
            normalized = self._normalize_symbol(symbol)
            
            # Set leverage before placing order (cross margin mode)
            try:
                leverage_result = self.exchange.update_leverage(leverage, normalized, is_cross=True)
                if leverage_result.get("status") != "ok":
                    logger.warning(f"Failed to set leverage for {symbol}: {leverage_result}")
                else:
                    logger.debug(f"Set leverage to {leverage}x for {symbol}")
            except Exception as e:
                logger.warning(f"Could not set leverage for {symbol}: {e}. Using existing leverage.")
            
            # Get current price
            price = await self.get_market_price(symbol)
            
            # Use limit order at slightly lower price
            limit_price_raw = price * 0.99
            
            # Format price according to Hyperliquid rules
            limit_price = self._format_price(symbol, limit_price_raw)
            
            # Format quantity to precision
            precision = self._get_precision(symbol)
            formatted_qty = round(quantity, precision)
            
            # Validate minimum order size
            # Hyperliquid typically requires minimum order value of $1 USD
            min_order_value = formatted_qty * limit_price
            if min_order_value < 1.0:
                logger.warning(
                    f"Order value ${min_order_value:.2f} is below minimum $1. "
                    f"Increasing quantity to meet minimum..."
                )
                # Increase to minimum $1 order value
                formatted_qty = max(formatted_qty, round(1.0 / limit_price, precision))
                min_order_value = formatted_qty * limit_price
                logger.info(f"Adjusted quantity to {formatted_qty} (value: ${min_order_value:.2f})")
            
            logger.info(
                f"Opening SHORT {symbol} ({normalized}): "
                f"quantity={formatted_qty}, price={limit_price}, leverage={leverage}x, "
                f"order_value=${formatted_qty * limit_price:.2f}, precision={precision}"
            )
            
            # Place order (is_buy=False for short)
            order_result = self.exchange.order(
                normalized,
                is_buy=False,
                sz=formatted_qty,
                limit_px=limit_price,
                order_type={"limit": {"tif": "Gtc"}}
            )
            
            # Parse response
            logger.debug(f"Order result: {order_result}")
            
            if order_result.get("status") == "ok":
                response_data = order_result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])
                if statuses:
                    status = statuses[0]
                    if "resting" in status:
                        oid = status["resting"].get("oid")
                        return {
                            "order_id": oid,
                            "symbol": symbol,
                            "side": "short",
                            "quantity": str(formatted_qty),
                            "price": str(limit_price),
                            "status": "resting",
                        }
                    elif "filled" in status:
                        return {
                            "order_id": None,
                            "symbol": symbol,
                            "side": "short",
                            "quantity": str(formatted_qty),
                            "price": str(limit_price),
                            "status": "filled",
                        }
                    elif "error" in status:
                        error_info = status["error"]
                        error_msg = error_info if isinstance(error_info, str) else str(error_info)
                        logger.error(f"Order error in status: {error_info}")
                        raise Exception(f"Order failed: {error_msg}")
            
            # Error case - try to extract error message from various locations
            error_msg = None
            if "response" in order_result:
                response = order_result["response"]
                if isinstance(response, dict):
                    error_msg = (
                        response.get("error") or 
                        response.get("data", {}).get("error") or
                        str(response)
                    )
            
            if not error_msg:
                error_msg = f"Unknown error. Full response: {order_result}"
            
            logger.error(f"Order failed for {symbol}: {error_msg}")
            logger.error(f"Order parameters: symbol={normalized}, is_buy=False, sz={formatted_qty}, limit_px={limit_price}, leverage={leverage}")
            raise Exception(f"Order failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"Failed to open short position for {symbol}: {e}", exc_info=True)
            raise
    
    async def close_position(self, symbol: str, side: str, quantity: float | None = None) -> Dict:
        """Close an existing position. Supports optional partial quantity."""
        try:
            # Get current position
            positions = await self.get_positions()
            position = next(
                (p for p in positions if p["symbol"] == symbol and p["side"] == side),
                None
            )
            
            if not position:
                raise ValueError(f"No {side} position found for {symbol}")
            
            normalized = self._normalize_symbol(symbol)
            position_amt = position["position_amt"]
            target_qty = position_amt if quantity is None else min(abs(quantity), position_amt)
            if target_qty <= 0:
                raise ValueError("Close quantity must be positive")
            price = await self.get_market_price(symbol)
            
            # Opposite side to close
            # If long, sell to close (is_buy=False)
            # If short, buy to close (is_buy=True)
            is_buy = (side == "short")
            limit_price_raw = price * 0.99 if side == "long" else price * 1.01
            
            # Format price according to Hyperliquid rules
            limit_price = self._format_price(symbol, limit_price_raw)
            
            # Format quantity
            precision = self._get_precision(symbol)
            formatted_qty = round(target_qty, precision)
            
            logger.info(f"Closing {side.upper()} {symbol}: quantity={formatted_qty}")
            
            # Place reduce-only order
            order_result = self.exchange.order(
                normalized,
                is_buy=is_buy,
                sz=formatted_qty,
                limit_px=limit_price,
                order_type={"limit": {"tif": "Gtc"}},
                reduce_only=True
            )
            
            # Parse response
            if order_result.get("status") == "ok":
                response_data = order_result.get("response", {}).get("data", {})
                statuses = response_data.get("statuses", [])
                if statuses:
                    status = statuses[0]
                    if "resting" in status:
                        oid = status["resting"].get("oid")
                        return {
                            "order_id": oid,
                            "symbol": symbol,
                            "closed_side": side,
                            "quantity": str(formatted_qty),
                            "closed_quantity": formatted_qty,
                            "fully_closed": abs(target_qty - position_amt) < 1e-9,
                            "status": "resting",
                        }
                    elif "filled" in status:
                        return {
                            "order_id": None,
                            "symbol": symbol,
                            "closed_side": side,
                            "quantity": str(formatted_qty),
                            "closed_quantity": formatted_qty,
                            "fully_closed": abs(target_qty - position_amt) < 1e-9,
                            "status": "filled",
                        }
            
            # Error case
            error_msg = order_result.get("response", {}).get("error", "Unknown error")
            raise Exception(f"Close order failed: {error_msg}")
            
        except Exception as e:
            logger.error(f"Failed to close position for {symbol}: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Close HTTP client and cleanup."""
        # Hyperliquid SDK doesn't require explicit cleanup
        # but we can disconnect websocket if needed
        try:
            if hasattr(self.info, 'disconnect_websocket'):
                self.info.disconnect_websocket()
        except Exception:
            pass
        logger.info("HyperliquidToolkit closed")
