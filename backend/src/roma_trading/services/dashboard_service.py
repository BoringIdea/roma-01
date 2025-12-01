"""
Dashboard service for large trade monitoring and token rankings.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Literal, Any
import asyncio
from loguru import logger

from roma_trading.api.schemas.dashboard import (
    FundingRateRanking,
    VolumeRanking,
    OpenInterestRanking,
    PriceChangeRanking,
)
from roma_trading.agents import AgentManager
from roma_trading.services.large_trade_streamer import LargeTradeStore


class DashboardService:
    """Dashboard service for market data.

    This service now maintains local snapshots for dashboard data:
    - Snapshots are refreshed periodically by a background task.
    - API handlers should prefer reading from snapshots and fall back to live APIs
      when snapshots are not yet available.
    """
    
    def __init__(
        self,
        agent_manager: AgentManager,
        large_trade_store: Optional[LargeTradeStore] = None,
    ):
        self.agent_manager = agent_manager
        self.large_trade_store = large_trade_store
        self.min_large_trade_amount = 100_000  # 100k USDT

        # Snapshot state
        self._snapshot_lock = asyncio.Lock()
        self._funding_rate_snapshot: Optional[List[FundingRateRanking]] = None
        self._volume_snapshot: Optional[List[VolumeRanking]] = None
        self._price_change_snapshot: Optional[List[PriceChangeRanking]] = None
        self._open_interest_snapshot: Optional[List[OpenInterestRanking]] = None

        # Large trades snapshot (default dashboard view)
        self._large_trades_snapshot: Optional[Dict[str, Any]] = None
        self._large_trades_last_updated: Optional[datetime] = None
        self._large_trades_dirty: bool = False

        # Background updater task
        self._background_task: Optional[asyncio.Task] = None
        self._background_interval_seconds: int = 60
    
    def _get_dex_toolkit(self, dex: Literal["aster", "hyperliquid"]):
        """Get DEX toolkit from agent manager."""
        # Find an agent using the specified DEX
        for agent_id, agent in self.agent_manager.agents.items():
            if hasattr(agent, 'dex') and agent.dex:
                # Check agent config to determine DEX type
                exchange_cfg = agent.config.get("exchange", {})
                agent_dex_type = exchange_cfg.get("type", "aster").lower()
                
                if agent_dex_type == dex:
                    logger.debug(f"Found {dex} toolkit from agent {agent_id}")
                    return agent.dex
        
        # If no agent found, try to create a read-only toolkit for public data
        # This is useful for dashboard data that doesn't require authentication
        if dex == "hyperliquid":
            try:
                from hyperliquid.info import Info
                from hyperliquid.utils import constants
                # Create a minimal read-only Info instance for public data
                # Hyperliquid public API doesn't require authentication
                logger.info("No Hyperliquid agent found, creating read-only Info instance for public data")
                
                # Create a simple wrapper that has the methods we need
                class ReadOnlyHyperliquidToolkit:
                    def __init__(self):
                        self.info = Info(constants.MAINNET_API_URL, skip_ws=True)
                    
                    async def get_meta_and_asset_ctxs(self):
                        return self.info.meta_and_asset_ctxs()
                    
                    async def get_all_mids(self):
                        return self.info.all_mids()
                
                return ReadOnlyHyperliquidToolkit()
            except Exception as e:
                logger.warning(f"Failed to create read-only Hyperliquid toolkit: {e}", exc_info=True)
        
        elif dex == "aster":
            try:
                import httpx
                # Create a minimal read-only Aster toolkit for public data
                # Aster public market data API doesn't require authentication
                logger.info("No Aster agent found, creating read-only toolkit for public data")
                
                # Create a simple wrapper that has the methods we need
                class ReadOnlyAsterToolkit:
                    BASE_URL = "https://fapi.asterdex.com"
                    
                    def __init__(self):
                        self.client = httpx.AsyncClient(
                            timeout=httpx.Timeout(30.0, connect=10.0),
                            limits=httpx.Limits(max_keepalive_connections=5)
                        )
                    
                    async def get_agg_trades(
                        self,
                        symbol: str,
                        start_time: Optional[int] = None,
                        end_time: Optional[int] = None,
                        limit: int = 500
                    ) -> List[Dict]:
                        """Get aggregated trades from Aster DEX (public API)."""
                        params = {
                            "symbol": symbol,
                            "limit": min(limit, 1000)
                        }
                        if start_time:
                            params["startTime"] = start_time
                        if end_time:
                            params["endTime"] = end_time
                        
                        response = await self.client.get(
                            f"{self.BASE_URL}/fapi/v3/aggTrades",
                            params=params
                        )
                        response.raise_for_status()
                        return response.json()
                    
                    async def get_ticker_24hr(self, symbol: Optional[str] = None) -> List[Dict]:
                        """Get 24hr ticker statistics (public API)."""
                        params = {}
                        if symbol:
                            params["symbol"] = symbol
                        
                        response = await self.client.get(
                            f"{self.BASE_URL}/fapi/v3/ticker/24hr",
                            params=params
                        )
                        response.raise_for_status()
                        data = response.json()
                        return data if isinstance(data, list) else [data]
                    
                    async def get_premium_index(self, symbol: Optional[str] = None) -> List[Dict]:
                        """Get premium index and funding rate (public API)."""
                        params = {}
                        if symbol:
                            params["symbol"] = symbol
                        
                        response = await self.client.get(
                            f"{self.BASE_URL}/fapi/v3/premiumIndex",
                            params=params
                        )
                        response.raise_for_status()
                        data = response.json()
                        return data if isinstance(data, list) else [data]
                    
                    async def close(self):
                        """Close HTTP client."""
                        await self.client.aclose()
                
                return ReadOnlyAsterToolkit()
            except Exception as e:
                logger.warning(f"Failed to create read-only Aster toolkit: {e}", exc_info=True)
        
        # If no agent found, return None
        # The caller should handle this gracefully
        logger.warning(f"No agent found with DEX type: {dex}. Available agents: {list(self.agent_manager.agents.keys())}")
        return None

    async def start_background_updater(self, interval_seconds: int = 60) -> None:
        """Start background task that periodically refreshes dashboard snapshots."""
        if self._background_task is not None and not self._background_task.done():
            return

        self._background_interval_seconds = max(10, int(interval_seconds))
        logger.info(
            f"Starting dashboard snapshot background updater "
            f"(interval={self._background_interval_seconds}s)"
        )
        self._background_task = asyncio.create_task(self._run_background_updater())

    async def stop_background_updater(self) -> None:
        """Stop background snapshot updater if running."""
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    async def _run_background_updater(self) -> None:
        """Internal loop that keeps refreshing all dashboard snapshots."""
        while True:
            try:
                await self.refresh_all_snapshots()
            except Exception as exc:
                logger.error(f"Failed to refresh dashboard snapshots: {exc}", exc_info=True)
            await asyncio.sleep(self._background_interval_seconds)

    async def refresh_all_snapshots(self) -> None:
        """Refresh all dashboard snapshots in one batch."""
        logger.debug("Refreshing dashboard snapshots...")

        funding: List[FundingRateRanking] = []
        volume: List[VolumeRanking] = []
        price_change: List[PriceChangeRanking] = []
        open_interest: List[OpenInterestRanking] = []
        large_trades: Optional[Dict[str, Any]] = None

        # Refresh snapshots using existing live API methods
        try:
            funding = await self.get_funding_rate_rankings(dex=None, sort_order="desc", limit=500)
        except Exception as exc:
            logger.warning(f"Failed to refresh funding rate snapshot: {exc}", exc_info=True)

        try:
            volume = await self.get_volume_rankings(dex=None, sort_order="desc", limit=500)
        except Exception as exc:
            logger.warning(f"Failed to refresh volume snapshot: {exc}", exc_info=True)

        try:
            price_change = await self.get_price_change_rankings(dex=None, sort_order="desc", limit=500)
        except Exception as exc:
            logger.warning(f"Failed to refresh price change snapshot: {exc}", exc_info=True)

        try:
            open_interest = await self.get_open_interest_rankings(sort_order="desc", limit=500)
        except Exception as exc:
            logger.warning(f"Failed to refresh open interest snapshot: {exc}", exc_info=True)

        try:
            if self.large_trade_store:
                # Default dashboard snapshot for large trades: 24h, global, descending by time
                large_trades = self.large_trade_store.query(
                    dex=None,
                    symbol=None,
                    side=None,
                    min_amount=self.min_large_trade_amount,
                    time_window="24h",
                    limit=1000,
                    offset=0,
                )
        except Exception as exc:
            logger.warning(f"Failed to refresh large trades snapshot: {exc}", exc_info=True)

        async with self._snapshot_lock:
            self._funding_rate_snapshot = funding
            self._volume_snapshot = volume
            self._price_change_snapshot = price_change
            self._open_interest_snapshot = open_interest
            if large_trades is not None:
                self._large_trades_snapshot = large_trades
                self._large_trades_last_updated = datetime.now(timezone.utc)

        logger.info(
            "Dashboard snapshots refreshed: "
            f"funding={len(funding)}, volume={len(volume)}, "
            f"price_change={len(price_change)}, open_interest={len(open_interest)}, "
            f"large_trades={len(large_trades.get('trades', [])) if large_trades else 0}"
        )

    async def notify_large_trade_appended(self, record: Any) -> None:
        """Mark large trades snapshot as dirty when a new record is appended.

        The next background refresh will rebuild the snapshot. Until then,
        API calls can still fall back to direct store queries.
        """
        async with self._snapshot_lock:
            self._large_trades_dirty = True
    
    async def get_large_trades(
        self,
        dex: Optional[Literal["aster", "hyperliquid"]] = None,
        symbol: Optional[str] = None,
        side: Optional[Literal["BUY", "SELL"]] = None,
        min_amount: float = 100_000,
        time_window: str = "24h",
        limit: int = 100,
        offset: int = 0,
    ) -> Dict:
        """Return large trades from local snapshot if available, otherwise from store.

        Snapshot is only used for the default dashboard view:
        - No filters (dex/symbol/side)
        - 24h window
        For custom filters we query the store directly.
        """
        if not self.large_trade_store:
            raise RuntimeError("Large trade store is not initialized.")

        # Use snapshot only for the default dashboard view (no filters, 24h window)
        is_default_view = (
            dex is None
            and symbol is None
            and side is None
            and time_window == "24h"
            and min_amount == self.min_large_trade_amount
        )

        if is_default_view:
            async with self._snapshot_lock:
                snapshot = None if self._large_trades_dirty else self._large_trades_snapshot

            if snapshot is not None:
                trades = snapshot.get("trades", [])
                # Apply pagination on top of snapshot
                if limit is not None and limit > 0:
                    paginated = trades[offset : offset + limit]
                else:
                    paginated = trades[offset:]

                stats = snapshot.get("stats", {})
                pagination = snapshot.get("pagination", {}).copy()
                pagination.update(
                    {
                        "limit": limit or len(paginated),
                        "offset": offset,
                    }
                )

                return {
                    "trades": paginated,
                    "stats": stats,
                    "pagination": pagination,
                }

        # Fallback: direct query from store
        result = self.large_trade_store.query(
            dex=dex,
            symbol=symbol,
            side=side,
            min_amount=min_amount,
            time_window=time_window,
            limit=limit,
            offset=offset,
        )
        # For default view, update snapshot from fresh query
        if is_default_view:
            async with self._snapshot_lock:
                self._large_trades_snapshot = result
                self._large_trades_last_updated = datetime.now(timezone.utc)
                self._large_trades_dirty = False
        return result
    
    async def get_funding_rate_rankings(
        self,
        dex: Optional[Literal["aster", "hyperliquid"]] = None,
        sort_order: str = "desc",
        limit: int = 20
    ) -> List[FundingRateRanking]:
        """Get funding rate rankings.

        Prefer snapshot data (global view) when available. If a specific DEX filter
        is requested, we filter the snapshot in memory. For non-default sort
        order we sort on the fly.
        """
        # Try snapshot first (only for global data)
        async with self._snapshot_lock:
            snapshot = self._funding_rate_snapshot

        if snapshot is not None:
            rankings = [
                r for r in snapshot
                if dex is None or r.dex == dex
            ]
            rankings.sort(
                key=lambda x: x.funding_rate,
                reverse=(sort_order == "desc"),
            )
            return rankings[:limit]

        # Fallback: live query
        rankings: List[FundingRateRanking] = []
        
        try:
            # Aster data
            if dex is None or dex == "aster":
                aster_toolkit = self._get_dex_toolkit("aster")
                if aster_toolkit and hasattr(aster_toolkit, 'get_premium_index'):
                    try:
                        data = await aster_toolkit.get_premium_index()
                        for item in data:
                            rankings.append(FundingRateRanking(
                                symbol=item.get('symbol', ''),
                                funding_rate=float(item.get('lastFundingRate', 0)) * 100,
                                next_funding_time=datetime.fromtimestamp(
                                    item['nextFundingTime'] / 1000
                                ) if item.get('nextFundingTime') else None,
                                dex="aster"
                            ))
                    except Exception as e:
                        logger.warning(f"Failed to get Aster funding rates: {e}")
            
            # Hyperliquid data
            if dex is None or dex == "hyperliquid":
                hl_toolkit = self._get_dex_toolkit("hyperliquid")
                logger.debug(f"Hyperliquid toolkit: {hl_toolkit is not None}, has method: {hl_toolkit and hasattr(hl_toolkit, 'get_meta_and_asset_ctxs')}")
                if hl_toolkit and hasattr(hl_toolkit, 'get_meta_and_asset_ctxs'):
                    try:
                        logger.debug("Fetching Hyperliquid meta_and_asset_ctxs...")
                        result = await hl_toolkit.get_meta_and_asset_ctxs()
                        logger.debug(f"Got result type: {type(result)}, length: {len(result) if isinstance(result, (list, tuple)) else 'N/A'}")
                        
                        # meta_and_asset_ctxs returns a list: [meta_dict, ctxs_list]
                        if isinstance(result, list) and len(result) >= 2:
                            meta = result[0]
                            ctxs = result[1]
                        elif isinstance(result, tuple) and len(result) >= 2:
                            meta, ctxs = result
                        else:
                            logger.error(f"Unexpected result format from get_meta_and_asset_ctxs: {type(result)}")
                            raise ValueError(f"Unexpected result format: {type(result)}")
                        
                        logger.debug(f"Meta: {meta is not None}, Ctxs: {ctxs is not None}, Universe length: {len(meta.get('universe', [])) if meta else 0}, Ctxs length: {len(ctxs) if ctxs else 0}")
                        
                        if meta and ctxs:
                            universe = meta.get('universe', [])
                            logger.debug(f"Processing {len(universe)} symbols from Hyperliquid")
                            for i, ctx in enumerate(ctxs):
                                if i < len(universe):
                                    symbol_name = universe[i].get('name', '')
                                    if symbol_name:
                                        # Map to USDT pair format
                                        symbol = f"{symbol_name}USDT" if symbol_name != "USDT" else symbol_name
                                        funding_str = ctx.get('funding', '0')
                                        try:
                                            funding_rate = float(funding_str) * 100
                                            rankings.append(FundingRateRanking(
                                                symbol=symbol,
                                                funding_rate=funding_rate,
                                                dex="hyperliquid"
                                            ))
                                            logger.debug(f"Added Hyperliquid funding rate for {symbol}: {funding_rate}%")
                                        except (ValueError, TypeError) as e:
                                            logger.debug(f"Failed to parse funding rate for {symbol_name}: {e}, value: {funding_str}")
                            logger.info(f"Successfully fetched {len([r for r in rankings if r.dex == 'hyperliquid'])} Hyperliquid funding rates")
                    except Exception as e:
                        logger.error(f"Failed to get Hyperliquid funding rates: {e}", exc_info=True)
                else:
                    logger.warning("Hyperliquid toolkit not available or missing get_meta_and_asset_ctxs method")
            
            # Sort
            rankings.sort(
                key=lambda x: x.funding_rate,
                reverse=(sort_order == "desc")
            )
            
            return rankings[:limit]
        except Exception as e:
            logger.error(f"Error getting funding rate rankings: {e}", exc_info=True)
            return []
    
    async def get_volume_rankings(
        self,
        dex: Optional[Literal["aster", "hyperliquid"]] = None,
        sort_order: str = "desc",
        limit: int = 20
    ) -> List[VolumeRanking]:
        """Get volume rankings.

        Prefer snapshot data when available, then fall back to live APIs.
        """
        async with self._snapshot_lock:
            snapshot = self._volume_snapshot

        if snapshot is not None:
            rankings = [
                r for r in snapshot
                if dex is None or r.dex == dex
            ]
            rankings.sort(
                key=lambda x: x.quote_volume_24h,
                reverse=(sort_order == "desc"),
            )
            return rankings[:limit]

        rankings: List[VolumeRanking] = []
        
        try:
            # Aster data
            if dex is None or dex == "aster":
                aster_toolkit = self._get_dex_toolkit("aster")
                if aster_toolkit and hasattr(aster_toolkit, 'get_ticker_24hr'):
                    try:
                        data = await aster_toolkit.get_ticker_24hr()
                        for item in data:
                            rankings.append(VolumeRanking(
                                symbol=item.get('symbol', ''),
                                volume_24h=float(item.get('volume', 0)),
                                quote_volume_24h=float(item.get('quoteVolume', 0)),
                                dex="aster"
                            ))
                    except Exception as e:
                        logger.warning(f"Failed to get Aster volume: {e}")
            
            # Hyperliquid data
            if dex is None or dex == "hyperliquid":
                hl_toolkit = self._get_dex_toolkit("hyperliquid")
                if hl_toolkit and hasattr(hl_toolkit, 'get_meta_and_asset_ctxs'):
                    try:
                        result = await hl_toolkit.get_meta_and_asset_ctxs()
                        # meta_and_asset_ctxs returns a list: [meta_dict, ctxs_list]
                        if isinstance(result, list) and len(result) >= 2:
                            meta = result[0]
                            ctxs = result[1]
                        elif isinstance(result, tuple) and len(result) >= 2:
                            meta, ctxs = result
                        else:
                            logger.error(f"Unexpected result format from get_meta_and_asset_ctxs: {type(result)}")
                            raise ValueError(f"Unexpected result format: {type(result)}")
                        
                        if meta and ctxs:
                            universe = meta.get('universe', [])
                            for i, ctx in enumerate(ctxs):
                                if i < len(universe):
                                    symbol_name = universe[i].get('name', '')
                                    if symbol_name:
                                        symbol = f"{symbol_name}USDT" if symbol_name != "USDT" else symbol_name
                                        volume_str = ctx.get('dayNtlVlm', '0')
                                        try:
                                            quote_volume_24h = float(volume_str)
                                            rankings.append(VolumeRanking(
                                                symbol=symbol,
                                                quote_volume_24h=quote_volume_24h,
                                                dex="hyperliquid"
                                            ))
                                        except (ValueError, TypeError) as e:
                                            logger.debug(f"Failed to parse volume for {symbol_name}: {e}, value: {volume_str}")
                        logger.info(f"Successfully fetched {len([r for r in rankings if r.dex == 'hyperliquid'])} Hyperliquid volume rankings")
                    except Exception as e:
                        logger.error(f"Failed to get Hyperliquid volume: {e}", exc_info=True)
            
            # Sort by quote_volume_24h (default)
            rankings.sort(
                key=lambda x: x.quote_volume_24h,
                reverse=(sort_order == "desc")
            )
            
            return rankings[:limit]
        except Exception as e:
            logger.error(f"Error getting volume rankings: {e}", exc_info=True)
            return []
    
    async def get_price_change_rankings(
        self,
        dex: Optional[Literal["aster", "hyperliquid"]] = None,
        sort_order: str = "desc",
        limit: int = 20
    ) -> List[PriceChangeRanking]:
        """Get 24h price change rankings.

        Prefer snapshot data when available, then fall back to live APIs.
        """
        async with self._snapshot_lock:
            snapshot = self._price_change_snapshot

        if snapshot is not None:
            rankings = [
                r for r in snapshot
                if dex is None or r.dex == dex
            ]
            rankings.sort(
                key=lambda x: x.price_change_percent_24h,
                reverse=(sort_order == "desc"),
            )
            return rankings[:limit]

        rankings: List[PriceChangeRanking] = []
        
        try:
            # Aster data
            if dex is None or dex == "aster":
                aster_toolkit = self._get_dex_toolkit("aster")
                if aster_toolkit and hasattr(aster_toolkit, 'get_ticker_24hr'):
                    try:
                        data = await aster_toolkit.get_ticker_24hr()
                        for item in data:
                            price_change = float(item.get('priceChange', 0))
                            price_change_percent = float(item.get('priceChangePercent', 0))
                            rankings.append(PriceChangeRanking(
                                symbol=item.get('symbol', ''),
                                current_price=float(item.get('lastPrice', 0)),
                                price_change_24h=price_change,
                                price_change_percent_24h=price_change_percent,
                                high_24h=float(item.get('highPrice', 0)) if item.get('highPrice') else None,
                                low_24h=float(item.get('lowPrice', 0)) if item.get('lowPrice') else None,
                                open_24h=float(item.get('openPrice', 0)) if item.get('openPrice') else None,
                                dex="aster"
                            ))
                    except Exception as e:
                        logger.warning(f"Failed to get Aster price changes: {e}")
            
            # Hyperliquid data
            if dex is None or dex == "hyperliquid":
                hl_toolkit = self._get_dex_toolkit("hyperliquid")
                if hl_toolkit and hasattr(hl_toolkit, 'get_meta_and_asset_ctxs'):
                    try:
                        result = await hl_toolkit.get_meta_and_asset_ctxs()
                        # meta_and_asset_ctxs returns a list: [meta_dict, ctxs_list]
                        if isinstance(result, list) and len(result) >= 2:
                            meta = result[0]
                            ctxs = result[1]
                        elif isinstance(result, tuple) and len(result) >= 2:
                            meta, ctxs = result
                        else:
                            logger.error(f"Unexpected result format from get_meta_and_asset_ctxs: {type(result)}")
                            raise ValueError(f"Unexpected result format: {type(result)}")
                        
                        mids = await hl_toolkit.get_all_mids()
                        if meta and ctxs:
                            universe = meta.get('universe', [])
                            for i, ctx in enumerate(ctxs):
                                if i < len(universe):
                                    symbol_name = universe[i].get('name', '')
                                    if symbol_name:
                                        symbol = f"{symbol_name}USDT" if symbol_name != "USDT" else symbol_name
                                        try:
                                            current_price = float(mids.get(symbol_name, 0))
                                            prev_price_str = ctx.get('prevDayPx', '0')
                                            prev_price = float(prev_price_str) if prev_price_str else 0
                                            if prev_price > 0:
                                                price_change = current_price - prev_price
                                                price_change_percent = (price_change / prev_price) * 100
                                            else:
                                                price_change = 0
                                                price_change_percent = 0
                                            
                                            rankings.append(PriceChangeRanking(
                                                symbol=symbol,
                                                current_price=current_price,
                                                price_change_24h=price_change,
                                                price_change_percent_24h=price_change_percent,
                                                dex="hyperliquid"
                                            ))
                                        except (ValueError, TypeError) as e:
                                            logger.debug(f"Failed to parse price change for {symbol_name}: {e}")
                        logger.info(f"Successfully fetched {len([r for r in rankings if r.dex == 'hyperliquid'])} Hyperliquid price change rankings")
                    except Exception as e:
                        logger.error(f"Failed to get Hyperliquid price changes: {e}", exc_info=True)
            
            # Sort by price_change_percent_24h
            rankings.sort(
                key=lambda x: x.price_change_percent_24h,
                reverse=(sort_order == "desc")
            )
            
            return rankings[:limit]
        except Exception as e:
            logger.error(f"Error getting price change rankings: {e}", exc_info=True)
            return []
    
    async def get_open_interest_rankings(
        self,
        sort_order: str = "desc",
        limit: int = 20
    ) -> List[OpenInterestRanking]:
        """Get open interest rankings (Hyperliquid only).

        Prefer snapshot data when available, then fall back to live APIs.
        """
        async with self._snapshot_lock:
            snapshot = self._open_interest_snapshot

        if snapshot is not None:
            rankings = list(snapshot)
            rankings.sort(
                key=lambda x: x.open_interest,
                reverse=(sort_order == "desc"),
            )
            return rankings[:limit]

        rankings: List[OpenInterestRanking] = []
        
        try:
            hl_toolkit = self._get_dex_toolkit("hyperliquid")
            if hl_toolkit and hasattr(hl_toolkit, 'get_meta_and_asset_ctxs'):
                try:
                    result = await hl_toolkit.get_meta_and_asset_ctxs()
                    # meta_and_asset_ctxs returns a list: [meta_dict, ctxs_list]
                    if isinstance(result, list) and len(result) >= 2:
                        meta = result[0]
                        ctxs = result[1]
                    elif isinstance(result, tuple) and len(result) >= 2:
                        meta, ctxs = result
                    else:
                        logger.error(f"Unexpected result format from get_meta_and_asset_ctxs: {type(result)}")
                        raise ValueError(f"Unexpected result format: {type(result)}")
                    
                    if meta and ctxs:
                        universe = meta.get('universe', [])
                        for i, ctx in enumerate(ctxs):
                            if i < len(universe):
                                symbol_name = universe[i].get('name', '')
                                if symbol_name:
                                    symbol = f"{symbol_name}USDT" if symbol_name != "USDT" else symbol_name
                                    oi_str = ctx.get('openInterest', '0')
                                    try:
                                        open_interest = float(oi_str)
                                        rankings.append(OpenInterestRanking(
                                            symbol=symbol,
                                            open_interest=open_interest,
                                            dex="hyperliquid"
                                        ))
                                    except (ValueError, TypeError) as e:
                                        logger.debug(f"Failed to parse open interest for {symbol_name}: {e}, value: {oi_str}")
                    logger.info(f"Successfully fetched {len(rankings)} Hyperliquid open interest rankings")
                except Exception as e:
                    logger.error(f"Failed to get Hyperliquid open interest: {e}", exc_info=True)
            
            # Sort
            rankings.sort(
                key=lambda x: x.open_interest,
                reverse=(sort_order == "desc")
            )
            
            return rankings[:limit]
        except Exception as e:
            logger.error(f"Error getting open interest rankings: {e}", exc_info=True)
            return []

