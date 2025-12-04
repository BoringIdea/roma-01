"""Storage interfaces (abstract base classes) for all storage types."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class TradeStorage(ABC):
    """Interface for trade history storage."""
    
    @abstractmethod
    async def create_trade(
        self,
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
    ) -> Dict[str, Any]:
        """Create a new trade record."""
        pass
    
    @abstractmethod
    async def get_trades(
        self,
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get trades with optional filters."""
        pass
    
    @abstractmethod
    def get_trades_sync(
        self,
        agent_id: Optional[str] = None,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get trades synchronously (for sync contexts)."""
        pass


class EquityHistoryStorage(ABC):
    """Interface for equity history storage."""
    
    @abstractmethod
    async def create_equity_entry(
        self,
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
    ) -> Dict[str, Any]:
        """Create a new equity history entry."""
        pass
    
    @abstractmethod
    async def get_equity_history(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get equity history for an agent."""
        pass
    
    @abstractmethod
    def get_equity_history_sync(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get equity history synchronously."""
        pass


class DecisionLogStorage(ABC):
    """Interface for decision log storage."""
    
    @abstractmethod
    async def create_decision_log(
        self,
        agent_id: str,
        cycle_number: int,
        timestamp: datetime,
        chain_of_thought: Optional[str] = None,
        decisions: Optional[List[Dict]] = None,
        account_state: Optional[Dict] = None,
        positions: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Create a new decision log."""
        pass
    
    @abstractmethod
    async def get_decision_logs(
        self,
        agent_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get decision logs for an agent."""
        pass
    
    @abstractmethod
    def get_last_cycle_number_sync(self, agent_id: str) -> int:
        """Get the last cycle number synchronously."""
        pass
    
    @abstractmethod
    def get_recent_decisions_sync(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent decision logs synchronously."""
        pass


class AnalysisInsightStorage(ABC):
    """Interface for analysis insight storage."""
    
    @abstractmethod
    async def save_insight(self, insight: Any) -> str:
        """Save insight and return insight_id."""
        pass
    
    @abstractmethod
    async def get_latest_insights(
        self,
        agent_id: Optional[str] = None,
        limit: int = 10,
        min_confidence: float = 0.7,
    ) -> List[Any]:
        """Get latest active insights."""
        pass
    
    @abstractmethod
    async def get_insights_by_category(
        self,
        agent_id: Optional[str],
        category: str,
        limit: int = 10,
    ) -> List[Any]:
        """Get insights by category."""
        pass


class AnalysisSnapshotStorage(ABC):
    """Interface for analysis snapshot storage."""
    
    @abstractmethod
    async def create_snapshot(
        self,
        agent_id: Optional[str],
        snapshot_data: Dict[str, Any],
        period_start: datetime,
        period_end: datetime,
        is_latest: bool = True,
    ) -> str:
        """Create and save analysis snapshot."""
        pass
    
    @abstractmethod
    async def get_latest_snapshot(
        self,
        agent_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Get the latest snapshot."""
        pass


class AnalysisJobStorage(ABC):
    """Interface for analysis job storage."""
    
    @abstractmethod
    async def create_job(self, job: Any) -> None:
        """Create a new analysis job."""
        pass
    
    @abstractmethod
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """Update an analysis job."""
        pass
    
    @abstractmethod
    async def get_jobs(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Get analysis jobs with optional filters."""
        pass
    
    @abstractmethod
    def get_jobs_sync(
        self,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Any]:
        """Get jobs synchronously."""
        pass


class LargeTradeStorage(ABC):
    """Interface for large trade storage."""
    
    @abstractmethod
    async def append(self, record: Any) -> None:
        """Append a large trade record."""
        pass
    
    @abstractmethod
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
        """Query large trades with filters."""
        pass

