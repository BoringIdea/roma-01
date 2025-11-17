"""Decision logging and trade history tracking."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

CASH_FLOW_EPSILON = 1e-6
from loguru import logger


class DecisionLogger:
    """
    Logs trading decisions and tracks trade history for performance analysis.
    
    Stores:
    - Decision logs (JSON files with CoT and decisions)
    - Trade history (open/close pairs for PnL calculation)
    - Equity history (account value over time)
    """

    def __init__(self, agent_id: str, log_dir: str = "logs/decisions"):
        """
        Initialize decision logger.
        
        Args:
            agent_id: Unique agent identifier
            log_dir: Base directory for logs
        """
        self.agent_id = agent_id
        self.log_dir = Path(log_dir) / agent_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths for persistent storage
        self.trades_file = self.log_dir / "trade_history.json"
        self.equity_file = self.log_dir / "equity_history.json"
        self.cash_flow_file = self.log_dir / "cash_flow_state.json"
        
        # In-memory trade tracking
        self.open_positions: Dict[str, Dict] = {}  # key: "symbol_side"
        self.trade_history: List[Dict] = []
        self.equity_history: List[Dict] = []

        # Runtime state for cash flow tracking
        self._net_deposits: float = 0.0
        self._last_equity: Optional[float] = None
        self._last_unrealized: Optional[float] = None
        self._last_logged_trade_index: int = 0
        self._last_external_cash_flow: float = 0.0
        
        # Load existing history from files
        self._load_history()
        self._load_cash_flow_state()
        self._initialize_runtime_state()
        
        logger.info(f"Initialized DecisionLogger for agent={agent_id}, loaded {len(self.trade_history)} trades")

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
        filename = f"decision_{timestamp.strftime('%Y%m%d_%H%M%S')}_cycle{cycle}.json"

        current_equity = float(account.get("total_wallet_balance", 0.0))
        current_unrealized = float(account.get("total_unrealized_profit", 0.0))

        # Calculate realized PnL since last log
        new_trades = []
        if self._last_logged_trade_index < len(self.trade_history):
            new_trades = self.trade_history[self._last_logged_trade_index:]
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
        
        log_data = {
            "timestamp": timestamp.isoformat(),
            "cycle_number": cycle,
            "chain_of_thought": chain_of_thought,
            "decisions": decisions,
            "account_state": account,
            "positions": positions,
        }
        
        # Save to file
        with open(self.log_dir / filename, "w") as f:
            json.dump(log_data, f, indent=2)
        
        # Update equity history
        self._last_equity = current_equity
        self._last_unrealized = current_unrealized
        self._last_logged_trade_index = len(self.trade_history)
        self._last_external_cash_flow = external_cash_flow

        entry = {
            "timestamp": timestamp.isoformat(),
            "cycle": cycle,
            "equity": adjusted_equity,
            "adjusted_equity": adjusted_equity,
            "gross_equity": current_equity,
            "unrealized_pnl": current_unrealized,
            "pnl": current_unrealized,
            "net_deposits": self._net_deposits,
            "external_cash_flow": external_cash_flow,
        }

        self.equity_history.append(entry)
        
        # Save equity history to file
        self._save_equity_history()
        self._save_cash_flow_state()
        
        logger.info(f"Logged decision cycle {cycle} for agent {self.agent_id}")

    def log_remote_strategy(
        self,
        cycle: int,
        account: Dict,
        positions: List[Dict],
        payload: Dict,
    ) -> None:
        """Log remote strategy suggestion response."""

        timestamp = datetime.now()
        filename = f"remote_strategy_{timestamp.strftime('%Y%m%d_%H%M%S')}_cycle{cycle}.json"

        log_data = {
            "timestamp": timestamp.isoformat(),
            "cycle_number": cycle,
            "remote": payload,
            "account_state": account,
            "positions": positions,
        }

        with open(self.log_dir / filename, "w") as f:
            json.dump(log_data, f, indent=2)

        self.equity_history.append({
            "timestamp": timestamp.isoformat(),
            "cycle": cycle,
            "equity": account.get("total_wallet_balance", 0.0),
            "pnl": account.get("total_unrealized_profit", 0.0),
        })

        self._save_equity_history()

        logger.info(f"Logged remote strategy cycle {cycle} for agent {self.agent_id}")

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
        
        self.trade_history.append(trade)
        
        # Save trade history to file
        self._save_trade_history()
        
        logger.info(f"Recorded closed position {key}: quantity={close_quantity:.6f}, PnL={pnl_pct:+.2f}% (${pnl_usdt:+.2f})")

        remaining_quantity = open_quantity - close_quantity
        if remaining_quantity <= 1e-9:
            self.open_positions.pop(key, None)
        else:
            open_pos["quantity"] = remaining_quantity
            self.open_positions[key] = open_pos
        
        return trade

    def get_last_cycle_number(self) -> int:
        """Get the last cycle number from existing logs, return 0 if no logs exist."""
        log_files = list(self.log_dir.glob("decision_*.json"))
        
        if not log_files:
            return 0
        
        def extract_cycle_number(file_path):
            try:
                parts = file_path.stem.split('_')
                for part in parts:
                    if part.startswith('cycle'):
                        return int(part.replace('cycle', ''))
                return 0
            except (IndexError, ValueError):
                return 0
        
        # Find the maximum cycle number
        max_cycle = max((extract_cycle_number(f) for f in log_files), default=0)
        return max_cycle

    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Get recent decision logs, sorted by cycle number (most recent first)."""
        log_files = list(self.log_dir.glob("decision_*.json"))
        
        # Sort by cycle number extracted from filename (e.g., decision_20251101_070311_cycle58.json -> 58)
        def extract_cycle_number(file_path):
            try:
                # Extract number from filename like "decision_20251101_070311_cycle123.json"
                # Split by '_' and get the last part which is "cycle123"
                parts = file_path.stem.split('_')
                for part in parts:
                    if part.startswith('cycle'):
                        return int(part.replace('cycle', ''))
                return 0
            except (IndexError, ValueError):
                return 0
        
        log_files = sorted(log_files, key=extract_cycle_number, reverse=True)[:limit]
        
        decisions = []
        for file in log_files:
            with open(file, "r") as f:
                decisions.append(json.load(f))
        
        return decisions

    def get_equity_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get equity history."""
        history = self.equity_history[-limit:] if limit else self.equity_history
        return [self._ensure_equity_entry_fields(entry) for entry in history]

    def get_trade_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get completed trade history."""
        if limit:
            return self.trade_history[-limit:]
        return self.trade_history
    
    def _load_history(self):
        """Load trade and equity history from files."""
        # Load trade history
        if self.trades_file.exists():
            try:
                with open(self.trades_file, "r") as f:
                    self.trade_history = json.load(f)
                logger.info(f"Loaded {len(self.trade_history)} trades from {self.trades_file}")
            except Exception as e:
                logger.warning(f"Failed to load trade history: {e}")
                self.trade_history = []
        
        # Load equity history
        if self.equity_file.exists():
            try:
                with open(self.equity_file, "r") as f:
                    self.equity_history = json.load(f)
                logger.info(f"Loaded {len(self.equity_history)} equity points from {self.equity_file}")
                self.equity_history = [self._ensure_equity_entry_fields(entry) for entry in self.equity_history]
            except Exception as e:
                logger.warning(f"Failed to load equity history: {e}")
                self.equity_history = []
    
    def _save_trade_history(self):
        """Save trade history to file."""
        try:
            with open(self.trades_file, "w") as f:
                json.dump(self.trade_history, f, indent=2)
            logger.debug(f"Saved {len(self.trade_history)} trades to {self.trades_file}")
        except Exception as e:
            logger.error(f"Failed to save trade history: {e}")
    
    def _save_equity_history(self):
        """Save equity history to file."""
        try:
            with open(self.equity_file, "w") as f:
                json.dump(self.equity_history, f, indent=2)
            logger.debug(f"Saved {len(self.equity_history)} equity points to {self.equity_file}")
        except Exception as e:
            logger.error(f"Failed to save equity history: {e}")

    def _load_cash_flow_state(self) -> None:
        """Load cash flow tracking state from disk."""
        if not self.cash_flow_file.exists():
            return
        try:
            with open(self.cash_flow_file, "r") as f:
                data = json.load(f)
            self._net_deposits = float(data.get("net_deposits", 0.0))
            self._last_equity = data.get("last_equity")
            self._last_unrealized = data.get("last_unrealized")
            self._last_external_cash_flow = data.get("last_external_cash_flow", 0.0)
        except Exception as e:
            logger.warning(f"Failed to load cash flow state: {e}")

    def _initialize_runtime_state(self) -> None:
        """Initialize runtime state from loaded history."""
        self._last_logged_trade_index = len(self.trade_history)

        if self.equity_history:
            last_entry = self.equity_history[-1]
            if self._last_equity is None:
                self._last_equity = last_entry.get("equity")
            if self._last_unrealized is None:
                self._last_unrealized = last_entry.get("unrealized_pnl", last_entry.get("pnl", 0.0))
            # Prefer persisted net deposits if available; otherwise derive from entry
            if "net_deposits" in last_entry:
                self._net_deposits = last_entry.get("net_deposits", self._net_deposits)
            if "external_cash_flow" in last_entry:
                self._last_external_cash_flow = last_entry.get("external_cash_flow", 0.0)

    def _save_cash_flow_state(self) -> None:
        """Persist cash flow tracking state to disk."""
        try:
            data = {
                "net_deposits": self._net_deposits,
                "last_equity": self._last_equity,
                "last_unrealized": self._last_unrealized,
                "last_external_cash_flow": self._last_external_cash_flow,
            }
            with open(self.cash_flow_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cash flow state: {e}")

    def _ensure_equity_entry_fields(self, entry: Dict) -> Dict:
        """Ensure legacy equity entries contain expected fields."""
        normalized = dict(entry)
        if "unrealized_pnl" not in normalized:
            normalized["unrealized_pnl"] = normalized.get("pnl", 0.0)
        if "pnl" not in normalized:
            normalized["pnl"] = normalized.get("unrealized_pnl", 0.0)
        if "net_deposits" not in normalized:
            normalized["net_deposits"] = 0.0
        if "external_cash_flow" not in normalized:
            normalized["external_cash_flow"] = 0.0
        if "gross_equity" not in normalized:
            normalized["gross_equity"] = normalized.get("equity", 0.0)
        if "adjusted_equity" not in normalized:
            normalized["adjusted_equity"] = normalized.get("equity", 0.0) - normalized.get("net_deposits", 0.0)
        normalized["equity"] = normalized.get("adjusted_equity", normalized.get("equity", 0.0))
        return normalized

    def get_net_deposits(self) -> float:
        """Return cumulative net deposits (deposits minus withdrawals)."""
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

