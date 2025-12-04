"""Database service layer for ROMA Trading Platform."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from loguru import logger
import json

from .models import (
    Trade,
    EquityHistory,
    DecisionLog,
    AnalysisInsight,
    AnalysisSnapshot,
    AnalysisJob,
    LargeTrade,
)


class TradeService:
    """Service for trade operations."""
    
    @staticmethod
    async def create_trade(
        session: AsyncSession,
        agent_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        close_price: float,
        quantity: float,
        leverage: int,
        open_time: datetime,
        close_time: datetime,
        pnl_pct: float,
        pnl_usdt: float,
    ) -> Trade:
        """Create a new trade record."""
        trade = Trade(
            agent_id=agent_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            close_price=close_price,
            quantity=quantity,
            leverage=leverage,
            open_time=open_time,
            close_time=close_time,
            pnl_pct=pnl_pct,
            pnl_usdt=pnl_usdt,
        )
        session.add(trade)
        await session.commit()
        await session.refresh(trade)
        return trade
    
    @staticmethod
    async def get_trades(
        session: AsyncSession,
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Trade]:
        """Get trades with optional filters."""
        query = select(Trade)
        
        conditions = []
        if agent_id:
            conditions.append(Trade.agent_id == agent_id)
        if symbol:
            conditions.append(Trade.symbol == symbol)
        if start_date:
            conditions.append(Trade.close_time >= start_date)
        if end_date:
            conditions.append(Trade.close_time <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(Trade.close_time))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def count_trades(
        session: AsyncSession,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count trades with optional filters."""
        query = select(func.count(Trade.id))
        
        conditions = []
        if agent_id:
            conditions.append(Trade.agent_id == agent_id)
        if start_date:
            conditions.append(Trade.close_time >= start_date)
        if end_date:
            conditions.append(Trade.close_time <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await session.execute(query)
        return result.scalar() or 0


class EquityHistoryService:
    """Service for equity history operations."""
    
    @staticmethod
    async def create_equity_entry(
        session: AsyncSession,
        agent_id: str,
        timestamp: datetime,
        cycle: int,
        equity: float,
        adjusted_equity: float,
        gross_equity: float,
        unrealized_pnl: float,
        pnl: float,
        net_deposits: float,
        external_cash_flow: float,
    ) -> EquityHistory:
        """Create a new equity history entry."""
        entry = EquityHistory(
            agent_id=agent_id,
            timestamp=timestamp,
            cycle=cycle,
            equity=equity,
            adjusted_equity=adjusted_equity,
            gross_equity=gross_equity,
            unrealized_pnl=unrealized_pnl,
            pnl=pnl,
            net_deposits=net_deposits,
            external_cash_flow=external_cash_flow,
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return entry
    
    @staticmethod
    async def get_equity_history(
        session: AsyncSession,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[EquityHistory]:
        """Get equity history for an agent."""
        query = select(EquityHistory).where(EquityHistory.agent_id == agent_id)
        
        if start_date:
            # SQLite stores naive UTC datetimes, so convert aware datetime to naive UTC
            if start_date.tzinfo is not None:
                start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(EquityHistory.timestamp >= start_date)
        if end_date:
            # SQLite stores naive UTC datetimes, so convert aware datetime to naive UTC
            if end_date.tzinfo is not None:
                end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(EquityHistory.timestamp <= end_date)
        
        query = query.order_by(EquityHistory.timestamp)
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())


class DecisionLogService:
    """Service for decision log operations."""
    
    @staticmethod
    async def create_decision_log(
        session: AsyncSession,
        agent_id: str,
        cycle_number: int,
        timestamp: datetime,
        chain_of_thought: Optional[str] = None,
        decisions: Optional[List[Dict]] = None,
        account_state: Optional[Dict] = None,
        positions: Optional[List[Dict]] = None,
    ) -> DecisionLog:
        """Create a new decision log."""
        log = DecisionLog(
            agent_id=agent_id,
            cycle_number=cycle_number,
            timestamp=timestamp,
            chain_of_thought=chain_of_thought,
            decisions=json.dumps(decisions) if decisions else None,
            account_state=json.dumps(account_state) if account_state else None,
            positions=json.dumps(positions) if positions else None,
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log
    
    @staticmethod
    async def get_decision_logs(
        session: AsyncSession,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[DecisionLog]:
        """Get decision logs for an agent."""
        query = select(DecisionLog).where(DecisionLog.agent_id == agent_id)
        
        if start_date:
            # SQLite stores naive UTC datetimes, so convert aware datetime to naive UTC
            if start_date.tzinfo is not None:
                start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(DecisionLog.timestamp >= start_date)
        if end_date:
            # SQLite stores naive UTC datetimes, so convert aware datetime to naive UTC
            if end_date.tzinfo is not None:
                end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)
            query = query.where(DecisionLog.timestamp <= end_date)
        
        query = query.order_by(desc(DecisionLog.cycle_number))
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_last_cycle_number(
        session: AsyncSession,
        agent_id: str,
    ) -> int:
        """Get the last cycle number for an agent."""
        query = select(func.max(DecisionLog.cycle_number)).where(
            DecisionLog.agent_id == agent_id
        )
        result = await session.execute(query)
        max_cycle = result.scalar()
        return max_cycle if max_cycle is not None else 0


class AnalysisInsightService:
    """Service for analysis insight operations."""
    
    @staticmethod
    async def create_insight(
        session: AsyncSession,
        insight_id: str,
        agent_id: Optional[str],
        category: str,
        title: str,
        summary: Optional[str],
        detailed_findings: Optional[str],
        recommendations: Optional[List[str]],
        confidence_score: float,
        created_at: datetime,
        deprecated_at: Optional[datetime] = None,
        is_active: bool = True,
        supporting_trade_ids: Optional[List[str]] = None,
    ) -> AnalysisInsight:
        """Create a new analysis insight."""
        insight = AnalysisInsight(
            insight_id=insight_id,
            agent_id=agent_id,
            category=category,
            title=title,
            summary=summary,
            detailed_findings=detailed_findings,
            recommendations=json.dumps(recommendations) if recommendations else None,
            confidence_score=confidence_score,
            created_at=created_at,
            deprecated_at=deprecated_at,
            is_active=is_active,
            supporting_trade_ids=json.dumps(supporting_trade_ids) if supporting_trade_ids else None,
        )
        session.add(insight)
        await session.commit()
        await session.refresh(insight)
        return insight
    
    @staticmethod
    async def get_latest_insights(
        session: AsyncSession,
        agent_id: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.7,
    ) -> List[AnalysisInsight]:
        """Get latest active insights."""
        query = select(AnalysisInsight).where(
            and_(
                AnalysisInsight.is_active == True,
                AnalysisInsight.confidence_score >= min_confidence,
            )
        )
        
        if agent_id:
            query = query.where(AnalysisInsight.agent_id == agent_id)
        
        query = query.order_by(desc(AnalysisInsight.created_at)).limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())


class AnalysisSnapshotService:
    """Service for analysis snapshot operations."""
    
    @staticmethod
    async def create_snapshot(
        session: AsyncSession,
        agent_id: str,
        snapshot_type: str,
        period_start: datetime,
        period_end: datetime,
        snapshot_data: Optional[Dict],
        is_latest: bool = False,
    ) -> AnalysisSnapshot:
        """Create a new analysis snapshot."""
        # Mark previous snapshots as not latest if this is the latest
        if is_latest:
            await AnalysisSnapshotService._mark_previous_not_latest(
                session, agent_id, snapshot_type
            )
        
        snapshot = AnalysisSnapshot(
            agent_id=agent_id,
            snapshot_type=snapshot_type,
            period_start=period_start,
            period_end=period_end,
            snapshot_data=json.dumps(snapshot_data) if snapshot_data else None,
            is_latest=is_latest,
        )
        session.add(snapshot)
        await session.commit()
        await session.refresh(snapshot)
        return snapshot
    
    @staticmethod
    async def get_latest_snapshot(
        session: AsyncSession,
        agent_id: Optional[str],
        snapshot_type: str = "latest",
    ) -> Optional[AnalysisSnapshot]:
        """Get the latest snapshot."""
        query = select(AnalysisSnapshot).where(
            and_(
                AnalysisSnapshot.is_latest == True,
                AnalysisSnapshot.snapshot_type == snapshot_type,
            )
        )
        
        if agent_id:
            query = query.where(AnalysisSnapshot.agent_id == agent_id)
        else:
            query = query.where(AnalysisSnapshot.agent_id.is_(None))
        
        query = query.order_by(desc(AnalysisSnapshot.created_at)).limit(1)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def _mark_previous_not_latest(
        session: AsyncSession,
        agent_id: Optional[str],
        snapshot_type: str,
    ) -> None:
        """Mark previous snapshots as not latest."""
        query = select(AnalysisSnapshot).where(
            and_(
                AnalysisSnapshot.is_latest == True,
                AnalysisSnapshot.snapshot_type == snapshot_type,
            )
        )
        
        if agent_id:
            query = query.where(AnalysisSnapshot.agent_id == agent_id)
        else:
            query = query.where(AnalysisSnapshot.agent_id.is_(None))
        
        result = await session.execute(query)
        snapshots = result.scalars().all()
        for snapshot in snapshots:
            snapshot.is_latest = False


class AnalysisJobService:
    """Service for analysis job operations."""
    
    @staticmethod
    async def create_job(
        session: AsyncSession,
        job_id: str,
        agent_id: Optional[str],
        status: str,
        scheduled_at: datetime,
        analysis_period_start: Optional[datetime] = None,
        analysis_period_end: Optional[datetime] = None,
    ) -> AnalysisJob:
        """Create a new analysis job."""
        job = AnalysisJob(
            job_id=job_id,
            agent_id=agent_id,
            status=status,
            scheduled_at=scheduled_at,
            analysis_period_start=analysis_period_start,
            analysis_period_end=analysis_period_end,
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job
    
    @staticmethod
    async def update_job(
        session: AsyncSession,
        job_id: str,
        status: Optional[str] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AnalysisJob]:
        """Update an analysis job."""
        query = select(AnalysisJob).where(AnalysisJob.job_id == job_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            return None
        
        if status is not None:
            job.status = status
        if started_at is not None:
            job.started_at = started_at
        if completed_at is not None:
            job.completed_at = completed_at
        if error_message is not None:
            job.error_message = error_message
        
        await session.commit()
        await session.refresh(job)
        return job
    
    @staticmethod
    async def get_jobs(
        session: AsyncSession,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[AnalysisJob]:
        """Get analysis jobs with optional filters."""
        query = select(AnalysisJob)
        
        conditions = []
        if agent_id:
            conditions.append(AnalysisJob.agent_id == agent_id)
        if status:
            conditions.append(AnalysisJob.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(AnalysisJob.scheduled_at))
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())


class LargeTradeService:
    """Service for large trade operations."""
    
    @staticmethod
    async def create_large_trade(
        session: AsyncSession,
        dex: str,
        symbol: str,
        price: float,
        quantity: float,
        quote_quantity: float,
        side: str,
        timestamp: datetime,
        trade_id: str,
    ) -> LargeTrade:
        """Create a new large trade record."""
        trade = LargeTrade(
            dex=dex,
            symbol=symbol,
            price=price,
            quantity=quantity,
            quote_quantity=quote_quantity,
            side=side,
            timestamp=timestamp,
            trade_id=trade_id,
        )
        session.add(trade)
        await session.commit()
        await session.refresh(trade)
        return trade
    
    @staticmethod
    async def query_large_trades(
        session: AsyncSession,
        dex: Optional[str] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        min_amount: float = 100_000,
        start_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[LargeTrade], int]:
        """Query large trades with filters."""
        query = select(LargeTrade)
        
        conditions = []
        if dex:
            conditions.append(LargeTrade.dex == dex)
        if symbol:
            conditions.append(LargeTrade.symbol == symbol)
        if side:
            conditions.append(LargeTrade.side == side)
        if start_time:
            # SQLite stores naive UTC datetimes, so convert aware datetime to naive UTC
            if start_time.tzinfo is not None:
                start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
            conditions.append(LargeTrade.timestamp >= start_time)
        
        conditions.append(LargeTrade.quote_quantity >= min_amount)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = select(func.count(LargeTrade.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await session.execute(count_query)
        total = count_result.scalar() or 0
        
        # Get paginated results
        query = query.order_by(desc(LargeTrade.timestamp)).offset(offset).limit(limit)
        result = await session.execute(query)
        
        return list(result.scalars().all()), total

