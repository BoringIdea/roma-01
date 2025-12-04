"""Database models for ROMA Trading Platform."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
import json

from .base import Base


class Trade(Base):
    """Trade history model."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # "long" or "short"
    entry_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False)
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime, nullable=False, index=True)
    pnl_pct = Column(Float, nullable=False)
    pnl_usdt = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index("idx_trades_agent", "agent_id"),
        Index("idx_trades_symbol", "symbol"),
        Index("idx_trades_time", "open_time", "close_time"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "close_price": self.close_price,
            "quantity": self.quantity,
            "leverage": self.leverage,
            "open_time": self.open_time.isoformat() if self.open_time else None,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "pnl_pct": self.pnl_pct,
            "pnl_usdt": self.pnl_usdt,
        }


class EquityHistory(Base):
    """Equity history model."""
    
    __tablename__ = "equity_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    cycle = Column(Integer, nullable=False)
    equity = Column(Float, nullable=False)
    adjusted_equity = Column(Float, nullable=False)
    gross_equity = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)
    pnl = Column(Float, nullable=False)
    net_deposits = Column(Float, nullable=False)
    external_cash_flow = Column(Float, nullable=False)
    
    __table_args__ = (
        Index("idx_equity_agent", "agent_id"),
        Index("idx_equity_time", "timestamp"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "cycle": self.cycle,
            "equity": self.equity,
            "adjusted_equity": self.adjusted_equity,
            "gross_equity": self.gross_equity,
            "unrealized_pnl": self.unrealized_pnl,
            "pnl": self.pnl,
            "net_deposits": self.net_deposits,
            "external_cash_flow": self.external_cash_flow,
        }


class DecisionLog(Base):
    """Decision log model."""
    
    __tablename__ = "decision_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, index=True)
    cycle_number = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    chain_of_thought = Column(Text, nullable=True)
    decisions = Column(Text, nullable=True)  # JSON string
    account_state = Column(Text, nullable=True)  # JSON string
    positions = Column(Text, nullable=True)  # JSON string
    
    __table_args__ = (
        Index("idx_decision_agent_cycle", "agent_id", "cycle_number"),
        Index("idx_decision_time", "timestamp"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "cycle_number": self.cycle_number,
            "chain_of_thought": self.chain_of_thought,
            "decisions": json.loads(self.decisions) if self.decisions else None,
            "account_state": json.loads(self.account_state) if self.account_state else None,
            "positions": json.loads(self.positions) if self.positions else None,
        }


class AnalysisInsight(Base):
    """Analysis insight model."""
    
    __tablename__ = "analysis_insights"
    
    insight_id = Column(String(100), primary_key=True)
    agent_id = Column(String(100), nullable=True, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    detailed_findings = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)  # JSON array
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    deprecated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    supporting_trade_ids = Column(Text, nullable=True)  # JSON array
    
    __table_args__ = (
        Index("idx_insights_agent", "agent_id"),
        Index("idx_insights_category", "category"),
        Index("idx_insights_active", "is_active", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "insight_id": self.insight_id,
            "agent_id": self.agent_id,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "detailed_findings": self.detailed_findings,
            "recommendations": json.loads(self.recommendations) if self.recommendations else None,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "is_active": self.is_active,
            "supporting_trade_ids": json.loads(self.supporting_trade_ids) if self.supporting_trade_ids else None,
        }


class AnalysisSnapshot(Base):
    """Analysis snapshot model."""
    
    __tablename__ = "analysis_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, index=True)
    snapshot_type = Column(String(50), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    snapshot_data = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=func.now(), index=True)
    is_latest = Column(Boolean, default=False, index=True)
    
    __table_args__ = (
        Index("idx_snapshots_agent", "agent_id"),
        Index("idx_snapshots_latest", "is_latest", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "snapshot_type": self.snapshot_type,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "snapshot_data": json.loads(self.snapshot_data) if self.snapshot_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_latest": self.is_latest,
        }


class AnalysisJob(Base):
    """Analysis job model."""
    
    __tablename__ = "analysis_jobs"
    
    job_id = Column(String(100), primary_key=True)
    agent_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    analysis_period_start = Column(DateTime, nullable=True)
    analysis_period_end = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    __table_args__ = (
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_scheduled", "scheduled_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "analysis_period_start": self.analysis_period_start.isoformat() if self.analysis_period_start else None,
            "analysis_period_end": self.analysis_period_end.isoformat() if self.analysis_period_end else None,
            "error_message": self.error_message,
        }


class LargeTrade(Base):
    """Large trade model."""
    
    __tablename__ = "large_trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dex = Column(String(50), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    quote_quantity = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)  # "BUY" or "SELL"
    timestamp = Column(DateTime, nullable=False, index=True)
    trade_id = Column(String(200), nullable=False)
    
    __table_args__ = (
        Index("idx_large_trades_dex", "dex"),
        Index("idx_large_trades_symbol", "symbol"),
        Index("idx_large_trades_time", "timestamp"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "quantity": self.quantity,
            "quote_quantity": self.quote_quantity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_buyer_maker": self.side == "SELL",
            "dex": self.dex,
            "trade_id": self.trade_id,
            "side": self.side,
        }

