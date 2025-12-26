from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Literal, Optional, Tuple

import httpx
from loguru import logger

LeaderboardWindow = Literal["day", "week", "month", "allTime"]


class HyperliquidLeaderboardService:
    """Fetch and cache Hyperliquid public leaderboard."""

    LEADERBOARD_URL = "https://stats-data.hyperliquid.xyz/Mainnet/leaderboard"

    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._cache_data: Optional[List[Dict]] = None
        self._cache_timestamp: float = 0.0
        self._lock = asyncio.Lock()

    async def get_leaderboard(
        self,
        window: LeaderboardWindow = "month",
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        data = await self._ensure_cache()
        total = len(data)
        window = self._normalize_window(window)

        rows: List[Dict] = []
        for idx, row in enumerate(data[offset : offset + limit], start=offset + 1):
            performance = self._extract_window_performance(row, window)
            rows.append(
                {
                    "rank": idx,
                    "address": row.get("ethAddress"),
                    "display_name": row.get("displayName"),
                    "account_value": float(row.get("accountValue", 0.0)),
                    "pnl": performance.get("pnl", 0.0),
                    "roi": performance.get("roi", 0.0),
                    "volume": performance.get("vlm", 0.0),
                    "window": window,
                }
            )

        return rows, total

    async def _ensure_cache(self) -> List[Dict]:
        async with self._lock:
            now = time.time()
            if self._cache_data and now - self._cache_timestamp < self.cache_ttl:
                return self._cache_data

            logger.info("Fetching Hyperliquid leaderboard...")
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(self.LEADERBOARD_URL)
                resp.raise_for_status()
                payload = resp.json()
                rows = payload.get("leaderboardRows", [])

                self._cache_data = rows
                self._cache_timestamp = now
                logger.info(f"Fetched {len(rows)} leaderboard rows.")
                return rows

    @staticmethod
    def _normalize_window(window: str) -> LeaderboardWindow:
        if window not in {"day", "week", "month", "allTime"}:
            return "month"
        return window  # type: ignore

    @staticmethod
    def _extract_window_performance(row: Dict, window: LeaderboardWindow) -> Dict[str, float]:
        performances = row.get("windowPerformances", [])
        perf_map = {name: stats for name, stats in performances if isinstance(stats, dict)}
        stats = perf_map.get(window, {})

        def parse_float(value: Optional[str]) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        return {
            "pnl": parse_float(stats.get("pnl")),
            "roi": parse_float(stats.get("roi")),
            "vlm": parse_float(stats.get("vlm")),
        }

