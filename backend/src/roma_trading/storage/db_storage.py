"""Database-based storage implementations."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from .interfaces import (
    TradeStorage,
    EquityHistoryStorage,
    DecisionLogStorage,
    AnalysisInsightStorage,
    AnalysisSnapshotStorage,
    AnalysisJobStorage,
    LargeTradeStorage,
)
from roma_trading.database.base import get_async_session, get_session
from roma_trading.database.services import (
    TradeService,
    EquityHistoryService,
    DecisionLogService,
    AnalysisInsightService,
    AnalysisSnapshotService,
    AnalysisJobService,
    LargeTradeService,
)
from roma_trading.database.services_sync import (
    TradeServiceSync,
    EquityHistoryServiceSync,
    DecisionLogServiceSync,
)


class DatabaseTradeStorage(TradeStorage):
    """Database-based trade storage."""
    
    async def create_trade(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Create trade in database."""
        async for session in get_async_session():
            try:
                trade = await TradeService.create_trade(
                    session=session,
                    agent_id=agent_id,
                    symbol=kwargs["symbol"],
                    side=kwargs["side"],
                    entry_price=kwargs["entry_price"],
                    close_price=kwargs["close_price"],
                    quantity=kwargs["quantity"],
                    leverage=kwargs["leverage"],
                    open_time=kwargs["open_time"],
                    close_time=kwargs["close_time"],
                    pnl_pct=kwargs["pnl_pct"],
                    pnl_usdt=kwargs["pnl_usdt"],
                )
                return trade.to_dict()
            finally:
                await session.close()
    
    async def get_trades(
        self,
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get trades from database."""
        async for session in get_async_session():
            try:
                trades = await TradeService.get_trades(
                    session=session,
                    agent_id=agent_id,
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset,
                )
                return [trade.to_dict() for trade in trades]
            finally:
                await session.close()
    
    def get_trades_sync(self, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous version."""
        session = get_session()
        try:
            trades = TradeServiceSync.get_trades(
                session=session,
                agent_id=kwargs.get("agent_id"),
                limit=kwargs.get("limit"),
            )
            return [trade.to_dict() for trade in trades]
        finally:
            session.close()


class DatabaseEquityHistoryStorage(EquityHistoryStorage):
    """Database-based equity history storage."""
    
    async def create_equity_entry(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Create equity entry in database."""
        async for session in get_async_session():
            try:
                entry = await EquityHistoryService.create_equity_entry(
                    session=session,
                    agent_id=agent_id,
                    timestamp=kwargs["timestamp"],
                    cycle=kwargs["cycle"],
                    equity=kwargs["equity"],
                    adjusted_equity=kwargs["adjusted_equity"],
                    gross_equity=kwargs["gross_equity"],
                    unrealized_pnl=kwargs["unrealized_pnl"],
                    pnl=kwargs["pnl"],
                    net_deposits=kwargs["net_deposits"],
                    external_cash_flow=kwargs["external_cash_flow"],
                )
                return entry.to_dict()
            finally:
                await session.close()
    
    async def get_equity_history(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get equity history from database."""
        async for session in get_async_session():
            try:
                entries = await EquityHistoryService.get_equity_history(
                    session=session,
                    agent_id=agent_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
                return [entry.to_dict() for entry in entries]
            finally:
                await session.close()
    
    def get_equity_history_sync(self, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous version."""
        session = get_session()
        try:
            entries = EquityHistoryServiceSync.get_equity_history(
                session=session,
                agent_id=kwargs["agent_id"],
                limit=kwargs.get("limit"),
            )
            return [entry.to_dict() for entry in entries]
        finally:
            session.close()


class DatabaseDecisionLogStorage(DecisionLogStorage):
    """Database-based decision log storage."""
    
    async def create_decision_log(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Create decision log in database."""
        async for session in get_async_session():
            try:
                log = await DecisionLogService.create_decision_log(
                    session=session,
                    agent_id=agent_id,
                    cycle_number=kwargs["cycle_number"],
                    timestamp=kwargs["timestamp"],
                    chain_of_thought=kwargs.get("chain_of_thought"),
                    decisions=kwargs.get("decisions"),
                    account_state=kwargs.get("account_state"),
                    positions=kwargs.get("positions"),
                )
                return log.to_dict()
            finally:
                await session.close()
    
    async def get_decision_logs(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision logs from database."""
        async for session in get_async_session():
            try:
                logs = await DecisionLogService.get_decision_logs(
                    session=session,
                    agent_id=agent_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
                return [log.to_dict() for log in logs]
            finally:
                await session.close()
    
    def get_last_cycle_number_sync(self, agent_id: str) -> int:
        """Get last cycle number synchronously."""
        session = get_session()
        try:
            return DecisionLogServiceSync.get_last_cycle_number(
                session=session,
                agent_id=agent_id,
            )
        finally:
            session.close()
    
    def get_recent_decisions_sync(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decisions synchronously."""
        session = get_session()
        try:
            logs = DecisionLogServiceSync.get_decision_logs(
                session=session,
                agent_id=agent_id,
                limit=limit,
            )
            return [log.to_dict() for log in logs]
        finally:
            session.close()


class DatabaseAnalysisInsightStorage(AnalysisInsightStorage):
    """Database-based analysis insight storage."""
    
    async def save_insight(self, insight: Any) -> str:
        """Save insight to database."""
        async for session in get_async_session():
            try:
                await AnalysisInsightService.create_insight(
                    session=session,
                    insight_id=insight.insight_id,
                    agent_id=insight.agent_id,
                    category=insight.category.value if hasattr(insight.category, 'value') else str(insight.category),
                    title=insight.title,
                    summary=insight.summary,
                    detailed_findings=insight.detailed_findings,
                    recommendations=insight.recommendations,
                    confidence_score=insight.confidence_score,
                    created_at=insight.created_at,
                    deprecated_at=insight.deprecated_at,
                    is_active=insight.is_active,
                    supporting_trade_ids=insight.supporting_trade_ids,
                )
                return insight.insight_id
            finally:
                await session.close()
    
    async def get_latest_insights(
        self,
        agent_id: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.7,
    ) -> List[Any]:
        """Get latest insights from database."""
        from roma_trading.core.trade_history_analyzer import AnalysisInsight, InsightCategory
        
        async for session in get_async_session():
            try:
                db_insights = await AnalysisInsightService.get_latest_insights(
                    session=session,
                    agent_id=agent_id,
                    limit=limit,
                    min_confidence=min_confidence,
                )
                
                insights = []
                for db_insight in db_insights:
                    try:
                        insight_dict = db_insight.to_dict()
                        category = InsightCategory(insight_dict["category"])
                        
                        # Get supporting trade IDs and calculate trade_count
                        supporting_trade_ids = insight_dict.get("supporting_trade_ids") or []
                        if not isinstance(supporting_trade_ids, list):
                            supporting_trade_ids = []
                        trade_count = len(supporting_trade_ids)
                        
                        # Get analysis period dates (fallback to created_at if not available)
                        created_at = datetime.fromisoformat(insight_dict["created_at"])
                        analysis_period_start_str = insight_dict.get("analysis_period_start")
                        analysis_period_end_str = insight_dict.get("analysis_period_end")
                        
                        if analysis_period_start_str:
                            analysis_period_start = datetime.fromisoformat(analysis_period_start_str)
                        else:
                            # Fallback: use created_at minus 30 days
                            analysis_period_start = created_at - timedelta(days=30)
                        
                        if analysis_period_end_str:
                            analysis_period_end = datetime.fromisoformat(analysis_period_end_str)
                        else:
                            # Fallback: use created_at
                            analysis_period_end = created_at
                        
                        insight = AnalysisInsight(
                            insight_id=insight_dict["insight_id"],
                            agent_id=insight_dict.get("agent_id"),
                            category=category,
                            title=insight_dict["title"],
                            summary=insight_dict.get("summary") or "",
                            detailed_findings=insight_dict.get("detailed_findings") or "",
                            recommendations=insight_dict.get("recommendations") or [],
                            confidence_score=insight_dict.get("confidence_score", 0.7),
                            created_at=created_at,
                            deprecated_at=datetime.fromisoformat(insight_dict["deprecated_at"]) if insight_dict.get("deprecated_at") else None,
                            is_active=insight_dict.get("is_active", True),
                            supporting_trade_ids=supporting_trade_ids,
                            trade_count=trade_count,  # Required field
                            analysis_period_start=analysis_period_start,
                            analysis_period_end=analysis_period_end,
                        )
                        insights.append(insight)
                    except Exception as e:
                        logger.warning(f"Failed to convert insight: {e}", exc_info=True)
                        continue
                
                return insights
            finally:
                await session.close()
    
    async def get_insights_by_category(
        self,
        agent_id: Optional[str],
        category: str,
        limit: int = 10,
    ) -> List[Any]:
        """Get insights by category."""
        from roma_trading.core.trade_history_analyzer import InsightCategory
        
        all_insights = await self.get_latest_insights(agent_id, limit=1000)
        category_enum = InsightCategory(category)
        filtered = [ins for ins in all_insights if ins.category == category_enum]
        return filtered[:limit]


class DatabaseAnalysisSnapshotStorage(AnalysisSnapshotStorage):
    """Database-based analysis snapshot storage."""
    
    async def create_snapshot(
        self,
        agent_id: Optional[str],
        snapshot_data: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
        is_latest: bool = True,
    ) -> str:
        """Create snapshot in database."""
        async for session in get_async_session():
            try:
                await AnalysisSnapshotService.create_snapshot(
                    session=session,
                    agent_id=agent_id or "global",
                    snapshot_type="latest",
                    period_start=period_start,
                    period_end=period_end,
                    snapshot_data=snapshot_data,
                    is_latest=is_latest,
                )
                return snapshot_data.get("snapshot_id", "unknown")
            finally:
                await session.close()
    
    async def get_latest_snapshot(
        self,
        agent_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Get latest snapshot from database."""
        async for session in get_async_session():
            try:
                db_snapshot = await AnalysisSnapshotService.get_latest_snapshot(
                    session=session,
                    agent_id=agent_id,
                    snapshot_type="latest",
                )
                if db_snapshot:
                    return db_snapshot.to_dict()
                return None
            finally:
                await session.close()


class DatabaseAnalysisJobStorage(AnalysisJobStorage):
    """Database-based analysis job storage."""
    
    async def create_job(self, job: Any) -> None:
        """Create job in database."""
        async for session in get_async_session():
            try:
                await AnalysisJobService.create_job(
                    session=session,
                    job_id=job.job_id,
                    agent_id=job.agent_id,
                    status=job.status,
                    scheduled_at=job.scheduled_at,
                    analysis_period_start=None,
                    analysis_period_end=None,
                )
            finally:
                await session.close()
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update job in database."""
        async for session in get_async_session():
            try:
                await AnalysisJobService.update_job(
                    session=session,
                    job_id=job_id,
                    status=updates.get("status"),
                    started_at=updates.get("started_at"),
                    completed_at=updates.get("completed_at"),
                    error_message=updates.get("error_message"),
                )
            finally:
                await session.close()
    
    async def get_jobs(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Get jobs from database."""
        from roma_trading.core.trade_history_analyzer import AnalysisJob
        
        async for session in get_async_session():
            try:
                db_jobs = await AnalysisJobService.get_jobs(
                    session=session,
                    agent_id=agent_id,
                    status=status,
                    limit=limit,
                )
                
                jobs = []
                for db_job in db_jobs:
                    job_dict = db_job.to_dict()
                    job = AnalysisJob(
                        job_id=job_dict["job_id"],
                        agent_id=job_dict.get("agent_id"),
                        status=job_dict["status"],
                        scheduled_at=datetime.fromisoformat(job_dict["scheduled_at"]),
                        started_at=datetime.fromisoformat(job_dict["started_at"]) if job_dict.get("started_at") else None,
                        completed_at=datetime.fromisoformat(job_dict["completed_at"]) if job_dict.get("completed_at") else None,
                        error_message=job_dict.get("error_message"),
                    )
                    jobs.append(job)
                
                return jobs
            finally:
                await session.close()
    
    def get_jobs_sync(self, **kwargs) -> List[Any]:
        """Synchronous version."""
        from roma_trading.core.trade_history_analyzer import AnalysisJob
        
        # For sync, we'll use async with asyncio.run
        import asyncio
        try:
            return asyncio.run(self.get_jobs(**kwargs))
        except RuntimeError:
            # If event loop is running, create a new one
            import nest_asyncio
            try:
                nest_asyncio.apply()
                return asyncio.run(self.get_jobs(**kwargs))
            except ImportError:
                # Fallback: return empty list
                logger.warning("Cannot run async get_jobs in sync context")
                return []


class DatabaseLargeTradeStorage(LargeTradeStorage):
    """Database-based large trade storage."""
    
    def __init__(self, max_records: int = 2000):
        self.max_records = max_records
        self._records = []  # In-memory cache
    
    async def append(self, record: Any) -> None:
        """Append record to database."""
        async for session in get_async_session():
            try:
                await LargeTradeService.create_large_trade(
                    session=session,
                    dex=record.dex,
                    symbol=record.symbol,
                    price=record.price,
                    quantity=record.quantity,
                    quote_quantity=record.quote_quantity,
                    side=record.side,
                    timestamp=record.timestamp,
                    trade_id=record.trade_id,
                )
                
                # Update cache
                record_dict = {
                    "symbol": record.symbol,
                    "price": record.price,
                    "quantity": record.quantity,
                    "quote_quantity": record.quote_quantity,
                    "side": record.side,
                    "timestamp": record.timestamp.isoformat(),
                    "dex": record.dex,
                    "trade_id": record.trade_id,
                }
                self._records.append(record_dict)
                if len(self._records) > self.max_records:
                    self._records = self._records[-self.max_records:]
            finally:
                await session.close()
    
    def query(
        self,
        dex: Optional[str] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        min_amount: float = 100_000,
        time_window: str = "24h",
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Query large trades from database."""
        from datetime import timezone
        
        # Parse time window - use UTC for consistency
        now = datetime.now(timezone.utc)
        if time_window == "1h":
            start_time = now - timedelta(hours=1)
        elif time_window == "6h":
            start_time = now - timedelta(hours=6)
        else:
            start_time = now - timedelta(hours=24)
        
        # Query database
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use cache
                return self._query_from_cache(dex, symbol, side, min_amount, start_time, limit, offset)
            else:
                return loop.run_until_complete(
                    self._query_async(dex, symbol, side, min_amount, start_time, limit, offset)
                )
        except RuntimeError:
            return asyncio.run(
                self._query_async(dex, symbol, side, min_amount, start_time, limit, offset)
            )
    
    async def _query_async(
        self,
        dex: Optional[str],
        symbol: Optional[str],
        side: Optional[str],
        min_amount: float,
        start_time: datetime,
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        """Async query."""
        from datetime import timezone
        
        # Ensure start_time is timezone-aware for database comparison
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        
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
                
                # Get stats
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
                
                stats = self._calculate_stats(all_trades)
                
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
    
    def _query_from_cache(
        self,
        dex: Optional[str],
        symbol: Optional[str],
        side: Optional[str],
        min_amount: float,
        start_time: datetime,
        limit: int,
        offset: int,
    ) -> Dict[str, Any]:
        """Query from cache (fallback)."""
        from datetime import timezone
        
        filtered = []
        for record in reversed(self._records):
            timestamp_str = record["timestamp"]
            timestamp = datetime.fromisoformat(timestamp_str)
            # Ensure timestamp is timezone-aware (assume UTC if naive)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            # Ensure start_time is also timezone-aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if timestamp < start_time:
                break
            if dex and record.get("dex") != dex:
                continue
            if symbol and record.get("symbol") != symbol:
                continue
            if side and record.get("side") != side:
                continue
            if record.get("quote_quantity", 0) < min_amount:
                continue
            filtered.append(record)
        
        paginated = filtered[offset:offset + limit] if limit else filtered[offset:]
        stats = self._calculate_stats_from_list(filtered)
        
        return {
            "trades": [
                {
                    "symbol": r["symbol"],
                    "price": r["price"],
                    "quantity": r["quantity"],
                    "quote_quantity": r["quote_quantity"],
                    "timestamp": r["timestamp"],
                    "is_buyer_maker": r.get("side") == "SELL",
                    "dex": r.get("dex"),
                    "trade_id": r.get("trade_id"),
                    "side": r.get("side"),
                }
                for r in paginated
            ],
            "stats": stats,
            "pagination": {
                "total": len(filtered),
                "limit": limit,
                "offset": offset,
            },
        }
    
    @staticmethod
    def _calculate_stats(trades: List) -> Dict:
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
        symbol_dist = {}
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
    def _calculate_stats_from_list(trades: List[Dict]) -> Dict:
        """Calculate stats from list of dicts."""
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
        total_volume = sum(r.get("quote_quantity", 0) for r in trades)
        buy_trades = [r for r in trades if r.get("side") == "BUY"]
        sell_trades = [r for r in trades if r.get("side") == "SELL"]
        symbol_dist = {}
        for trade in trades:
            symbol = trade.get("symbol", "")
            symbol_dist[symbol] = symbol_dist.get(symbol, 0) + 1
        return {
            "total_count": len(trades),
            "total_volume": total_volume,
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "buy_volume": sum(r.get("quote_quantity", 0) for r in buy_trades),
            "sell_volume": sum(r.get("quote_quantity", 0) for r in sell_trades),
            "symbol_distribution": symbol_dist,
        }

