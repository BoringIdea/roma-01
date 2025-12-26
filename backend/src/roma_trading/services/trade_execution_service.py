"""Concurrency limiter for trade execution flows."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from loguru import logger


class TradeExecutionService:
    """Coordinate trade execution across agents to limit concurrent load."""

    def __init__(self, max_concurrent_trades: int = 1, timeout_seconds: float = 300.0) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent_trades)
        self._timeout_seconds = timeout_seconds

    @asynccontextmanager
    async def guard(self, agent_id: str) -> AsyncIterator[None]:
        """Acquire a slot for the next trading cycle."""
        logger.debug("Agent %s waiting for trade slot", agent_id)
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self._timeout_seconds)
        except asyncio.TimeoutError as timeout_exc:
            logger.warning(
                "Agent %s timed out waiting for an execution slot after %.1fs",
                agent_id,
                self._timeout_seconds,
            )
            raise RuntimeError("Timed out waiting for trade execution slot") from timeout_exc

        logger.debug("Agent %s acquired trade execution slot", agent_id)
        try:
            yield
        finally:
            self._semaphore.release()
            logger.debug("Agent %s released trade execution slot", agent_id)
