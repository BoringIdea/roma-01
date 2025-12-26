"""Agent scheduler + worker helpers."""

import asyncio
from typing import Dict, Optional

from loguru import logger

from roma_trading.agents.trading_agent import TradingAgent


class AgentWorker:
    """Runs trading cycles for a single agent and exposes trigger control."""

    def __init__(self, agent: TradingAgent, interval_seconds: float) -> None:
        self.agent = agent
        self.interval_seconds = interval_seconds
        self._trigger = asyncio.Event()
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the worker loop."""
        self.agent.is_running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the worker loop and wait for completion."""
        self._stop_event.set()
        self.trigger()
        if self._task:
            await self._task
        self.agent.is_running = False

    def trigger(self) -> None:
        """Signal the worker to execute its next cycle."""
        self._trigger.set()

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            await self._trigger.wait()
            self._trigger.clear()

            if self._stop_event.is_set():
                break

            try:
                await self.agent.trading_cycle()
            except Exception as exc:  # pragma: no cover - runtime safety
                logger.error("Agent %s failed a trading cycle: %s", self.agent.agent_id, exc)

            if self._stop_event.is_set():
                break

            await asyncio.sleep(0)


class AgentScheduler:
    """Coordinates AgentWorker instances for all configured agents."""

    def __init__(self) -> None:
        self.workers: Dict[str, AgentWorker] = {}
        self.ticker_tasks: Dict[str, asyncio.Task] = {}

    async def start(self, agents: Dict[str, TradingAgent]) -> None:
        """Create and start workers for every agent."""
        logger.info("Starting agent scheduler for %d agents", len(agents))
        for agent_id, agent in agents.items():
            interval_minutes = agent.config.get("strategy", {}).get("scan_interval_minutes", 3)
            worker = AgentWorker(agent, interval_minutes * 60)
            self.workers[agent_id] = worker
            await worker.start()
            self.ticker_tasks[agent_id] = asyncio.create_task(
                self._run_ticker(worker, interval_minutes * 60)
            )

    async def _run_ticker(self, worker: AgentWorker, interval_seconds: float) -> None:
        """Trigger worker cycles on a fixed interval."""
        while True:
            worker.trigger()
            await asyncio.sleep(interval_seconds)

    async def stop(self) -> None:
        """Stop all workers."""
        logger.info("Stopping agent scheduler")
        for task in self.ticker_tasks.values():
            task.cancel()
        await asyncio.gather(*self.ticker_tasks.values(), return_exceptions=True)
        await asyncio.gather(*(worker.stop() for worker in self.workers.values()), return_exceptions=True)
        self.workers.clear()
        self.ticker_tasks.clear()

    def trigger(self, agent_id: str) -> None:
        """Trigger a specific worker immediately."""
        worker = self.workers.get(agent_id)
        if worker:
            worker.trigger()
