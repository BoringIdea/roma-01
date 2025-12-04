"""Decision logging and trade history tracking with storage abstraction."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

CASH_FLOW_EPSILON = 1e-6
from loguru import logger

from roma_trading.storage import (
    TradeStorage,
    EquityHistoryStorage,
    DecisionLogStorage,
    get_storage_factory,
)


class DecisionLogger:
    """
    Logs trading decisions and tracks trade history for performance analysis.
    
    Uses storage abstraction - doesn't care about file vs database.
    """
    
    def __init__(
        self,
        agent_id: str,
        storage_factory=None,
    ):
        """
        Initialize decision logger.
        
        Args:
            agent_id: Unique agent identifier
            storage_factory: Optional storage factory (uses global if not provided)
        """
        self.agent_id = agent_id
        
        # Get storage instances from factory
        if storage_factory is None:
            storage_factory = get_storage_factory()
        
        self.trade_storage: TradeStorage = storage_factory.create_trade_storage()
        self.equity_storage: EquityHistoryStorage = storage_factory.create_equity_history_storage()
        self.decision_log_storage: DecisionLogStorage = storage_factory.create_decision_log_storage()
        
        # In-memory trade tracking
        self.open_positions: Dict[str, Dict] = {}  # key: "symbol_side"
        
        # Runtime state for cash flow tracking
        self._net_deposits: float = 0.0
        self._last_equity: Optional[float] = None
        self._last_unrealized: Optional[float] = None
        self._last_logged_trade_index: int = 0
        self._last_external_cash_flow: float = 0.0
        
        # Load existing state
        self._initialize_runtime_state()
        
        logger.info(f"Initialized DecisionLogger for agent={agent_id} using {storage_factory.storage_type} storage")
    
    def log_decision(
        self,
        cycle: int,
        chain_of_thought: str,
        decisions: List[Dict],
        account: Dict,
        positions: List[Dict],
    ) -> None:
        """
        Log a complete decision cycle.
        
        Args:
            cycle: Cycle number
            chain_of_thought: AI's reasoning
            decisions: List of decisions
            account: Account information
            positions: Current positions
        """
        timestamp = datetime.now()
        
        current_equity = float(account.get("total_wallet_balance", 0.0))
        current_unrealized = float(account.get("total_unrealized_profit", 0.0))
        
        # Get recent trades to calculate realized PnL
        recent_trades = self.get_trade_history(limit=100)
        new_trades = recent_trades[self._last_logged_trade_index:]
        realized_change = sum(t.get("pnl_usdt", 0.0) for t in new_trades)
        
        equity_delta = 0.0
        unrealized_delta = 0.0
        external_cash_flow = 0.0
        if self._last_equity is not None:
            equity_delta = current_equity - self._last_equity
            unrealized_delta = current_unrealized - (self._last_unrealized or 0.0)
            external_cash_flow = equity_delta - realized_change - unrealized_delta
            if abs(external_cash_flow) < CASH_FLOW_EPSILON:
                external_cash_flow = 0.0
            if external_cash_flow != 0.0:
                self._net_deposits += external_cash_flow
                logger.debug(
                    "Detected external cash flow: %+0.2f USDT (cumulative %+0.2f)",
                    external_cash_flow,
                    self._net_deposits,
                )
        
        adjusted_equity = current_equity - self._net_deposits
        account["gross_total_balance"] = current_equity
        account["adjusted_total_balance"] = adjusted_equity
        account["net_deposits"] = self._net_deposits
        account["external_cash_flow"] = external_cash_flow
        
        # Save decision log (async, but we'll handle it)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self.decision_log_storage.create_decision_log(
                        agent_id=self.agent_id,
                        cycle_number=cycle,
                        timestamp=timestamp,
                        chain_of_thought=chain_of_thought,
                        decisions=decisions,
                        account_state=account,
                        positions=positions,
                    )
                )
            else:
                loop.run_until_complete(
                    self.decision_log_storage.create_decision_log(
                        agent_id=self.agent_id,
                        cycle_number=cycle,
                        timestamp=timestamp,
                        chain_of_thought=chain_of_thought,
                        decisions=decisions,
                        account_state=account,
                        positions=positions,
                    )
                )
        except RuntimeError:
            asyncio.run(
                self.decision_log_storage.create_decision_log(
                    agent_id=self.agent_id,
                    cycle_number=cycle,
                    timestamp=timestamp,
                    chain_of_thought=chain_of_thought,
                    decisions=decisions,
                    account_state=account,
                    positions=positions,
                )
            )
        
        # Save equity history entry
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self.equity_storage.create_equity_entry(
                        agent_id=self.agent_id,
                        timestamp=timestamp,
                        cycle=cycle,
                        equity=adjusted_equity,
                        adjusted_equity=adjusted_equity,
                        gross_equity=current_equity,
                        unrealized_pnl=current_unrealized,
                        pnl=current_unrealized,
                        net_deposits=self._net_deposits,
                        external_cash_flow=external_cash_flow,
                    )
                )
            else:
                loop.run_until_complete(
                    self.equity_storage.create_equity_entry(
                        agent_id=self.agent_id,
                        timestamp=timestamp,
                        cycle=cycle,
                        equity=adjusted_equity,
                        adjusted_equity=adjusted_equity,
                        gross_equity=current_equity,
                        unrealized_pnl=current_unrealized,
                        pnl=current_unrealized,
                        net_deposits=self._net_deposits,
                        external_cash_flow=external_cash_flow,
                    )
                )
        except RuntimeError:
            asyncio.run(
                self.equity_storage.create_equity_entry(
                    agent_id=self.agent_id,
                    timestamp=timestamp,
                    cycle=cycle,
                    equity=adjusted_equity,
                    adjusted_equity=adjusted_equity,
                    gross_equity=current_equity,
                    unrealized_pnl=current_unrealized,
                    pnl=current_unrealized,
                    net_deposits=self._net_deposits,
                    external_cash_flow=external_cash_flow,
                )
            )
        
        # Update state
        self._last_equity = current_equity
        self._last_unrealized = current_unrealized
        self._last_logged_trade_index = len(recent_trades)
        self._last_external_cash_flow = external_cash_flow
        
        logger.info(f"Logged decision cycle {cycle} for agent {self.agent_id}")
    
    def record_open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        leverage: int,
    ) -> None:
        """Record a position opening."""
        key = f"{symbol}_{side}"
        self.open_positions[key] = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "leverage": leverage,
            "open_time": datetime.now().isoformat(),
        }
        logger.debug(f"Recorded open position: {key}")
    
    def record_close_position(
        self,
        symbol: str,
        side: str,
        close_price: float,
        quantity: Optional[float] = None,
    ) -> Optional[Dict]:
        """
        Record a position closing and calculate PnL.
        
        Returns:
            Trade record with PnL information
        """
        key = f"{symbol}_{side}"
        
        if key not in self.open_positions:
            logger.warning(f"No open position found for {key}")
            return None
        
        open_pos = self.open_positions[key]
        
        # Calculate PnL
        entry_price = open_pos["entry_price"]
        open_quantity = open_pos["quantity"]
        leverage = open_pos["leverage"]
        
        close_quantity = open_quantity if quantity is None else min(open_quantity, max(0.0, quantity))
        if close_quantity <= 0:
            logger.warning("Close quantity must be positive to record trade")
            return None
        
        if side == "long":
            pnl_pct = (close_price - entry_price) / entry_price * 100
            pnl_usdt = (close_price - entry_price) * close_quantity * leverage
        else:  # short
            pnl_pct = (entry_price - close_price) / entry_price * 100
            pnl_usdt = (entry_price - close_price) * close_quantity * leverage
        
        # Create trade record
        trade = {
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "close_price": close_price,
            "quantity": close_quantity,
            "leverage": leverage,
            "open_time": open_pos["open_time"],
            "close_time": datetime.now().isoformat(),
            "pnl_pct": pnl_pct,
            "pnl_usdt": pnl_usdt,
        }
        
        # Save to storage
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    self.trade_storage.create_trade(
                        agent_id=self.agent_id,
                        symbol=symbol,
                        side=side,
                        entry_price=entry_price,
                        close_price=close_price,
                        quantity=close_quantity,
                        leverage=leverage,
                        open_time=datetime.fromisoformat(open_pos["open_time"]),
                        close_time=datetime.now(),
                        pnl_pct=pnl_pct,
                        pnl_usdt=pnl_usdt,
                    )
                )
            else:
                loop.run_until_complete(
                    self.trade_storage.create_trade(
                        agent_id=self.agent_id,
                        symbol=symbol,
                        side=side,
                        entry_price=entry_price,
                        close_price=close_price,
                        quantity=close_quantity,
                        leverage=leverage,
                        open_time=datetime.fromisoformat(open_pos["open_time"]),
                        close_time=datetime.now(),
                        pnl_pct=pnl_pct,
                        pnl_usdt=pnl_usdt,
                    )
                )
        except RuntimeError:
            asyncio.run(
                self.trade_storage.create_trade(
                    agent_id=self.agent_id,
                    symbol=symbol,
                    side=side,
                    entry_price=entry_price,
                    close_price=close_price,
                    quantity=close_quantity,
                    leverage=leverage,
                    open_time=datetime.fromisoformat(open_pos["open_time"]),
                    close_time=datetime.now(),
                    pnl_pct=pnl_pct,
                    pnl_usdt=pnl_usdt,
                )
            )
        
        logger.info(f"Recorded closed position {key}: quantity={close_quantity:.6f}, PnL={pnl_pct:+.2f}% (${pnl_usdt:+.2f})")
        
        remaining_quantity = open_quantity - close_quantity
        if remaining_quantity <= 1e-9:
            self.open_positions.pop(key, None)
        else:
            open_pos["quantity"] = remaining_quantity
            self.open_positions[key] = open_pos
        
        return trade
    
    def get_last_cycle_number(self) -> int:
        """Get the last cycle number."""
        return self.decision_log_storage.get_last_cycle_number_sync(self.agent_id)
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Get recent decision logs."""
        return self.decision_log_storage.get_recent_decisions_sync(self.agent_id, limit=limit)
    
    def get_equity_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get equity history."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use sync version
                return self.equity_storage.get_equity_history_sync(
                    agent_id=self.agent_id,
                    limit=limit,
                )
            else:
                return loop.run_until_complete(
                    self.equity_storage.get_equity_history(
                        agent_id=self.agent_id,
                        limit=limit,
                    )
                )
        except RuntimeError:
            return asyncio.run(
                self.equity_storage.get_equity_history(
                    agent_id=self.agent_id,
                    limit=limit,
                )
            )
    
    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get completed trade history."""
        return self.trade_storage.get_trades_sync(
            agent_id=self.agent_id,
            limit=limit,
        )
    
    def _initialize_runtime_state(self) -> None:
        """Initialize runtime state from loaded history."""
        # Load recent equity history to get last state
        equity_history = self.get_equity_history(limit=1)
        if equity_history:
            last_entry = equity_history[-1]
            self._net_deposits = last_entry.get("net_deposits", 0.0)
            self._last_equity = last_entry.get("gross_equity", last_entry.get("equity", 0.0))
            self._last_unrealized = last_entry.get("unrealized_pnl", 0.0)
        
        # Load trade history to get index
        trades = self.get_trade_history(limit=None)
        self._last_logged_trade_index = len(trades)
    
    def get_net_deposits(self) -> float:
        """Return cumulative net deposits."""
        return self._net_deposits
    
    def get_last_external_cash_flow(self) -> float:
        """Return the most recent cycle's detected external cash flow."""
        return self._last_external_cash_flow
    
    def augment_account_balance(self, account: Dict, initial_balance: float = None) -> Dict:
        """Augment raw account balance with deposit-adjusted metrics."""
        enriched = dict(account)
        current_equity = float(enriched.get("total_wallet_balance", 0.0))
        adjusted_equity = current_equity - self._net_deposits
        enriched.setdefault("total_unrealized_profit", float(enriched.get("total_unrealized_profit", 0.0)))
        enriched["adjusted_total_balance"] = adjusted_equity
        enriched["gross_total_balance"] = current_equity
        enriched["net_deposits"] = self._net_deposits
        enriched.setdefault("external_cash_flow", 0.0)
        if initial_balance is not None:
            enriched["initial_balance"] = float(initial_balance)
        return enriched
