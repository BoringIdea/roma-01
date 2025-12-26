"""FastAPI route for x402-protected strategy advisory endpoint."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from roma_trading.api.schemas.x402 import (
    PaymentReceipt,
    StrategyMetadata,
    StrategyRequest,
    StrategyResponse,
)
from roma_trading.config import get_settings
from roma_trading.core import StrategyAdvisor


router = APIRouter(tags=["x402"])

_settings = get_settings()
_advisor = StrategyAdvisor()


def _atomic_amount_to_decimal(value: str, decimals: Optional[int]) -> str:
    try:
        decimals = int(decimals) if decimals is not None else 6
    except (TypeError, ValueError):  # pragma: no cover - invalid config safety
        decimals = 6

    try:
        quantized = Decimal(value) / (Decimal(10) ** Decimal(decimals))
        # Normalise to avoid excessive trailing zeros
        return format(quantized.normalize(), "f")
    except (InvalidOperation, ValueError):  # pragma: no cover
        logger.warning(
            "Failed to convert atomic amount '{}' with decimals {}", value, decimals
        )
        return value


@router.post("/x402", response_model=StrategyResponse)
async def create_strategy(request: Request, payload: StrategyRequest) -> StrategyResponse:
    """Return a strategy recommendation once payment has been verified."""

    payment_requirements = getattr(request.state, "payment_details", None)
    verify_response = getattr(request.state, "verify_response", None)

    if payment_requirements is None or verify_response is None:
        logger.debug("Payment validation did not occur before /x402 handler")
        raise HTTPException(status_code=402, detail="Payment required")

    if not verify_response.is_valid:
        raise HTTPException(status_code=402, detail="Invalid payment")

    recommendation = await _advisor.generate(payload)

    decimals_hint = None
    extra = getattr(payment_requirements, "extra", None) or {}
    if isinstance(extra, dict):
        decimals_hint = extra.get("decimals") or extra.get("DECIMALS")

    amount_decimal = _atomic_amount_to_decimal(payment_requirements.max_amount_required, decimals_hint)

    disclaimer_text = _settings.strategy_disclaimer_text or ""
    request_id = str(uuid4())

    payment_receipt = PaymentReceipt(
        amount=amount_decimal,
        asset=payment_requirements.asset,
        network=payment_requirements.network,
        pay_to=payment_requirements.pay_to,
        deadline_seconds=payment_requirements.max_timeout_seconds,
        payer=verify_response.payer,
        receipt_header=request.headers.get("X-PAYMENT"),
    )

    metadata = StrategyMetadata(
        request_id=request_id,
        model=_settings.strategy_model_id,
        generated_at=datetime.now(tz=timezone.utc),
        telemetry=payload.telemetry,
    )

    return StrategyResponse(
        strategy=recommendation,
        disclaimer=disclaimer_text,
        payment=payment_receipt,
        metadata=metadata,
    )


