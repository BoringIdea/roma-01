"""Decision logging and trade history tracking."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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
        
        # In-memory trade tracking
        self.open_positions: Dict[str, Dict] = {}  # key: "symbol_side"
        self.trade_history: List[Dict] = []
        self.equity_history: List[Dict] = []
        
        # Load existing history from files
        self._load_history()
        
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
        self.equity_history.append({
            "timestamp": timestamp.isoformat(),
            "cycle": cycle,
            "equity": account.get("total_wallet_balance", 0.0),
            "pnl": account.get("total_unrealized_profit", 0.0),
        })
        
        # Save equity history to file
        self._save_equity_history()
        
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
        if limit:
            return self.equity_history[-limit:]
        return self.equity_history

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

