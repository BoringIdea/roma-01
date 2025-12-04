"""Storage factory for creating storage instances based on configuration."""

from typing import Optional
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
from .file_storage import (
    FileTradeStorage,
    FileEquityHistoryStorage,
    FileDecisionLogStorage,
    FileAnalysisInsightStorage,
    FileAnalysisSnapshotStorage,
    FileAnalysisJobStorage,
    FileLargeTradeStorage,
)
from .db_storage import (
    DatabaseTradeStorage,
    DatabaseEquityHistoryStorage,
    DatabaseDecisionLogStorage,
    DatabaseAnalysisInsightStorage,
    DatabaseAnalysisSnapshotStorage,
    DatabaseAnalysisJobStorage,
    DatabaseLargeTradeStorage,
)


class StorageFactory:
    """Factory for creating storage instances."""
    
    def __init__(
        self,
        storage_type: str = "database",  # "database" or "file"
        base_dir: str = "logs",
        large_trades_file: str = "data/large_trades.jsonl",
    ):
        """
        Initialize storage factory.
        
        Args:
            storage_type: "database" or "file"
            base_dir: Base directory for file storage
            large_trades_file: Path to large trades file
        """
        self.storage_type = storage_type
        self.base_dir = base_dir
        self.large_trades_file = large_trades_file
        
        logger.info(f"StorageFactory initialized with type: {storage_type}")
    
    def create_trade_storage(self) -> TradeStorage:
        """Create trade storage instance."""
        if self.storage_type == "database":
            return DatabaseTradeStorage()
        else:
            return FileTradeStorage(base_dir=f"{self.base_dir}/decisions")
    
    def create_equity_history_storage(self) -> EquityHistoryStorage:
        """Create equity history storage instance."""
        if self.storage_type == "database":
            return DatabaseEquityHistoryStorage()
        else:
            return FileEquityHistoryStorage(base_dir=f"{self.base_dir}/decisions")
    
    def create_decision_log_storage(self) -> DecisionLogStorage:
        """Create decision log storage instance."""
        if self.storage_type == "database":
            return DatabaseDecisionLogStorage()
        else:
            return FileDecisionLogStorage(base_dir=f"{self.base_dir}/decisions")
    
    def create_analysis_insight_storage(self) -> AnalysisInsightStorage:
        """Create analysis insight storage instance."""
        if self.storage_type == "database":
            return DatabaseAnalysisInsightStorage()
        else:
            return FileAnalysisInsightStorage(base_dir=f"{self.base_dir}/analysis/insights")
    
    def create_analysis_snapshot_storage(self) -> AnalysisSnapshotStorage:
        """Create analysis snapshot storage instance."""
        if self.storage_type == "database":
            return DatabaseAnalysisSnapshotStorage()
        else:
            return FileAnalysisSnapshotStorage(base_dir=f"{self.base_dir}/analysis/snapshots")
    
    def create_analysis_job_storage(self) -> AnalysisJobStorage:
        """Create analysis job storage instance."""
        if self.storage_type == "database":
            return DatabaseAnalysisJobStorage()
        else:
            return FileAnalysisJobStorage(base_dir=f"{self.base_dir}/analysis")
    
    def create_large_trade_storage(self, max_records: int = 2000) -> LargeTradeStorage:
        """Create large trade storage instance."""
        if self.storage_type == "database":
            return DatabaseLargeTradeStorage(max_records=max_records)
        else:
            return FileLargeTradeStorage(
                file_path=self.large_trades_file,
                max_records=max_records,
            )


# Global storage factory instance
_storage_factory: Optional[StorageFactory] = None


def get_storage_factory() -> StorageFactory:
    """Get global storage factory instance."""
    global _storage_factory
    if _storage_factory is None:
        from roma_trading.config import get_settings
        from pathlib import Path
        import yaml
        
        settings = get_settings()
        
        # Try to load storage config from trading_config.yaml
        storage_type = "database"  # Default to database
        base_dir = "logs"
        large_trades_file = "data/large_trades.jsonl"
        
        config_path = Path(settings.config_file_path)
        if not config_path.exists():
            # Try default path
            config_path = Path("config/trading_config.yaml")
        
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                
                storage_config = config.get("system", {}).get("storage", {})
                if storage_config:
                    storage_type = storage_config.get("type", "database")
                    base_dir = storage_config.get("base_dir", "logs")
                    large_trades_file = storage_config.get("large_trades_file", "data/large_trades.jsonl")
                    logger.info(f"Loaded storage config from {config_path}: type={storage_type}")
            except Exception as e:
                logger.warning(f"Failed to load storage config from {config_path}: {e}, using defaults")
        
        # Fallback: if no config file or config doesn't specify, check database_url
        if storage_type == "database":
            # Verify database is actually configured
            if not settings.database_url or "sqlite" not in settings.database_url.lower():
                logger.warning(
                    "Storage type is 'database' but database_url is not configured. "
                    "Falling back to 'file' storage."
                )
                storage_type = "file"
        
        _storage_factory = StorageFactory(
            storage_type=storage_type,
            base_dir=base_dir,
            large_trades_file=large_trades_file,
        )
    
    return _storage_factory


def set_storage_factory(factory: StorageFactory) -> None:
    """Set global storage factory instance."""
    global _storage_factory
    _storage_factory = factory

