"""Utility to orchestrate BaseService instances."""

from __future__ import annotations

import asyncio
from typing import Iterable, List

from loguru import logger

from roma_trading.services.base_service import BaseService


class ServiceManager:
    """Start/stop a collection of services as a group."""

    def __init__(self, services: Iterable[BaseService]) -> None:
        self.services: List[BaseService] = [s for s in services if s]

    async def start_all(self) -> None:
        logger.info("Starting %d managed service(s)", len(self.services))
        for service in self.services:
            try:
                await service.start()
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Failed to start %s: %s", type(service).__name__, exc)

    async def stop_all(self) -> None:
        logger.info("Stopping %d managed service(s)", len(self.services))
        results = await asyncio.gather(
            *[service.stop() for service in self.services],
            return_exceptions=True,
        )
        for service, result in zip(self.services, results):
            if isinstance(result, Exception):
                logger.error("Service %s failed to stop: %s", type(service).__name__, result)
