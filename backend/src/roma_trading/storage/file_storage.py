"""File-based storage implementations."""

import json
from pathlib import Path
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


class FileTradeStorage(TradeStorage):
    """File-based trade storage."""
    
    def __init__(self, base_dir: str = "logs/decisions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_trades_file(self, agent_id: str) -> Path:
        return self.base_dir / agent_id / "trade_history.json"
    
    async def create_trade(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Create trade (saves to file)."""
        trades_file = self._get_trades_file(agent_id)
        trades_file.parent.mkdir(parents=True, exist_ok=True)
        
        trade = {
            "symbol": kwargs["symbol"],
            "side": kwargs["side"],
            "entry_price": kwargs["entry_price"],
            "close_price": kwargs["close_price"],
            "quantity": kwargs["quantity"],
            "leverage": kwargs["leverage"],
            "open_time": kwargs["open_time"].isoformat(),
            "close_time": kwargs["close_time"].isoformat(),
            "pnl_pct": kwargs["pnl_pct"],
            "pnl_usdt": kwargs["pnl_usdt"],
        }
        
        # Load existing trades
        trades = []
        if trades_file.exists():
            try:
                with open(trades_file, "r") as f:
                    trades = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load trades: {e}")
        
        trades.append(trade)
        
        # Save back
        with open(trades_file, "w") as f:
            json.dump(trades, f, indent=2)
        
        return trade
    
    async def get_trades(
        self,
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get trades from file."""
        if not agent_id:
            return []
        
        trades_file = self._get_trades_file(agent_id)
        if not trades_file.exists():
            return []
        
        try:
            with open(trades_file, "r") as f:
                trades = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load trades: {e}")
            return []
        
        # Filter
        filtered = []
        for trade in trades:
            if symbol and trade.get("symbol") != symbol:
                continue
            if start_date or end_date:
                close_time_str = trade.get("close_time", "")
                if close_time_str:
                    try:
                        close_time = datetime.fromisoformat(close_time_str)
                        if start_date and close_time < start_date:
                            continue
                        if end_date and close_time > end_date:
                            continue
                    except ValueError:
                        continue
            filtered.append(trade)
        
        # Sort by close_time descending
        filtered.sort(key=lambda x: x.get("close_time", ""), reverse=True)
        
        # Paginate
        if offset:
            filtered = filtered[offset:]
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_trades_sync(self, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous version."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we need to handle differently
                # For now, use file directly
                return self._get_trades_sync_direct(**kwargs)
            else:
                return loop.run_until_complete(self.get_trades(**kwargs))
        except RuntimeError:
            return asyncio.run(self.get_trades(**kwargs))
    
    def _get_trades_sync_direct(self, **kwargs) -> List[Dict[str, Any]]:
        """Direct synchronous file read."""
        agent_id = kwargs.get("agent_id")
        if not agent_id:
            return []
        
        trades_file = self._get_trades_file(agent_id)
        if not trades_file.exists():
            return []
        
        try:
            with open(trades_file, "r") as f:
                trades = json.load(f)
        except Exception:
            return []
        
        # Apply filters (simplified)
        symbol = kwargs.get("symbol")
        if symbol:
            trades = [t for t in trades if t.get("symbol") == symbol]
        
        limit = kwargs.get("limit")
        if limit:
            trades = trades[-limit:]
        
        return trades


class FileEquityHistoryStorage(EquityHistoryStorage):
    """File-based equity history storage."""
    
    def __init__(self, base_dir: str = "logs/decisions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_equity_file(self, agent_id: str) -> Path:
        return self.base_dir / agent_id / "equity_history.json"
    
    async def create_equity_entry(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Create equity entry."""
        equity_file = self._get_equity_file(agent_id)
        equity_file.parent.mkdir(parents=True, exist_ok=True)
        
        entry = {
            "timestamp": kwargs["timestamp"].isoformat(),
            "cycle": kwargs["cycle"],
            "equity": kwargs["equity"],
            "adjusted_equity": kwargs["adjusted_equity"],
            "gross_equity": kwargs["gross_equity"],
            "unrealized_pnl": kwargs["unrealized_pnl"],
            "pnl": kwargs["pnl"],
            "net_deposits": kwargs["net_deposits"],
            "external_cash_flow": kwargs["external_cash_flow"],
        }
        
        # Load existing
        history = []
        if equity_file.exists():
            try:
                with open(equity_file, "r") as f:
                    history = json.load(f)
            except Exception:
                pass
        
        history.append(entry)
        
        # Save
        with open(equity_file, "w") as f:
            json.dump(history, f, indent=2)
        
        return entry
    
    async def get_equity_history(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get equity history."""
        equity_file = self._get_equity_file(agent_id)
        if not equity_file.exists():
            return []
        
        try:
            with open(equity_file, "r") as f:
                history = json.load(f)
        except Exception:
            return []
        
        # Filter by date
        if start_date or end_date:
            filtered = []
            for entry in history:
                timestamp_str = entry.get("timestamp", "")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if start_date and timestamp < start_date:
                            continue
                        if end_date and timestamp > end_date:
                            continue
                        filtered.append(entry)
                    except ValueError:
                        continue
            history = filtered
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get("timestamp", ""))
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_equity_history_sync(self, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous version."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self._get_equity_history_sync_direct(**kwargs)
            else:
                return loop.run_until_complete(self.get_equity_history(**kwargs))
        except RuntimeError:
            return asyncio.run(self.get_equity_history(**kwargs))
    
    def _get_equity_history_sync_direct(self, **kwargs) -> List[Dict[str, Any]]:
        """Direct synchronous read."""
        agent_id = kwargs.get("agent_id")
        if not agent_id:
            return []
        
        equity_file = self._get_equity_file(agent_id)
        if not equity_file.exists():
            return []
        
        try:
            with open(equity_file, "r") as f:
                return json.load(f)
        except Exception:
            return []


class FileDecisionLogStorage(DecisionLogStorage):
    """File-based decision log storage."""
    
    def __init__(self, base_dir: str = "logs/decisions"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_dir(self, agent_id: str) -> Path:
        return self.base_dir / agent_id
    
    async def create_decision_log(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """Create decision log."""
        log_dir = self._get_log_dir(agent_id)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = kwargs["timestamp"]
        cycle = kwargs["cycle_number"]
        filename = f"decision_{timestamp.strftime('%Y%m%d_%H%M%S')}_cycle{cycle}.json"
        
        log_data = {
            "timestamp": timestamp.isoformat(),
            "cycle_number": cycle,
            "chain_of_thought": kwargs.get("chain_of_thought"),
            "decisions": kwargs.get("decisions"),
            "account_state": kwargs.get("account_state"),
            "positions": kwargs.get("positions"),
        }
        
        with open(log_dir / filename, "w") as f:
            json.dump(log_data, f, indent=2)
        
        return log_data
    
    async def get_decision_logs(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision logs."""
        log_dir = self._get_log_dir(agent_id)
        if not log_dir.exists():
            return []
        
        logs = []
        for log_file in log_dir.glob("decision_*.json"):
            try:
                with open(log_file, "r") as f:
                    log_data = json.load(f)
                log_time = datetime.fromisoformat(log_data.get("timestamp", ""))
                if start_date and log_time < start_date:
                    continue
                if end_date and log_time > end_date:
                    continue
                logs.append(log_data)
            except Exception:
                continue
        
        # Sort by cycle number
        logs.sort(key=lambda x: x.get("cycle_number", 0), reverse=True)
        
        if limit:
            logs = logs[:limit]
        
        return logs
    
    def get_last_cycle_number_sync(self, agent_id: str) -> int:
        """Get last cycle number."""
        log_dir = self._get_log_dir(agent_id)
        if not log_dir.exists():
            return 0
        
        max_cycle = 0
        for log_file in log_dir.glob("decision_*.json"):
            try:
                parts = log_file.stem.split('_')
                for part in parts:
                    if part.startswith('cycle'):
                        cycle = int(part.replace('cycle', ''))
                        max_cycle = max(max_cycle, cycle)
            except (ValueError, AttributeError):
                continue
        
        return max_cycle
    
    def get_recent_decisions_sync(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decisions."""
        log_dir = self._get_log_dir(agent_id)
        if not log_dir.exists():
            return []
        
        logs = []
        for log_file in log_dir.glob("decision_*.json"):
            try:
                with open(log_file, "r") as f:
                    logs.append(json.load(f))
            except Exception:
                continue
        
        # Sort by cycle
        def extract_cycle(log_data):
            return log_data.get("cycle_number", 0)
        
        logs.sort(key=extract_cycle, reverse=True)
        return logs[:limit]


class FileAnalysisInsightStorage(AnalysisInsightStorage):
    """File-based analysis insight storage."""
    
    def __init__(self, base_dir: str = "logs/analysis/insights"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_insight(self, insight: Any) -> str:
        """Save insight."""
        agent_dir = self.base_dir / (insight.agent_id or "global")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        insight_file = agent_dir / f"{insight.insight_id}.json"
        with open(insight_file, "w") as f:
            json.dump(insight.to_dict(), f, indent=2)
        
        return insight.insight_id
    
    async def get_latest_insights(
        self,
        agent_id: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.7,
    ) -> List[Any]:
        """Get latest insights."""
        from roma_trading.core.trade_history_analyzer import AnalysisInsight, InsightCategory
        
        agent_dir = self.base_dir / (agent_id or "global")
        if not agent_dir.exists():
            return []
        
        insights = []
        for insight_file in agent_dir.glob("*.json"):
            try:
                with open(insight_file, "r") as f:
                    data = json.load(f)
                
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["analysis_period_start"] = datetime.fromisoformat(data["analysis_period_start"])
                data["analysis_period_end"] = datetime.fromisoformat(data["analysis_period_end"])
                if data.get("deprecated_at"):
                    data["deprecated_at"] = datetime.fromisoformat(data["deprecated_at"])
                data["category"] = InsightCategory(data["category"])
                
                insight = AnalysisInsight(**data)
                if insight.is_active and insight.confidence_score >= min_confidence:
                    insights.append(insight)
            except Exception:
                continue
        
        insights.sort(key=lambda x: (x.created_at, x.confidence_score), reverse=True)
        return insights[:limit]
    
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


class FileAnalysisSnapshotStorage(AnalysisSnapshotStorage):
    """File-based analysis snapshot storage."""
    
    def __init__(self, base_dir: str = "logs/analysis/snapshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_snapshot_file(self, agent_id: Optional[str]) -> Path:
        if agent_id:
            agent_dir = self.base_dir / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            return agent_dir / "latest_snapshot.json"
        else:
            global_dir = self.base_dir / "global"
            global_dir.mkdir(parents=True, exist_ok=True)
            return global_dir / "latest_snapshot.json"
    
    async def create_snapshot(
        self,
        agent_id: Optional[str],
        snapshot_data: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
        is_latest: bool = True,
    ) -> str:
        """Create snapshot."""
        snapshot_file = self._get_snapshot_file(agent_id)
        snapshot_data["created_at"] = datetime.now().isoformat()
        snapshot_data["analysis_period_start"] = period_start.isoformat()
        snapshot_data["analysis_period_end"] = period_end.isoformat()
        
        with open(snapshot_file, "w") as f:
            json.dump(snapshot_data, f, indent=2)
        
        return snapshot_data.get("snapshot_id", "unknown")
    
    async def get_latest_snapshot(
        self,
        agent_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Get latest snapshot."""
        snapshot_file = self._get_snapshot_file(agent_id)
        if not snapshot_file.exists():
            return None
        
        try:
            with open(snapshot_file, "r") as f:
                return json.load(f)
        except Exception:
            return None


class FileAnalysisJobStorage(AnalysisJobStorage):
    """File-based analysis job storage."""
    
    def __init__(self, base_dir: str = "logs/analysis"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_file = self.base_dir / "jobs.json"
    
    def _load_jobs(self) -> List[Dict]:
        """Load jobs from file."""
        if not self.jobs_file.exists():
            return []
        try:
            with open(self.jobs_file, "r") as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_jobs(self, jobs: List[Dict]) -> None:
        """Save jobs to file."""
        with open(self.jobs_file, "w") as f:
            json.dump(jobs, f, indent=2)
    
    async def create_job(self, job: Any) -> None:
        """Create job."""
        jobs = self._load_jobs()
        jobs.append(job.to_dict())
        self._save_jobs(jobs)
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update job."""
        jobs = self._load_jobs()
        for i, job in enumerate(jobs):
            if job.get("job_id") == job_id:
                jobs[i].update(updates)
                self._save_jobs(jobs)
                return
    
    async def get_jobs(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Get jobs."""
        from roma_trading.core.trade_history_analyzer import AnalysisJob
        
        jobs_data = self._load_jobs()
        
        # Filter
        filtered = []
        for job_data in jobs_data:
            if agent_id and job_data.get("agent_id") != agent_id:
                continue
            if status and job_data.get("status") != status:
                continue
            
            # Reconstruct datetime fields
            job_data["scheduled_at"] = datetime.fromisoformat(job_data["scheduled_at"])
            if job_data.get("started_at"):
                job_data["started_at"] = datetime.fromisoformat(job_data["started_at"])
            if job_data.get("completed_at"):
                job_data["completed_at"] = datetime.fromisoformat(job_data["completed_at"])
            
            filtered.append(AnalysisJob(**job_data))
        
        # Sort
        filtered.sort(key=lambda x: x.scheduled_at, reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def get_jobs_sync(self, **kwargs) -> List[Any]:
        """Synchronous version."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self._get_jobs_sync_direct(**kwargs)
            else:
                return loop.run_until_complete(self.get_jobs(**kwargs))
        except RuntimeError:
            return asyncio.run(self.get_jobs(**kwargs))
    
    def _get_jobs_sync_direct(self, **kwargs) -> List[Any]:
        """Direct synchronous read."""
        from roma_trading.core.trade_history_analyzer import AnalysisJob
        
        jobs_data = self._load_jobs()
        agent_id = kwargs.get("agent_id")
        status = kwargs.get("status")
        
        filtered = []
        for job_data in jobs_data:
            if agent_id and job_data.get("agent_id") != agent_id:
                continue
            if status and job_data.get("status") != status:
                continue
            
            job_data["scheduled_at"] = datetime.fromisoformat(job_data["scheduled_at"])
            if job_data.get("started_at"):
                job_data["started_at"] = datetime.fromisoformat(job_data["started_at"])
            if job_data.get("completed_at"):
                job_data["completed_at"] = datetime.fromisoformat(job_data["completed_at"])
            
            filtered.append(AnalysisJob(**job_data))
        
        filtered.sort(key=lambda x: x.scheduled_at, reverse=True)
        
        limit = kwargs.get("limit")
        if limit:
            filtered = filtered[:limit]
        
        return filtered


class FileLargeTradeStorage(LargeTradeStorage):
    """File-based large trade storage."""
    
    def __init__(self, file_path: str = "data/large_trades.jsonl", max_records: int = 2000):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_records = max_records
        self._records = []  # In-memory cache
        self._load_existing()
    
    def _load_existing(self) -> None:
        """Load existing records."""
        if not self.file_path.exists():
            return
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            self._records.append(record)
                        except Exception:
                            continue
            # Keep only recent records
            self._records = self._records[-self.max_records:]
        except Exception as e:
            logger.warning(f"Failed to load large trades: {e}")
    
    async def append(self, record: Any) -> None:
        """Append record."""
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
        
        # Append to file
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record_dict) + "\n")
    
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
        """Query large trades."""
        from datetime import timezone
        
        # Parse time window - use UTC for consistency
        now = datetime.now(timezone.utc)
        if time_window == "1h":
            start_time = now - timedelta(hours=1)
        elif time_window == "6h":
            start_time = now - timedelta(hours=6)
        else:
            start_time = now - timedelta(hours=24)
        
        # Filter
        filtered = []
        for record in reversed(self._records):
            timestamp_str = record["timestamp"]
            timestamp = datetime.fromisoformat(timestamp_str)
            # Ensure timestamp is timezone-aware (assume UTC if naive)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
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
        
        # Paginate
        paginated = filtered[offset:offset + limit] if limit else filtered[offset:]
        
        # Calculate stats
        total_volume = sum(r.get("quote_quantity", 0) for r in filtered)
        buy_count = sum(1 for r in filtered if r.get("side") == "BUY")
        sell_count = sum(1 for r in filtered if r.get("side") == "SELL")
        
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
            "stats": {
                "total_count": len(filtered),
                "total_volume": total_volume,
                "buy_count": buy_count,
                "sell_count": sell_count,
                "buy_volume": sum(r.get("quote_quantity", 0) for r in filtered if r.get("side") == "BUY"),
                "sell_volume": sum(r.get("quote_quantity", 0) for r in filtered if r.get("side") == "SELL"),
                "symbol_distribution": {},
            },
            "pagination": {
                "total": len(filtered),
                "limit": limit,
                "offset": offset,
            },
        }

