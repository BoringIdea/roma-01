"""Client utilities for requesting remote strategies over x402."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlsplit, urlunsplit

import httpx
from eth_account import Account
from loguru import logger

from x402.clients.base import PaymentError, PaymentAmountExceededError
from x402.clients.httpx import x402HttpxClient

from roma_trading.api.schemas.x402 import (
    AccountSnapshot,
    BalanceSnapshot,
    PositionSnapshot,
    PreferenceSnapshot,
    StrategyRequest,
    StrategyResponse,
)
from roma_trading.config import get_settings


ASSET_DECIMALS = {
    "USDC": 6,
    "USDT": 6,
    "DAI": 18,
}


class RemoteStrategyError(Exception):
    """Base exception for remote strategy operations."""


class RemoteStrategyConfigError(RemoteStrategyError):
    """Raised when remote strategy configuration is invalid."""


class RemoteStrategyPaymentError(RemoteStrategyError):
    """Raised when payment processing fails."""


@dataclass
class RemoteStrategyResult:
    """Result container for remote strategy responses."""

    request: StrategyRequest
    response: StrategyResponse
    settlement_header: Optional[str] = None

    def to_logging_payload(self) -> Dict:
        return {
            "request": self.request.model_dump(by_alias=True),
            "response": self.response.model_dump(by_alias=True),
            "settlementHeader": self.settlement_header,
        }


class RemoteStrategyClient:
    """Client for interacting with remote /x402 strategy endpoints."""

    def __init__(self):
        settings = get_settings()

        if not settings.remote_x402_endpoint:
            raise RemoteStrategyConfigError("Remote x402 endpoint not configured")
        if not settings.remote_x402_private_key:
            raise RemoteStrategyConfigError("Remote x402 private key not configured")

        self.settings = settings

        parts = urlsplit(settings.remote_x402_endpoint)
        if not parts.scheme or not parts.netloc:
            raise RemoteStrategyConfigError("Invalid remote x402 endpoint URL")

        self._base_url = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
        path = parts.path or "/x402"
        if parts.query:
            path = f"{path}?{parts.query}"
        self._endpoint_path = path

        try:
            self._account = Account.from_key(settings.remote_x402_private_key)
        except Exception as exc:  # pragma: no cover - invalid key runtime
            raise RemoteStrategyConfigError("Failed to load remote buyer private key") from exc

        self._network_filter = settings.remote_x402_network
        max_value = self._compute_max_value(settings.remote_x402_price_cap, settings.remote_x402_payment_asset)
        self._max_value = max_value

        self._client_args = {
            "max_value": max_value,
            "payment_requirements_selector": self._select_payment_requirements,
            "timeout": settings.remote_timeout_seconds,
        }

    @staticmethod
    def _compute_max_value(price_cap: Optional[float], asset: Optional[str]) -> Optional[int]:
        if price_cap is None:
            return None
        asset_key = (asset or "USDC").upper()
        decimals = ASSET_DECIMALS.get(asset_key, 6)
        scaled = Decimal(str(price_cap)) * (Decimal(10) ** decimals)
        return int(scaled)

    def _select_payment_requirements(self, accepts, network_filter, scheme_filter, max_value):
        target_network = self._network_filter or network_filter
        from x402.clients.base import x402Client

        return x402Client.default_payment_requirements_selector(
            accepts,
            network_filter=target_network,
            scheme_filter=scheme_filter,
            max_value=max_value or self._max_value,
        )

    async def request_strategy(self, payload: StrategyRequest) -> RemoteStrategyResult:
        """Send strategy request to remote seller and handle payment."""

        async with x402HttpxClient(
            account=self._account,
            base_url=self._base_url,
            **self._client_args,
        ) as client:
            try:
                response = await client.post(self._endpoint_path, json=payload.model_dump(by_alias=True))
            except PaymentAmountExceededError as exc:
                raise RemoteStrategyPaymentError(str(exc)) from exc
            except PaymentError as exc:
                raise RemoteStrategyPaymentError(str(exc)) from exc
            except httpx.HTTPError as exc:
                raise RemoteStrategyError(f"HTTP error while calling remote strategy: {exc}") from exc

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:  # pragma: no cover - response not JSON
                detail = response.text
            raise RemoteStrategyError(f"Remote strategy request failed ({response.status_code}): {detail}")

        try:
            strategy_response = StrategyResponse.model_validate(response.json())
        except Exception as exc:  # pragma: no cover - validation runtime
            raise RemoteStrategyError(f"Failed to parse remote strategy response: {exc}") from exc

        settlement = response.headers.get("X-PAYMENT-RESPONSE")

        return RemoteStrategyResult(
            request=payload,
            response=strategy_response,
            settlement_header=settlement,
        )


_remote_client_lock = asyncio.Lock()
_remote_client: Optional[RemoteStrategyClient] = None


async def get_remote_strategy_client() -> RemoteStrategyClient:
    global _remote_client

    if _remote_client is not None:
        return _remote_client

    async with _remote_client_lock:
        if _remote_client is None:
            _remote_client = RemoteStrategyClient()
        return _remote_client


def build_strategy_request(
    agent_id: str,
    exchange_cfg: Dict,
    strategy_cfg: Dict,
    account_snapshot: Dict,
    positions: List[Dict],
    cycle: int,
) -> StrategyRequest:
    """Construct a StrategyRequest from local agent context."""

    platform = exchange_cfg.get("type", "aster").lower()
    owner = exchange_cfg.get("account_id") or exchange_cfg.get("user")
    asset_symbol = strategy_cfg.get("quote_asset", "USDC")

    balance = BalanceSnapshot(
        asset=asset_symbol,
        amount=float(account_snapshot.get("available_balance", 0.0)),
    )

    position_snapshots: List[PositionSnapshot] = []
    for pos in positions:
        metadata = {
            k: v
            for k, v in pos.items()
            if k
            not in {
                "symbol",
                "side",
                "position_amt",
                "entry_price",
                "mark_price",
                "leverage",
                "unrealized_profit",
            }
        }
        position_snapshots.append(
            PositionSnapshot(
                symbol=pos.get("symbol", ""),
                size=float(pos.get("position_amt") or pos.get("size") or 0.0),
                side=pos.get("side"),
                entry_price=pos.get("entry_price"),
                mark_price=pos.get("mark_price"),
                leverage=pos.get("leverage"),
                unrealized_pnl=pos.get("unrealized_profit"),
                metadata=metadata,
            )
        )

    account_model = AccountSnapshot(
        platform=platform,
        owner=owner,
        balance=balance,
        equity=float(account_snapshot.get("total_wallet_balance", 0.0)),
        positions=position_snapshots,
        raw={"account": account_snapshot},
    )

    risk_cfg = strategy_cfg.get("risk_management", {})

    preference = PreferenceSnapshot(
        leverage=risk_cfg.get("max_leverage"),
        risk_tolerance=strategy_cfg.get("risk_profile"),
        time_horizon=f"{strategy_cfg.get('scan_interval_minutes', 5)}m",
        notes=strategy_cfg.get("preference_notes"),
    )

    constraints = []
    if risk_cfg:
        constraints.append(
            f"Max positions {risk_cfg.get('max_positions', 'n/a')} / Max leverage {risk_cfg.get('max_leverage', 'n/a')}x"
        )
        constraints.append(
            f"Stop loss {risk_cfg.get('stop_loss_pct', 'n/a')}% / Take profit {risk_cfg.get('take_profit_pct', 'n/a')}%"
        )

    symbols = strategy_cfg.get("default_coins", [])

    telemetry = {
        "agentId": agent_id,
        "cycle": cycle,
        "platform": platform,
        "remoteEndpoint": get_settings().remote_x402_endpoint,
    }

    objectives = strategy_cfg.get(
        "objectives",
        f"Generate actionable strategy guidance for agent {agent_id}",
    )

    return StrategyRequest(
        account=account_model,
        preferences=preference,
        objectives=objectives,
        constraints=[c for c in constraints if c],
        telemetry=telemetry,
        symbols=symbols,
    )


