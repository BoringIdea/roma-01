"""Synchronous database service layer for sync contexts like DecisionLogger."""

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_, func
from typing import List, Optional, Dict
from datetime import datetime
from loguru import logger
import json

from .models import Trade, EquityHistory, DecisionLog


class TradeServiceSync:
    """Synchronous service for trade operations."""
    
    @staticmethod
    def create_trade(
        session: Session,
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
        session.commit()
        session.refresh(trade)
        return trade
    
    @staticmethod
    def get_trades(
        session: Session,
        agent_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Trade]:
        """Get trades with optional filters."""
        query = select(Trade)
        
        if agent_id:
            query = query.where(Trade.agent_id == agent_id)
        
        query = query.order_by(desc(Trade.close_time))
        
        if limit:
            query = query.limit(limit)
        
        result = session.execute(query)
        return list(result.scalars().all())


class EquityHistoryServiceSync:
    """Synchronous service for equity history operations."""
    
    @staticmethod
    def create_equity_entry(
        session: Session,
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
        session.commit()
        session.refresh(entry)
        return entry
    
    @staticmethod
    def get_equity_history(
        session: Session,
        agent_id: str,
        limit: Optional[int] = None,
    ) -> List[EquityHistory]:
        """Get equity history for an agent."""
        query = select(EquityHistory).where(EquityHistory.agent_id == agent_id)
        query = query.order_by(EquityHistory.timestamp)
        
        if limit:
            query = query.limit(limit)
        
        result = session.execute(query)
        return list(result.scalars().all())


class DecisionLogServiceSync:
    """Synchronous service for decision log operations."""
    
    @staticmethod
    def create_decision_log(
        session: Session,
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
        session.commit()
        session.refresh(log)
        return log
    
    @staticmethod
    def get_decision_logs(
        session: Session,
        agent_id: str,
        limit: Optional[int] = None,
    ) -> List[DecisionLog]:
        """Get decision logs for an agent."""
        query = select(DecisionLog).where(DecisionLog.agent_id == agent_id)
        query = query.order_by(desc(DecisionLog.cycle_number))
        
        if limit:
            query = query.limit(limit)
        
        result = session.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    def get_last_cycle_number(
        session: Session,
        agent_id: str,
    ) -> int:
        """Get the last cycle number for an agent."""
        query = select(func.max(DecisionLog.cycle_number)).where(
            DecisionLog.agent_id == agent_id
        )
        result = session.execute(query)
        max_cycle = result.scalar()
        return max_cycle if max_cycle is not None else 0

