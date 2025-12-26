"""Pydantic schemas for the x402 strategy advisory endpoint."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class BalanceSnapshot(BaseModel):
    asset: str
    amount: float

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PositionSnapshot(BaseModel):
    symbol: str
    size: float = Field(validation_alias=AliasChoices("size", "quantity", "positionSize"))
    side: Optional[str] = None
    entry_price: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("entry_price", "entryPx", "entry_price_usd"),
        serialization_alias="entryPrice",
    )
    mark_price: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("mark_price", "markPx", "mark_price_usd"),
        serialization_alias="markPrice",
    )
    leverage: Optional[float] = None
    unrealized_pnl: Optional[float] = Field(default=None, validation_alias=AliasChoices("unrealized_pnl", "unrealizedPnl"))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class AccountSnapshot(BaseModel):
    platform: Literal["hyperliquid", "aster"]
    owner: Optional[str] = None
    balance: Optional[BalanceSnapshot] = None
    equity: Optional[float] = Field(default=None, validation_alias=AliasChoices("equity", "totalEquity"))
    positions: List[PositionSnapshot] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PreferenceSnapshot(BaseModel):
    leverage: Optional[float] = None
    risk_tolerance: Optional[str] = Field(default=None, validation_alias=AliasChoices("riskTolerance", "risk_tolerance"))
    time_horizon: Optional[str] = Field(default=None, validation_alias=AliasChoices("timeHorizon", "time_horizon"))
    notes: Optional[str] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class StrategyRequest(BaseModel):
    account: AccountSnapshot
    preferences: Optional[PreferenceSnapshot] = None
    objectives: Optional[str] = None
    constraints: Optional[List[str]] = None
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    symbols: Optional[List[str]] = None

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class StrategyRecommendation(BaseModel):
    summary: str
    steps: List[str]
    risk_notes: List[str] = Field(default_factory=list)
    confidence: Optional[float] = None
    rationale: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class PaymentReceipt(BaseModel):
    amount: str
    asset: str
    network: str
    pay_to: str
    deadline_seconds: int
    payer: Optional[str] = None
    receipt_header: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class StrategyMetadata(BaseModel):
    request_id: str
    model: Optional[str] = None
    generated_at: datetime
    telemetry: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class StrategyResponse(BaseModel):
    strategy: StrategyRecommendation
    disclaimer: str
    payment: PaymentReceipt
    metadata: StrategyMetadata

    model_config = ConfigDict(populate_by_name=True)


