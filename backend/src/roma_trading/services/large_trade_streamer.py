import asyncio
import json
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Deque, Dict, List, Literal, Optional, Callable, Awaitable
from contextlib import contextmanager

from websockets.legacy.client import connect as ws_connect
from websockets.exceptions import ConnectionClosed, InvalidState
from loguru import logger

from hyperliquid.utils import constants as hl_constants
from hyperliquid.info import Info as HyperliquidInfo
from roma_trading.storage import get_storage_factory
from roma_trading.services.base_service import BaseService

DexName = Literal["aster", "hyperliquid"]


@dataclass
class LargeTradeRecord:
    """Normalized large trade entry."""

    symbol: str
    price: float
    quantity: float
    quote_quantity: float
    side: Literal["BUY", "SELL"]
    timestamp: datetime
    dex: DexName
    trade_id: str

    def to_json(self) -> str:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def from_json(cls, payload: str) -> "LargeTradeRecord":
        data = json.loads(payload)
        timestamp = datetime.fromisoformat(data["timestamp"])
        # Ensure timestamp is timezone-aware (assume UTC if naive)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        data["timestamp"] = timestamp
        return cls(**data)


class LargeTradeStore:
    """Persist large trades using storage abstraction."""

    def __init__(
        self,
        file_path: Path = None,
        max_records: int = 2000,
        storage_factory=None,
    ):
        """
        Initialize large trade store.
        
        Args:
            file_path: Path to JSONL file (legacy, used if storage_factory uses file storage)
            max_records: Maximum records to keep in memory cache
            storage_factory: Optional storage factory (uses global if not provided)
        """
        # Get storage instance from factory
        if storage_factory is None:
            storage_factory = get_storage_factory()
        
        self.storage_factory = storage_factory
        self.large_trade_storage = storage_factory.create_large_trade_storage(max_records=max_records)
        
        self.max_records = max_records
        self._records: Deque[LargeTradeRecord] = deque(maxlen=max_records)
        self._lock = asyncio.Lock()
        self._append_subscribers: List[Callable[[LargeTradeRecord], Awaitable[None]]] = []
        
        # Load existing into cache
        self._load_existing()

    def _load_existing(self) -> None:
        """Load existing records into memory cache."""
        # Query recent records from storage
        try:
            result = self.large_trade_storage.query(limit=self.max_records, offset=0)
            trades = result.get("trades", [])
            
            # Convert to LargeTradeRecord and add to cache
            for trade_dict in trades:
                try:
                    record = LargeTradeRecord(
                        symbol=trade_dict["symbol"],
                        price=trade_dict["price"],
                        quantity=trade_dict["quantity"],
                        quote_quantity=trade_dict["quote_quantity"],
                        side=trade_dict["side"],
                        timestamp=datetime.fromisoformat(trade_dict["timestamp"]),
                        dex=trade_dict["dex"],
                        trade_id=trade_dict["trade_id"],
                    )
                    self._records.append(record)
                except Exception as e:
                    logger.warning(f"Failed to load trade record: {e}")
            
            logger.info(f"Loaded {len(trades)} large trades into cache")
        except Exception as e:
            logger.warning(f"Failed to load existing trades: {e}")

    async def append(self, record: LargeTradeRecord) -> None:
        """Append record to memory cache and storage."""
        async with self._lock:
            self._records.append(record)
        
        # Save to storage
        try:
            await self.large_trade_storage.append(record)
        except Exception as e:
            logger.error(f"Failed to save large trade to storage: {e}")
        
        # Notify subscribers without blocking append
        for subscriber in list(self._append_subscribers):
            try:
                asyncio.create_task(subscriber(record))
            except Exception as exc:
                logger.warning(f"Error notifying LargeTradeStore subscriber: {exc}", exc_info=True)

    def register_append_subscriber(
        self,
        subscriber: Callable[[LargeTradeRecord], Awaitable[None]],
    ) -> None:
        """Register an async callback to be notified when a new record is appended."""
        self._append_subscribers.append(subscriber)

    def query(
        self,
        dex: Optional[DexName] = None,
        symbol: Optional[str] = None,
        side: Optional[Literal["BUY", "SELL"]] = None,
        min_amount: float = 100_000,
        time_window: str = "24h",
        limit: int = 100,
        offset: int = 0,
    ) -> Dict:
        """Query large trades from storage."""
        return self.large_trade_storage.query(
            dex=dex,
            symbol=symbol,
            side=side,
            min_amount=min_amount,
            time_window=time_window,
            limit=limit,
            offset=offset,
        )
    
    def _query_legacy(
        self,
        dex: Optional[DexName] = None,
        symbol: Optional[str] = None,
        side: Optional[Literal["BUY", "SELL"]] = None,
        min_amount: float = 100_000,
        time_window: str = "24h",
        limit: int = 100,
        offset: int = 0,
    ) -> Dict:
        """
        Legacy query method (kept for reference).
        """
        start_time = self._parse_time_window(time_window)
        
        if False:  # Legacy code removed
            # Query from database
            try:
                from roma_trading.database.base import get_async_session
                from roma_trading.database.services import LargeTradeService
                
                async def _query():
                    async for session in get_async_session():
                        try:
                            db_trades, total = await LargeTradeService.query_large_trades(
                                session=session,
                                dex=dex,
                                symbol=symbol,
                                side=side,
                                min_amount=min_amount,
                                start_time=start_time,
                                limit=limit,
                                offset=offset,
                            )
                            
                            # Convert to response format
                            trades = [
                                {
                                    "symbol": t.symbol,
                                    "price": t.price,
                                    "quantity": t.quantity,
                                    "quote_quantity": t.quote_quantity,
                                    "timestamp": t.timestamp.isoformat(),
                                    "is_buyer_maker": t.side == "SELL",
                                    "dex": t.dex,
                                    "trade_id": t.trade_id,
                                    "side": t.side,
                                }
                                for t in db_trades
                            ]
                            
                            # Calculate stats from all filtered trades (need to query without limit)
                            all_trades, _ = await LargeTradeService.query_large_trades(
                                session=session,
                                dex=dex,
                                symbol=symbol,
                                side=side,
                                min_amount=min_amount,
                                start_time=start_time,
                                limit=None,
                                offset=0,
                            )
                            stats = self._calculate_stats_from_db(all_trades)
                            
                            return {
                                "trades": trades,
                                "stats": stats,
                                "pagination": {
                                    "total": total,
                                    "limit": limit,
                                    "offset": offset,
                                },
                            }
                        finally:
                            await session.close()
                
                # Run async query
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, we need to use a different approach
                        # For now, fall back to memory cache
                        logger.warning("Event loop is running, falling back to memory cache query")
                        return self._query_from_cache(dex, symbol, side, min_amount, start_time, limit, offset)
                    else:
                        return loop.run_until_complete(_query())
                except RuntimeError:
                    return asyncio.run(_query())
            except Exception as e:
                logger.warning(f"Failed to query from database: {e}, falling back to cache")
                return self._query_from_cache(dex, symbol, side, min_amount, start_time, limit, offset)
        else:
            # Query from memory cache
            return self._query_from_cache(dex, symbol, side, min_amount, start_time, limit, offset)
    
    def _query_from_cache(
        self,
        dex: Optional[DexName],
        symbol: Optional[str],
        side: Optional[Literal["BUY", "SELL"]],
        min_amount: float,
        start_time: datetime,
        limit: int,
        offset: int,
    ) -> Dict:
        """Query from memory cache."""
        filtered: List[LargeTradeRecord] = []

        # Ensure start_time is timezone-aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)

        with self._records_lockless_snapshot() as snapshot:
            for record in reversed(snapshot):
                # Ensure record timestamp is timezone-aware
                record_timestamp = record.timestamp
                if record_timestamp.tzinfo is None:
                    record_timestamp = record_timestamp.replace(tzinfo=timezone.utc)
                
                if record_timestamp < start_time:
                    break
                if dex and record.dex != dex:
                    continue
                if symbol and record.symbol != symbol:
                    continue
                if side and record.side != side:
                    continue
                if record.quote_quantity < min_amount:
                    continue
                filtered.append(record)

        # Apply pagination
        if limit is not None and limit > 0:
            paginated = filtered[offset : offset + limit]
        else:
            paginated = filtered[offset:]
        
        stats = self._calculate_stats(filtered)
        
        return {
            "trades": [
                {
                    "symbol": r.symbol,
                    "price": r.price,
                    "quantity": r.quantity,
                    "quote_quantity": r.quote_quantity,
                    "timestamp": r.timestamp.isoformat(),
                    "is_buyer_maker": r.side == "SELL",
                    "dex": r.dex,
                    "trade_id": r.trade_id,
                    "side": r.side,
                }
                for r in paginated
            ],
            "stats": stats,
            "pagination": {
                "total": len(filtered),
                "limit": limit or len(paginated),
                "offset": offset,
            },
        }
    
    @staticmethod
    def _calculate_stats_from_db(trades: List) -> Dict:
        """Calculate stats from database trade objects."""
        if not trades:
            return {
                "total_count": 0,
                "total_volume": 0.0,
                "buy_count": 0,
                "sell_count": 0,
                "buy_volume": 0.0,
                "sell_volume": 0.0,
                "symbol_distribution": {},
            }
        total_volume = sum(t.quote_quantity for t in trades)
        buy_trades = [t for t in trades if t.side == "BUY"]
        sell_trades = [t for t in trades if t.side == "SELL"]
        symbol_dist: Dict[str, int] = {}
        for trade in trades:
            symbol_dist[trade.symbol] = symbol_dist.get(trade.symbol, 0) + 1
        return {
            "total_count": len(trades),
            "total_volume": total_volume,
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "buy_volume": sum(t.quote_quantity for t in buy_trades),
            "sell_volume": sum(t.quote_quantity for t in sell_trades),
            "symbol_distribution": symbol_dist,
        }

    @staticmethod
    def _parse_time_window(time_window: str) -> datetime:
        now = datetime.now(timezone.utc)
        if time_window == "1h":
            return now - timedelta(hours=1)
        if time_window == "6h":
            return now - timedelta(hours=6)
        return now - timedelta(hours=24)

    @staticmethod
    def _calculate_stats(trades: List[LargeTradeRecord]) -> Dict:
        if not trades:
            return {
                "total_count": 0,
                "total_volume": 0.0,
                "buy_count": 0,
                "sell_count": 0,
                "buy_volume": 0.0,
                "sell_volume": 0.0,
                "symbol_distribution": {},
            }
        total_volume = sum(t.quote_quantity for t in trades)
        buy_trades = [t for t in trades if t.side == "BUY"]
        sell_trades = [t for t in trades if t.side == "SELL"]
        symbol_dist: Dict[str, int] = {}
        for trade in trades:
            symbol_dist[trade.symbol] = symbol_dist.get(trade.symbol, 0) + 1
        return {
            "total_count": len(trades),
            "total_volume": total_volume,
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "buy_volume": sum(t.quote_quantity for t in buy_trades),
            "sell_volume": sum(t.quote_quantity for t in sell_trades),
            "symbol_distribution": symbol_dist,
        }

    @contextmanager
    def _records_lockless_snapshot(self):
        yield list(self._records)


class LargeTradeStreamer(BaseService):
    """Background service that ingests WebSocket streams and stores large trades."""

    def __init__(
        self,
        store: LargeTradeStore,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        config: Optional[Dict] = None,
    ):
        super().__init__()
        self.store = store
        self.loop = loop or asyncio.get_event_loop()
        self.config = config or DEFAULT_STREAM_CONFIG
        self._stop_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []
        self._hyperliquid_info: Optional[HyperliquidInfo] = None

    async def _start(self):
        logger.info("Starting large trade streamer...")
        if "aster" in self.config:
            self._tasks.append(asyncio.create_task(self._run_aster_stream()))
        if "hyperliquid" in self.config:
            self._tasks.append(asyncio.create_task(self._run_hyperliquid_stream()))

    async def _stop(self):
        logger.info("Stopping large trade streamer...")
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self._hyperliquid_info:
            try:
                self._hyperliquid_info.disconnect_websocket()
            except Exception:
                pass

    async def _run_aster_stream(self):
        symbols = self.config["aster"]["symbols"]
        url = "wss://fstream.asterdex.com/ws"
        params = [f"{symbol.lower()}@aggTrade" for symbol in symbols]
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": params,
            "id": 1,
        }
        logger.info(f"Aster WebSocket subscribing to: {params}")
        
        reconnect_delay = 5
        max_reconnect_delay = 60
        consecutive_errors = 0
        
        while not self._stop_event.is_set():
            ws = None
            try:
                # Use longer ping interval and timeout for stability
                ws = await ws_connect(
                    url,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10,   # Wait 10 seconds for pong
                    close_timeout=10,
                    max_size=10 * 1024 * 1024,  # 10MB max message size
                )
                await ws.send(json.dumps(subscribe_msg))
                logger.info("Aster WebSocket connected and subscribed")
                consecutive_errors = 0
                reconnect_delay = 5  # Reset delay on successful connection
                
                async for message in ws:
                    if self._stop_event.is_set():
                        break
                    try:
                        await self._handle_aster_message(message)
                    except Exception as exc:
                        logger.warning(f"Error handling Aster message: {exc}")
                        # Continue processing other messages
                        continue
                        
            except ConnectionClosed as exc:
                if self._stop_event.is_set():
                    break
                consecutive_errors += 1
                logger.warning(f"Aster WebSocket connection closed: {exc.code} {exc.reason}")
            except (InvalidState, asyncio.TimeoutError) as exc:
                if self._stop_event.is_set():
                    break
                consecutive_errors += 1
                logger.warning(f"Aster WebSocket connection error: {exc}")
            except Exception as exc:
                if self._stop_event.is_set():
                    break
                consecutive_errors += 1
                logger.error(f"Aster WebSocket error: {exc}", exc_info=True)
            finally:
                # Ensure WebSocket is properly closed
                if ws is not None:
                    try:
                        await ws.close()
                    except Exception:
                        pass
            
            if self._stop_event.is_set():
                break
                
            # Exponential backoff with max delay
            delay = min(reconnect_delay * (2 ** min(consecutive_errors - 1, 4)), max_reconnect_delay)
            logger.info(f"Reconnecting Aster WebSocket in {delay} seconds... (attempt {consecutive_errors})")
            await asyncio.sleep(delay)

    async def _handle_aster_message(self, message: str):
        data = json.loads(message)
        payload = data.get("data") if "data" in data else data
        if not isinstance(payload, dict):
            return
        if payload.get("e") != "aggTrade":
            return
        symbol = payload.get("s")
        if not symbol:
            return
        price = float(payload.get("p", 0))
        qty = float(payload.get("q", 0))
        quote = price * qty
        threshold = self._get_threshold("aster", symbol)
        if quote < threshold:
            return
        side = "SELL" if payload.get("m") else "BUY"
        record = LargeTradeRecord(
            symbol=symbol,
            price=price,
            quantity=qty,
            quote_quantity=quote,
            side=side,
            timestamp=datetime.fromtimestamp(payload.get("T", 0) / 1000, tz=timezone.utc),
            dex="aster",
            trade_id=str(payload.get("a", "")),
        )
        await self.store.append(record)

    async def _run_hyperliquid_stream(self):
        symbols = self.config["hyperliquid"]["symbols"]
        logger.info(f"Hyperliquid WebSocket subscribing to trades: {symbols}")
        self._hyperliquid_info = HyperliquidInfo(hl_constants.MAINNET_API_URL, skip_ws=False)
        for coin in symbols:
            subscription = {"type": "trades", "coin": coin}
            self._hyperliquid_info.subscribe(
                subscription,
                lambda msg, coin=coin: self._handle_hyperliquid_message(coin, msg),
            )
        while not self._stop_event.is_set():
            await asyncio.sleep(1)

    def _handle_hyperliquid_message(self, coin: str, message: Dict):
        trades = message.get("data", [])
        if not trades:
            return
        for trade in trades:
            try:
                px = float(trade.get("px", 0))
                qty = float(trade.get("sz", 0))
                quote = abs(px * qty)
                symbol = f"{coin}USDT"
                threshold = self._get_threshold("hyperliquid", symbol)
                if quote < threshold:
                    continue
                side = "BUY" if trade.get("side") == "B" else "SELL"
                record = LargeTradeRecord(
                    symbol=symbol,
                    price=px,
                    quantity=qty,
                    quote_quantity=quote,
                    side=side,
                    timestamp=datetime.fromtimestamp(trade.get("time", 0) / 1000, tz=timezone.utc),
                    dex="hyperliquid",
                    trade_id=str(trade.get("hash", "")),
                )
                asyncio.run_coroutine_threadsafe(self.store.append(record), self.loop)
            except Exception as exc:
                logger.warning(f"Failed to process Hyperliquid trade: {exc}", exc_info=True)

    def _get_threshold(self, dex: DexName, symbol: str) -> float:
        dex_conf = self.config.get(dex, {})
        thresholds = dex_conf.get("thresholds", {})
        return thresholds.get(symbol, dex_conf.get("default_threshold", 100_000))


DEFAULT_STREAM_CONFIG = {
    "aster": {
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"],
        "default_threshold": 100_000,
        "thresholds": {"BTCUSDT": 250_000, "ETHUSDT": 150_000},
    },
    "hyperliquid": {
        "symbols": ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP", "LINK", "MATIC", "ARB"],
        "default_threshold": 100_000,
        "thresholds": {"BTCUSDT": 250_000, "ETHUSDT": 150_000},
    },
}
