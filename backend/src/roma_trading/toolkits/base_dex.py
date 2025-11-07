"""Base DEX toolkit interface for extensibility."""

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseDEXToolkit(ABC):
    """
    Abstract base class for DEX trading toolkits.
    
    This interface ensures all DEX implementations have consistent methods,
    making it easy to add support for new exchanges (Hyperliquid, dYdX, etc.).
    """

    @abstractmethod
    async def get_account_balance(self) -> Dict:
        """
        Get account balance information.
        
        Returns:
            Dict with keys:
                - total_wallet_balance: float
                - available_balance: float
                - total_unrealized_profit: float
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict]:
        """
        Get current open positions.
        
        Returns:
            List of position dicts with keys:
                - symbol: str
                - side: str ("long" or "short")
                - position_amt: float
                - entry_price: float
                - mark_price: float
                - unrealized_profit: float
                - leverage: int
                - liquidation_price: float
        """
        pass

    @abstractmethod
    async def open_long(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """
        Open a long position.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            quantity: Position size
            leverage: Leverage multiplier
            
        Returns:
            Dict with order information
        """
        pass

    @abstractmethod
    async def open_short(self, symbol: str, quantity: float, leverage: int) -> Dict:
        """
        Open a short position.
        
        Args:
            symbol: Trading pair
            quantity: Position size
            leverage: Leverage multiplier
            
        Returns:
            Dict with order information
        """
        pass

    @abstractmethod
    async def close_position(self, symbol: str, side: str, quantity: float | None = None) -> Dict:
        """
        Close an existing position.
        
        Args:
            symbol: Trading pair
            side: "long" or "short"
            quantity: Optional partial quantity to close. If None, close full position.
            
        Returns:
            Dict with close order information
        """
        pass

    @abstractmethod
    async def get_market_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Current price as float
        """
        pass

    @abstractmethod
    async def get_klines(
        self, symbol: str, interval: str = "3m", limit: int = 100
    ) -> List[Dict]:
        """
        Get historical kline/candlestick data.
        
        Args:
            symbol: Trading pair
            interval: Timeframe ("1m", "3m", "1h", "4h", etc.)
            limit: Number of candles to fetch
            
        Returns:
            List of kline dicts with OHLCV data
        """
        pass

    @abstractmethod
    async def place_take_profit_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        take_profit_pct: float | None,
        stop_loss_pct: float | None,
    ) -> Dict:
        """Place take-profit and/or stop-loss orders for an open position.

        Args:
            symbol: Trading pair
            side: "long" or "short" for the existing position
            quantity: Position size to protect
            entry_price: Entry price used to compute brackets
            take_profit_pct: Target profit percentage (None to skip)
            stop_loss_pct: Stop loss percentage (None to skip)

        Returns:
            Dict describing created orders (keys tp/sl) for logging purposes
        """
        pass

