from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Literal, Optional, Tuple

import httpx
from loguru import logger

LeaderboardWindow = Literal["day", "week", "month", "allTime"]


class AsterLeaderboardService:
    """Fetch and cache Aster public leaderboard."""

    LEADERBOARD_URL = "https://www.asterdex.com/bapi/futures/v1/public/campaign/trade/pro/leaderboard"

    # Map our window format to Aster's period format
    PERIOD_MAP = {
        "day": "d1",
        "week": "d7",
        "month": "d30",
        "allTime": "d30",  # Aster doesn't have allTime, use d30 as fallback
    }

    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Tuple[List[Dict], float]] = {}  # key: period, value: (data, timestamp)
        self._lock = asyncio.Lock()

    async def get_leaderboard(
        self,
        window: LeaderboardWindow = "month",
        limit: int = 20,
        offset: int = 0,
        sort: str = "pnl_rank",
        order: str = "asc",
    ) -> Tuple[List[Dict], int]:
        """Get Aster leaderboard data."""
        period = self._normalize_period(window)
        data = await self._ensure_cache(period, sort, order)
        total = len(data)

        # Apply pagination
        paginated = data[offset : offset + limit]

        rows: List[Dict] = []
        for idx, row in enumerate(paginated, start=offset + 1):
            rows.append(
                {
                    "rank": idx,
                    "address": row.get("address", ""),
                    "display_name": row.get("name") or None,
                    "account_value": 0.0,  # Aster doesn't provide account value
                    "pnl": float(row.get("pnl", 0.0)),
                    "roi": 0.0,  # Aster doesn't provide ROI, calculate from PNL if needed
                    "volume": float(row.get("volume", 0.0)),
                    "window": window,
                    "dex": "aster",
                }
            )

        return rows, total

    async def _ensure_cache(
        self, period: str, sort: str = "pnl_rank", order: str = "asc"
    ) -> List[Dict]:
        """Ensure cache is fresh and return data."""
        cache_key = f"{period}_{sort}_{order}"
        async with self._lock:
            now = time.time()
            if cache_key in self._cache:
                data, timestamp = self._cache[cache_key]
                if now - timestamp < self.cache_ttl:
                    return data

            logger.info(f"Fetching Aster leaderboard for period {period}...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch first page to get total count
                payload = {
                    "period": period,
                    "sort": sort,
                    "order": order,
                    "page": 1,
                    "rows": 100,  # Fetch more rows per request
                    "symbol": "",
                    "address": "",
                }
                resp = await client.post(self.LEADERBOARD_URL, json=payload)
                resp.raise_for_status()
                result = resp.json()

                if not result.get("success") or result.get("code") != "000000":
                    logger.error(f"Aster leaderboard API error: {result}")
                    return []

                data = result.get("data", [])
                total = result.get("total", len(data))

                # If total is more than what we fetched, fetch remaining pages
                if total > len(data):
                    remaining_pages = (total + 99) // 100  # Ceiling division
                    for page in range(2, remaining_pages + 1):
                        payload["page"] = page
                        resp = await client.post(self.LEADERBOARD_URL, json=payload)
                        resp.raise_for_status()
                        page_result = resp.json()
                        if page_result.get("success") and page_result.get("code") == "000000":
                            data.extend(page_result.get("data", []))

                self._cache[cache_key] = (data, now)
                logger.info(f"Fetched {len(data)} Aster leaderboard rows for period {period}.")
                return data

    @staticmethod
    def _normalize_period(window: str) -> str:
        """Convert window to Aster period format."""
        return AsterLeaderboardService.PERIOD_MAP.get(window, "d30")

