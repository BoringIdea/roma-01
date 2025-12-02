"""
Dashboard API schemas for large trades and token rankings.
"""

from datetime import datetime
from typing import Literal, Optional, Dict, List
from pydantic import BaseModel, Field


class LargeTrade(BaseModel):
    """Large trade data model"""
    symbol: str = Field(..., description="Trading pair symbol")
    side: Literal["BUY", "SELL"] = Field(..., description="Trade direction")
    price: float = Field(..., description="Trade price")
    quantity: float = Field(..., description="Trade quantity")
    quote_quantity: float = Field(..., description="Trade amount in USDT")
    timestamp: datetime = Field(..., description="Trade timestamp")
    is_buyer_maker: bool = Field(..., description="Whether buyer is maker")
    dex: Literal["aster", "hyperliquid"] = Field(..., description="DEX source")
    trade_id: Optional[str] = Field(None, description="Trade ID if available")


class LargeTradeStats(BaseModel):
    """Large trade statistics"""
    total_count: int = Field(..., description="Total number of large trades")
    total_volume: float = Field(..., description="Total trade volume in USDT")
    buy_count: int = Field(..., description="Number of buy trades")
    sell_count: int = Field(..., description="Number of sell trades")
    buy_volume: float = Field(..., description="Total buy volume in USDT")
    sell_volume: float = Field(..., description="Total sell volume in USDT")
    symbol_distribution: Dict[str, int] = Field(
        default_factory=dict, 
        description="Distribution of trades by symbol"
    )


class LargeTradeResponse(BaseModel):
    """Response model for large trades"""
    trades: List[LargeTrade] = Field(..., description="List of large trades")
    stats: LargeTradeStats = Field(..., description="Trade statistics")
    pagination: Optional[Dict] = Field(None, description="Pagination info")


class FundingRateRanking(BaseModel):
    """Funding rate ranking"""
    symbol: str = Field(..., description="Trading pair symbol")
    funding_rate: float = Field(..., description="Funding rate in percentage")
    funding_rate_24h_change: Optional[float] = Field(
        None, description="24h funding rate change"
    )
    next_funding_time: Optional[datetime] = Field(
        None, description="Next funding time"
    )
    dex: Literal["aster", "hyperliquid"] = Field(..., description="DEX source")


class VolumeRanking(BaseModel):
    """Volume ranking"""
    symbol: str = Field(..., description="Trading pair symbol")
    volume_24h: Optional[float] = Field(None, description="24h volume in base asset")
    quote_volume_24h: float = Field(..., description="24h quote volume in USDT")
    volume_change_24h: Optional[float] = Field(
        None, description="24h volume change percentage"
    )
    dex: Literal["aster", "hyperliquid"] = Field(..., description="DEX source")


class OpenInterestRanking(BaseModel):
    """Open interest ranking (Hyperliquid only)"""
    symbol: str = Field(..., description="Trading pair symbol")
    open_interest: float = Field(..., description="Open interest")
    open_interest_24h_change: Optional[float] = Field(
        None, description="24h open interest change percentage"
    )
    dex: Literal["hyperliquid"] = Field(..., description="DEX source (always hyperliquid)")


class PriceChangeRanking(BaseModel):
    """24h price change ranking"""
    symbol: str = Field(..., description="Trading pair symbol")
    current_price: float = Field(..., description="Current price")
    price_change_24h: float = Field(..., description="24h price change")
    price_change_percent_24h: float = Field(..., description="24h price change percentage")
    high_24h: Optional[float] = Field(None, description="24h high price")
    low_24h: Optional[float] = Field(None, description="24h low price")
    open_24h: Optional[float] = Field(None, description="24h open price")
    dex: Literal["aster", "hyperliquid"] = Field(..., description="DEX source")


class OrderBookDepthRanking(BaseModel):
    """Order book depth ranking"""
    symbol: str = Field(..., description="Trading pair symbol")
    bid_ask_ratio: float = Field(..., description="Bid/Ask ratio")
    bid_depth: float = Field(..., description="Bid depth (top 10 levels)")
    ask_depth: float = Field(..., description="Ask depth (top 10 levels)")
    depth_score: Optional[float] = Field(None, description="Market depth score")
    dex: Literal["aster", "hyperliquid"] = Field(..., description="DEX source")


class TokenRankingResponse(BaseModel):
    """Response model for token rankings"""
    data: List = Field(..., description="Ranking data")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class TraderLeaderboardRow(BaseModel):
    """Trader leaderboard entry"""
    rank: int = Field(..., description="Global rank")
    address: str = Field(..., description="Trader wallet address")
    display_name: Optional[str] = Field(None, description="Display name if available")
    account_value: float = Field(..., description="Account value in USD")
    pnl: float = Field(..., description="PNL for selected window")
    roi: float = Field(..., description="ROI for selected window")
    volume: float = Field(..., description="Trading volume for selected window")
    window: Literal["day", "week", "month", "allTime"] = Field(..., description="Performance window")
    dex: Literal["aster", "hyperliquid"] = Field(..., description="DEX source")


class TraderLeaderboardResponse(BaseModel):
    """Response for Hyperliquid leaderboard"""
    data: List[TraderLeaderboardRow]
    total: int
    window: Literal["day", "week", "month", "allTime"]

