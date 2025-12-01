"""
Dashboard API routes for large trades and token rankings.
"""

from typing import Optional, Literal, List, Dict
from fastapi import APIRouter, Query, HTTPException
from loguru import logger

from roma_trading.api.schemas.dashboard import (
    LargeTradeResponse,
    FundingRateRanking,
    VolumeRanking,
    OpenInterestRanking,
    PriceChangeRanking,
    TokenRankingResponse,
    TraderLeaderboardResponse,
)
from roma_trading.services.dashboard_service import DashboardService
from roma_trading.services.hyperliquid_leaderboard_service import HyperliquidLeaderboardService
from roma_trading.services.aster_leaderboard_service import AsterLeaderboardService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Global dashboard service (will be initialized in main.py)
dashboard_service: Optional[DashboardService] = None
hyperliquid_leaderboard_service: Optional[HyperliquidLeaderboardService] = None
aster_leaderboard_service: Optional[AsterLeaderboardService] = None


def set_dashboard_service(service: DashboardService):
    """Set the dashboard service instance."""
    global dashboard_service
    dashboard_service = service


def set_leaderboard_service(
    hyperliquid_service: Optional[HyperliquidLeaderboardService] = None,
    aster_service: Optional[AsterLeaderboardService] = None,
):
    """Set leaderboard services."""
    global hyperliquid_leaderboard_service, aster_leaderboard_service
    hyperliquid_leaderboard_service = hyperliquid_service
    aster_leaderboard_service = aster_service

@router.get("/large-trades", response_model=LargeTradeResponse)
async def get_large_trades(
    dex: Optional[Literal["aster", "hyperliquid"]] = Query(None, description="DEX filter"),
    symbol: Optional[str] = Query(None, description="Symbol filter"),
    side: Optional[Literal["BUY", "SELL"]] = Query(None, description="Trade side filter"),
    min_amount: float = Query(100_000, description="Minimum trade amount in USDT"),
    time_window: str = Query("24h", description="Time window (1h, 6h, 24h)"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of trades"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    sort_by: str = Query("time", description="Sort field (amount, time)"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)")
):
    """
    Get large trades.
    
    Returns list of trades with amount >= min_amount within the specified time window.
    """
    if dashboard_service is None:
        raise HTTPException(status_code=503, detail="Dashboard service not initialized")
    
    try:
        result = await dashboard_service.get_large_trades(
            dex=dex,
            symbol=symbol,
            side=side,
            min_amount=min_amount,
            time_window=time_window,
            limit=limit,
            offset=offset,
        )
        
        # Apply sorting
        if sort_by == "amount":
            result["trades"].sort(
                key=lambda x: x.quote_quantity,
                reverse=(sort_order == "desc")
            )
        # time is already sorted in service
        
        return LargeTradeResponse(**result)
    except Exception as e:
        logger.error(f"Error in get_large_trades: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/funding-rate", response_model=TokenRankingResponse)
async def get_funding_rate_rankings(
    dex: Optional[Literal["aster", "hyperliquid"]] = Query(None, description="DEX filter"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get funding rate rankings."""
    if dashboard_service is None:
        raise HTTPException(status_code=503, detail="Dashboard service not initialized")
    
    try:
        rankings = await dashboard_service.get_funding_rate_rankings(
            dex=dex,
            sort_order=sort_order,
            limit=limit
        )
        return TokenRankingResponse(data=rankings)
    except Exception as e:
        logger.error(f"Error in get_funding_rate_rankings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/volume", response_model=TokenRankingResponse)
async def get_volume_rankings(
    dex: Optional[Literal["aster", "hyperliquid"]] = Query(None, description="DEX filter"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get volume rankings (default sorted by quote_volume_24h)."""
    if dashboard_service is None:
        raise HTTPException(status_code=503, detail="Dashboard service not initialized")
    
    try:
        rankings = await dashboard_service.get_volume_rankings(
            dex=dex,
            sort_order=sort_order,
            limit=limit
        )
        return TokenRankingResponse(data=rankings)
    except Exception as e:
        logger.error(f"Error in get_volume_rankings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/price-change", response_model=TokenRankingResponse)
async def get_price_change_rankings(
    dex: Optional[Literal["aster", "hyperliquid"]] = Query(None, description="DEX filter"),
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get 24h price change rankings."""
    if dashboard_service is None:
        raise HTTPException(status_code=503, detail="Dashboard service not initialized")
    
    try:
        rankings = await dashboard_service.get_price_change_rankings(
            dex=dex,
            sort_order=sort_order,
            limit=limit
        )
        return TokenRankingResponse(data=rankings)
    except Exception as e:
        logger.error(f"Error in get_price_change_rankings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/open-interest", response_model=TokenRankingResponse)
async def get_open_interest_rankings(
    sort_order: str = Query("desc", description="Sort order (asc, desc)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results")
):
    """Get open interest rankings (Hyperliquid only)."""
    if dashboard_service is None:
        raise HTTPException(status_code=503, detail="Dashboard service not initialized")
    
    try:
        rankings = await dashboard_service.get_open_interest_rankings(
            sort_order=sort_order,
            limit=limit
        )
        return TokenRankingResponse(data=rankings)
    except Exception as e:
        logger.error(f"Error in get_open_interest_rankings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=TraderLeaderboardResponse)
async def get_trader_leaderboard(
    dex: Optional[Literal["aster", "hyperliquid"]] = Query(None, description="DEX filter"),
    window: Literal["day", "week", "month", "allTime"] = Query("month", description="Performance window"),
    limit: int = Query(20, ge=1, le=100, description="Rows per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Get trader leaderboard for specified DEX."""
    try:
        results: List[Dict] = []
        total = 0

        # Fetch Hyperliquid data
        if dex is None or dex == "hyperliquid":
            if hyperliquid_leaderboard_service is None:
                logger.warning("Hyperliquid leaderboard service not initialized")
            else:
                try:
                    hl_data, hl_total = await hyperliquid_leaderboard_service.get_leaderboard(
                        window=window, limit=1000, offset=0
                    )
                    # Add dex field to Hyperliquid data
                    for row in hl_data:
                        row["dex"] = "hyperliquid"
                    results.extend(hl_data)
                    total += hl_total
                except Exception as e:
                    logger.error(f"Error fetching Hyperliquid leaderboard: {e}", exc_info=True)

        # Fetch Aster data
        if dex is None or dex == "aster":
            if aster_leaderboard_service is None:
                logger.warning("Aster leaderboard service not initialized")
            else:
                try:
                    aster_data, aster_total = await aster_leaderboard_service.get_leaderboard(
                        window=window, limit=1000, offset=0
                    )
                    results.extend(aster_data)
                    total += aster_total
                except Exception as e:
                    logger.error(f"Error fetching Aster leaderboard: {e}", exc_info=True)

        # Apply pagination
        paginated = results[offset : offset + limit]

        return TraderLeaderboardResponse(data=paginated, total=total, window=window)
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

