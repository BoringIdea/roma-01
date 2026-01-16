"""Base service abstraction for lifecycle-managed services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from loguru import logger


class BaseService(ABC):
    """Minimal lifecycle contract for services."""

    name: Optional[str] = None

    def __init__(self) -> None:
        self._running = False

    async def start(self) -> None:
        """Start the service and mark it as running."""
        if self._running:
            logger.debug("%s already running", self.name or self.__class__.__name__)
            return
        self._running = True
        await self._start()

    async def stop(self) -> None:
        """Stop the service and mark it as stopped."""
        if not self._running:
            return
        await self._stop()
        self._running = False

    @abstractmethod
    async def _start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _stop(self) -> None:
        raise NotImplementedError
