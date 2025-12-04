#!/usr/bin/env python3
"""Migration script to migrate data from files to SQLite database."""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import sys

# Add src directory to path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from roma_trading.database.base import init_db, get_async_session
from roma_trading.database.services import (
    TradeService,
    EquityHistoryService,
    DecisionLogService,
    AnalysisInsightService,
    AnalysisSnapshotService,
    AnalysisJobService,
    LargeTradeService,
)


async def migrate_trades(session, agent_id: str, trades_file: Path) -> int:
    """Migrate trade history from JSON file to database."""
    if not trades_file.exists():
        logger.info(f"No trade history file found for {agent_id}: {trades_file}")
        return 0
    
    try:
        with open(trades_file, "r") as f:
            trades_data = json.load(f)
        
        if not isinstance(trades_data, list):
            logger.warning(f"Invalid trade history format for {agent_id}")
            return 0
        
        migrated = 0
        for trade in trades_data:
            try:
                await TradeService.create_trade(
                    session=session,
                    agent_id=agent_id,
                    symbol=trade["symbol"],
                    side=trade["side"],
                    entry_price=float(trade["entry_price"]),
                    close_price=float(trade["close_price"]),
                    quantity=float(trade["quantity"]),
                    leverage=int(trade["leverage"]),
                    open_time=datetime.fromisoformat(trade["open_time"]),
                    close_time=datetime.fromisoformat(trade["close_time"]),
                    pnl_pct=float(trade["pnl_pct"]),
                    pnl_usdt=float(trade["pnl_usdt"]),
                )
                migrated += 1
            except Exception as e:
                logger.warning(f"Failed to migrate trade {trade.get('symbol')}: {e}")
                continue
        
        logger.info(f"Migrated {migrated} trades for agent {agent_id}")
        return migrated
    except Exception as e:
        logger.error(f"Failed to migrate trades for {agent_id}: {e}")
        return 0


async def migrate_equity_history(session, agent_id: str, equity_file: Path) -> int:
    """Migrate equity history from JSON file to database."""
    if not equity_file.exists():
        logger.info(f"No equity history file found for {agent_id}: {equity_file}")
        return 0
    
    try:
        with open(equity_file, "r") as f:
            equity_data = json.load(f)
        
        if not isinstance(equity_data, list):
            logger.warning(f"Invalid equity history format for {agent_id}")
            return 0
        
        migrated = 0
        for entry in equity_data:
            try:
                timestamp = datetime.fromisoformat(entry["timestamp"])
                await EquityHistoryService.create_equity_entry(
                    session=session,
                    agent_id=agent_id,
                    timestamp=timestamp,
                    cycle=int(entry["cycle"]),
                    equity=float(entry.get("equity", entry.get("adjusted_equity", 0.0))),
                    adjusted_equity=float(entry.get("adjusted_equity", entry.get("equity", 0.0))),
                    gross_equity=float(entry.get("gross_equity", entry.get("equity", 0.0))),
                    unrealized_pnl=float(entry.get("unrealized_pnl", entry.get("pnl", 0.0))),
                    pnl=float(entry.get("pnl", entry.get("unrealized_pnl", 0.0))),
                    net_deposits=float(entry.get("net_deposits", 0.0)),
                    external_cash_flow=float(entry.get("external_cash_flow", 0.0)),
                )
                migrated += 1
            except Exception as e:
                logger.warning(f"Failed to migrate equity entry: {e}")
                continue
        
        logger.info(f"Migrated {migrated} equity entries for agent {agent_id}")
        return migrated
    except Exception as e:
        logger.error(f"Failed to migrate equity history for {agent_id}: {e}")
        return 0


async def migrate_decision_logs(session, agent_id: str, decision_dir: Path) -> int:
    """Migrate decision logs from JSON files to database."""
    if not decision_dir.exists():
        logger.info(f"No decision log directory found for {agent_id}: {decision_dir}")
        return 0
    
    log_files = list(decision_dir.glob("decision_*.json"))
    if not log_files:
        logger.info(f"No decision log files found for {agent_id}")
        return 0
    
    migrated = 0
    for log_file in log_files:
        try:
            with open(log_file, "r") as f:
                log_data = json.load(f)
            
            timestamp = datetime.fromisoformat(log_data["timestamp"])
            await DecisionLogService.create_decision_log(
                session=session,
                agent_id=agent_id,
                cycle_number=int(log_data["cycle_number"]),
                timestamp=timestamp,
                chain_of_thought=log_data.get("chain_of_thought"),
                decisions=log_data.get("decisions"),
                account_state=log_data.get("account_state"),
                positions=log_data.get("positions"),
            )
            migrated += 1
        except Exception as e:
            logger.warning(f"Failed to migrate decision log {log_file.name}: {e}")
            continue
    
    logger.info(f"Migrated {migrated} decision logs for agent {agent_id}")
    return migrated


async def migrate_analysis_insights(session, insights_dir: Path) -> int:
    """Migrate analysis insights from JSON files to database."""
    if not insights_dir.exists():
        logger.info(f"No insights directory found: {insights_dir}")
        return 0
    
    migrated = 0
    for insight_file in insights_dir.rglob("*.json"):
        try:
            with open(insight_file, "r") as f:
                insight_data = json.load(f)
            
            created_at = datetime.fromisoformat(insight_data["created_at"])
            deprecated_at = None
            if insight_data.get("deprecated_at"):
                deprecated_at = datetime.fromisoformat(insight_data["deprecated_at"])
            
            await AnalysisInsightService.create_insight(
                session=session,
                insight_id=insight_data["insight_id"],
                agent_id=insight_data.get("agent_id"),
                category=insight_data["category"],
                title=insight_data["title"],
                summary=insight_data.get("summary"),
                detailed_findings=insight_data.get("detailed_findings"),
                recommendations=insight_data.get("recommendations"),
                confidence_score=float(insight_data["confidence_score"]),
                created_at=created_at,
                deprecated_at=deprecated_at,
                is_active=insight_data.get("is_active", True),
                supporting_trade_ids=insight_data.get("supporting_trade_ids"),
            )
            migrated += 1
        except Exception as e:
            logger.warning(f"Failed to migrate insight {insight_file.name}: {e}")
            continue
    
    logger.info(f"Migrated {migrated} analysis insights")
    return migrated


async def migrate_analysis_snapshots(session, snapshots_dir: Path) -> int:
    """Migrate analysis snapshots from JSON files to database."""
    if not snapshots_dir.exists():
        logger.info(f"No snapshots directory found: {snapshots_dir}")
        return 0
    
    migrated = 0
    for snapshot_file in snapshots_dir.rglob("*.json"):
        try:
            with open(snapshot_file, "r") as f:
                snapshot_data = json.load(f)
            
            # Extract agent_id from directory structure
            # Path format: snapshots/{agent_id}/latest_snapshot.json
            parts = snapshot_file.parts
            agent_id = None
            if len(parts) >= 2:
                agent_dir_name = parts[-2]
                if agent_dir_name not in ["global", "snapshots"]:
                    agent_id = agent_dir_name
            
            period_start = datetime.fromisoformat(snapshot_data.get("period_start", ""))
            period_end = datetime.fromisoformat(snapshot_data.get("period_end", ""))
            
            await AnalysisSnapshotService.create_snapshot(
                session=session,
                agent_id=agent_id or "global",
                snapshot_type="latest",
                period_start=period_start,
                period_end=period_end,
                snapshot_data=snapshot_data,
                is_latest=True,
            )
            migrated += 1
        except Exception as e:
            logger.warning(f"Failed to migrate snapshot {snapshot_file.name}: {e}")
            continue
    
    logger.info(f"Migrated {migrated} analysis snapshots")
    return migrated


async def migrate_analysis_jobs(session, jobs_file: Path) -> int:
    """Migrate analysis jobs from JSON file to database."""
    if not jobs_file.exists():
        logger.info(f"No jobs file found: {jobs_file}")
        return 0
    
    try:
        with open(jobs_file, "r") as f:
            jobs_data = json.load(f)
        
        if not isinstance(jobs_data, list):
            logger.warning(f"Invalid jobs format")
            return 0
        
        migrated = 0
        for job_data in jobs_data:
            try:
                scheduled_at = datetime.fromisoformat(job_data["scheduled_at"])
                started_at = None
                if job_data.get("started_at"):
                    started_at = datetime.fromisoformat(job_data["started_at"])
                completed_at = None
                if job_data.get("completed_at"):
                    completed_at = datetime.fromisoformat(job_data["completed_at"])
                period_start = None
                if job_data.get("analysis_period_start"):
                    period_start = datetime.fromisoformat(job_data["analysis_period_start"])
                period_end = None
                if job_data.get("analysis_period_end"):
                    period_end = datetime.fromisoformat(job_data["analysis_period_end"])
                
                job = await AnalysisJobService.create_job(
                    session=session,
                    job_id=job_data["job_id"],
                    agent_id=job_data.get("agent_id"),
                    status=job_data["status"],
                    scheduled_at=scheduled_at,
                    analysis_period_start=period_start,
                    analysis_period_end=period_end,
                )
                
                # Update job with additional fields
                if started_at or completed_at or job_data.get("error_message"):
                    await AnalysisJobService.update_job(
                        session=session,
                        job_id=job_data["job_id"],
                        started_at=started_at,
                        completed_at=completed_at,
                        error_message=job_data.get("error_message"),
                    )
                
                migrated += 1
            except Exception as e:
                logger.warning(f"Failed to migrate job {job_data.get('job_id')}: {e}")
                continue
        
        logger.info(f"Migrated {migrated} analysis jobs")
        return migrated
    except Exception as e:
        logger.error(f"Failed to migrate analysis jobs: {e}")
        return 0


async def migrate_large_trades(session, large_trades_file: Path) -> int:
    """Migrate large trades from JSONL file to database."""
    if not large_trades_file.exists():
        logger.info(f"No large trades file found: {large_trades_file}")
        return 0
    
    try:
        migrated = 0
        with open(large_trades_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    trade_data = json.loads(line)
                    timestamp = datetime.fromisoformat(trade_data["timestamp"])
                    
                    await LargeTradeService.create_large_trade(
                        session=session,
                        dex=trade_data["dex"],
                        symbol=trade_data["symbol"],
                        price=float(trade_data["price"]),
                        quantity=float(trade_data["quantity"]),
                        quote_quantity=float(trade_data["quote_quantity"]),
                        side=trade_data["side"],
                        timestamp=timestamp,
                        trade_id=trade_data["trade_id"],
                    )
                    migrated += 1
                except Exception as e:
                    logger.warning(f"Failed to migrate large trade: {e}")
                    continue
        
        logger.info(f"Migrated {migrated} large trades")
        return migrated
    except Exception as e:
        logger.error(f"Failed to migrate large trades: {e}")
        return 0


async def main():
    """Main migration function."""
    logger.info("Starting data migration from files to SQLite database...")
    
    # Initialize database
    await init_db()
    
    # Base directories
    base_dir = Path("backend") if Path("backend").exists() else Path(".")
    logs_dir = base_dir / "logs"
    data_dir = base_dir / "data"
    
    total_migrated = 0
    
    async for session in get_async_session():
        try:
            # Migrate decision logs and related data per agent
            decisions_dir = logs_dir / "decisions"
            if decisions_dir.exists():
                for agent_dir in decisions_dir.iterdir():
                    if not agent_dir.is_dir():
                        continue
                    
                    agent_id = agent_dir.name
                    logger.info(f"Migrating data for agent: {agent_id}")
                    
                    # Migrate trades
                    trades_file = agent_dir / "trade_history.json"
                    total_migrated += await migrate_trades(session, agent_id, trades_file)
                    
                    # Migrate equity history
                    equity_file = agent_dir / "equity_history.json"
                    total_migrated += await migrate_equity_history(session, agent_id, equity_file)
                    
                    # Migrate decision logs
                    total_migrated += await migrate_decision_logs(session, agent_id, agent_dir)
            
            # Migrate analysis data
            analysis_dir = logs_dir / "analysis"
            if analysis_dir.exists():
                # Migrate insights
                insights_dir = analysis_dir / "insights"
                total_migrated += await migrate_analysis_insights(session, insights_dir)
                
                # Migrate snapshots
                snapshots_dir = analysis_dir / "snapshots"
                total_migrated += await migrate_analysis_snapshots(session, snapshots_dir)
                
                # Migrate jobs
                jobs_file = analysis_dir / "jobs.json"
                total_migrated += await migrate_analysis_jobs(session, jobs_file)
            
            # Migrate large trades
            large_trades_file = data_dir / "large_trades.jsonl"
            total_migrated += await migrate_large_trades(session, large_trades_file)
            
        finally:
            await session.close()
    
    logger.info(f"Migration completed! Total records migrated: {total_migrated}")


if __name__ == "__main__":
    asyncio.run(main())

