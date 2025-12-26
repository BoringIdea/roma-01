"""Strategy advisory service for x402-paid requests."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict

import dspy
from loguru import logger

from roma_trading.api.schemas.x402 import StrategyRecommendation, StrategyRequest
from roma_trading.config import get_settings
from roma_trading.core.chat_service import get_chat_service


class StrategyAdvisorSignature(dspy.Signature):
    """DSPy signature for generating strategy recommendations."""

    system_prompt: str = dspy.InputField(desc="Instruction set for the strategy advisor")
    account_context: str = dspy.InputField(desc="Structured snapshot of account, positions, and balances")
    objectives: str = dspy.InputField(desc="Primary objectives and constraints")
    response_json: str = dspy.OutputField(desc="JSON response with summary, steps, risk notes")


class StrategyAdvisor:
    """High-level service for orchestrating LLM-based strategy suggestions."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate(self, payload: StrategyRequest) -> StrategyRecommendation:
        """Generate a trading strategy recommendation from the provided payload."""

        chat_service = get_chat_service()
        lm = chat_service.get_llm()

        system_prompt = self._build_system_prompt()
        account_context = self._build_account_context(payload)
        objectives = payload.objectives or "Generate actionable delta-balanced strategy guidance."

        logger.debug("Generating strategy recommendation via LLM")
        with dspy.context(lm=lm):
            advisor = dspy.ChainOfThought(StrategyAdvisorSignature)
            result = advisor(
                system_prompt=system_prompt,
                account_context=account_context,
                objectives=objectives,
            )

        recommendation_dict = self._parse_response(result.response_json)
        return StrategyRecommendation(**recommendation_dict)

    def _build_system_prompt(self) -> str:
        disclaimer = self.settings.strategy_disclaimer_text or ""
        model_hint = self.settings.strategy_model_id or "model-config"
        return (
            "You are an AI trading strategist for ROMA-01. Produce concise, risk-aware "
            "recommendations for perpetual futures positions. Always return valid JSON with "
            "keys: summary (string), steps (array of strings), risk_notes (array of strings), "
            "confidence (number between 0 and 1), rationale (string). Reference leverage, "
            "position sizing, and hedging ideas. Include hyperliquid/aster nuances where relevant. "
            f"Tag ideas suitable for the configured model '{model_hint}'. "
            "Do not include markdown or additional commentary outside JSON. "
            "If data is insufficient, state limitations in risk_notes. "
            f"Reminder: {disclaimer}"
        )

    def _build_account_context(self, payload: StrategyRequest) -> str:
        account = payload.account
        preferences = payload.preferences

        lines = [f"Platform: {account.platform}"]

        if account.owner:
            lines.append(f"Owner: {account.owner}")

        if account.balance:
            lines.append(
                f"Balance: {account.balance.amount:.4f} {account.balance.asset.upper()}"
            )

        if account.equity is not None:
            lines.append(f"Equity: {account.equity:.4f} {account.balance.asset if account.balance else 'USDC'}")

        if preferences:
            if preferences.leverage is not None:
                lines.append(f"Preferred leverage: {preferences.leverage}x")
            if preferences.risk_tolerance:
                lines.append(f"Risk tolerance: {preferences.risk_tolerance}")
            if preferences.time_horizon:
                lines.append(f"Time horizon: {preferences.time_horizon}")
            if preferences.notes:
                lines.append(f"Preference notes: {preferences.notes}")

        if payload.constraints:
            lines.append("Constraints: " + "; ".join(payload.constraints))

        lines.append("Positions:")
        if account.positions:
            for pos in account.positions:
                side = (pos.side or "flat").upper()
                entry = f"entry {pos.entry_price:.2f}" if pos.entry_price is not None else "entry unknown"
                mark = f"mark {pos.mark_price:.2f}" if pos.mark_price is not None else "mark unknown"
                leverage = f", leverage {pos.leverage}x" if pos.leverage else ""
                lines.append(
                    f"- {pos.symbol}: {side} {pos.size} contracts ({entry}, {mark}{leverage})"
                )
                if pos.unrealized_pnl is not None:
                    lines.append(f"  Unrealized PnL: {pos.unrealized_pnl:+.2f}")
                if pos.metadata:
                    trimmed_meta = {
                        k: v
                        for k, v in pos.metadata.items()
                        if isinstance(v, (int, float, str))
                    }
                    if trimmed_meta:
                        lines.append(f"  Meta: {json.dumps(trimmed_meta, ensure_ascii=False)}")
        else:
            lines.append("- No open positions")

        if payload.telemetry:
            lines.append("Telemetry: " + json.dumps(payload.telemetry, ensure_ascii=False))

        return "\n".join(lines)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start == -1 or json_end <= json_start:
                raise ValueError("No JSON object found in response")
            payload = json.loads(response_text[json_start:json_end])
        except Exception as exc:  # pragma: no cover - fallback for malformed outputs
            logger.warning(f"Failed to parse strategy JSON, using fallback: {exc}")
            payload = {
                "summary": "Unable to parse model output. Provide manual review.",
                "steps": [],
                "risk_notes": ["Model output could not be parsed."],
                "confidence": 0.0,
                "rationale": response_text.strip(),
            }

        payload.setdefault("steps", [])
        payload.setdefault("risk_notes", [])
        payload.setdefault("summary", "No strategy generated.")
        payload.setdefault("confidence", 0.0)
        payload.setdefault("rationale", "")

        # Sanitise types
        try:
            payload["confidence"] = float(payload.get("confidence", 0.0))
        except (TypeError, ValueError):
            payload["confidence"] = 0.0

        payload["steps"] = [str(step) for step in payload.get("steps", [])]
        payload["risk_notes"] = [str(note) for note in payload.get("risk_notes", [])]
        payload["summary"] = str(payload.get("summary", ""))
        payload["rationale"] = str(payload.get("rationale", ""))

        return payload

