"""Database base configuration and session management."""

from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from typing import AsyncGenerator
from loguru import logger

from roma_trading.config import get_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# Global engine and session factories
_async_engine = None
_async_session_factory = None
_sync_engine = None
_sync_session_factory = None


def _get_database_url() -> str:
    """Get database URL from settings."""
    settings = get_settings()
    return settings.database_url


def _ensure_db_directory_exists(database_url: str) -> None:
    """Ensure the directory for SQLite database file exists."""
    if "sqlite" not in database_url.lower():
        return
    
    try:
        # Extract file path from SQLite URL
        # Format: sqlite+aiosqlite:///./path/to/db.db or sqlite:///./path/to/db.db
        url_parts = database_url.split("///")
        if len(url_parts) > 1:
            db_path = url_parts[-1]
            
            # Handle relative paths
            if db_path.startswith("./"):
                db_path = db_path[2:]  # Remove ./
            
            # Create Path object (handles both absolute and relative paths)
            db_file = Path(db_path)
            
            # Only create directory if it's a relative path or if parent is not root
            if not db_file.is_absolute() or db_file.parent != Path("/"):
                db_file.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured database directory exists: {db_file.parent.absolute()}")
    except Exception as e:
        logger.warning(f"Failed to ensure database directory exists: {e}")


async def init_db() -> None:
    """Initialize database connection and create tables."""
    global _async_engine, _async_session_factory, _sync_engine, _sync_session_factory
    
    database_url = _get_database_url()
    
    # Ensure data directory exists for SQLite databases
    _ensure_db_directory_exists(database_url)
    
    logger.info(f"Initializing database: {database_url}")
    
    # Create async engine
    _async_engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
    )
    
    _async_session_factory = async_sessionmaker(
        _async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # For sync operations (migrations, etc.)
    # Convert async URL to sync URL
    sync_url = database_url.replace("+aiosqlite", "").replace("sqlite+aiosqlite", "sqlite")
    _sync_engine = create_engine(
        sync_url,
        echo=False,
        future=True,
    )
    
    _sync_session_factory = sessionmaker(
        bind=_sync_engine,
        autocommit=False,
        autoflush=False,
    )
    
    # Create all tables
    async with _async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    if _async_session_factory is None:
        await init_db()
    
    async with _async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_session():
    """Get sync database session (for migrations and sync operations)."""
    global _sync_engine, _sync_session_factory
    
    if _sync_session_factory is None:
        # Initialize sync engine
        database_url = _get_database_url()
        
        # Ensure data directory exists for SQLite databases
        _ensure_db_directory_exists(database_url)
        
        sync_url = database_url.replace("+aiosqlite", "").replace("sqlite+aiosqlite", "sqlite")
        _sync_engine = create_engine(
            sync_url,
            echo=False,
            future=True,
        )
        _sync_session_factory = sessionmaker(
            bind=_sync_engine,
            autocommit=False,
            autoflush=False,
        )
        # Create tables
        Base.metadata.create_all(_sync_engine)
    
    return _sync_session_factory()


async def close_db() -> None:
    """Close database connections."""
    global _async_engine, _sync_engine
    
    if _async_engine:
        await _async_engine.dispose()
        logger.info("Async database engine closed")
    
    if _sync_engine:
        _sync_engine.dispose()
        logger.info("Sync database engine closed")

