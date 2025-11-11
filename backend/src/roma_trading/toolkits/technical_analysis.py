"""
Technical Analysis Toolkit using TA-Lib.

Provides technical indicators for market analysis: MACD, RSI, EMA, ATR, etc.
"""

import numpy as np
import talib
from typing import List, Dict, Optional
from loguru import logger


class TechnicalAnalysisToolkit:
    """Technical analysis toolkit for crypto market analysis."""

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """
        Calculate MACD indicator.
        
        Args:
            prices: List of closing prices
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period
            
        Returns:
            Dict with macd, signal, histogram values
        """
        prices_array = np.array(prices, dtype=float)
        macd, signal_line, histogram = talib.MACD(
            prices_array, fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
        
        return {
            "macd": float(macd[-1]) if not np.isnan(macd[-1]) else 0.0,
            "signal": float(signal_line[-1]) if not np.isnan(signal_line[-1]) else 0.0,
            "histogram": float(histogram[-1]) if not np.isnan(histogram[-1]) else 0.0,
        }

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """
        Calculate RSI indicator.
        
        Args:
            prices: List of closing prices
            period: RSI period
            
        Returns:
            RSI value (0-100)
        """
        prices_array = np.array(prices, dtype=float)
        rsi = talib.RSI(prices_array, timeperiod=period)
        return float(rsi[-1]) if not np.isnan(rsi[-1]) else 50.0

    @staticmethod
    def calculate_ema(prices: List[float], period: int = 20) -> float:
        """
        Calculate EMA (Exponential Moving Average).
        
        Args:
            prices: List of closing prices
            period: EMA period
            
        Returns:
            EMA value
        """
        prices_array = np.array(prices, dtype=float)
        ema = talib.EMA(prices_array, timeperiod=period)
        return float(ema[-1]) if not np.isnan(ema[-1]) else 0.0

    @staticmethod
    def calculate_atr(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> float:
        """
        Calculate ATR (Average True Range).
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            period: ATR period
            
        Returns:
            ATR value
        """
        highs_array = np.array(highs, dtype=float)
        lows_array = np.array(lows, dtype=float)
        closes_array = np.array(closes, dtype=float)
        
        atr = talib.ATR(highs_array, lows_array, closes_array, timeperiod=period)
        return float(atr[-1]) if not np.isnan(atr[-1]) else 0.0

    @classmethod
    def analyze_klines(cls, klines: List[Dict], interval: str = "3m") -> Dict:
        """
        Comprehensive analysis of kline data.
        
        Args:
            klines: List of kline dicts with OHLCV data
            interval: Timeframe ("3m", "1h", "4h")
            
        Returns:
            Dict with all technical indicators
        """
        if not klines or len(klines) < 50:
            logger.warning(f"Insufficient kline data: {len(klines)} candles")
            return cls._empty_analysis()
        
        # Extract price data
        opens = [k["open"] for k in klines]
        highs = [k["high"] for k in klines]
        lows = [k["low"] for k in klines]
        closes = [k["close"] for k in klines]
        volumes = [k["volume"] for k in klines]
        
        closes_array = np.array(closes, dtype=float)
        volumes_array = np.array(volumes, dtype=float)
        
        # Calculate indicators based on interval
        rsi_period = 7 if interval == "3m" else 14
        
        # Price changes
        price_change_1h = ((closes[-1] - closes[-20]) / closes[-20] * 100) if len(closes) >= 20 else 0.0
        price_change_4h = ((closes[-1] - closes[-80]) / closes[-80] * 100) if len(closes) >= 80 else 0.0
        
        # MACD
        macd_data = cls.calculate_macd(closes)
        
        # RSI
        rsi = cls.calculate_rsi(closes, period=rsi_period)
        
        # EMAs
        ema20 = cls.calculate_ema(closes, period=20)
        ema50 = cls.calculate_ema(closes, period=50) if len(closes) >= 50 else None
        
        # ATR
        atr = cls.calculate_atr(highs, lows, closes)
        
        # Volume analysis
        volume_avg = float(np.mean(volumes_array[-20:])) if len(volumes) >= 20 else 0.0
        volume_ratio = (volumes[-1] / volume_avg) if volume_avg > 0 else 1.0
        
        return {
            "current_price": float(closes[-1]),
            "price_change_1h": price_change_1h,
            "price_change_4h": price_change_4h,
            "macd": macd_data,
            "rsi": rsi,
            "ema20": ema20,
            "ema50": ema50,
            "atr": atr,
            "volume": float(volumes[-1]),
            "volume_avg": volume_avg,
            "volume_ratio": volume_ratio,
            "interval": interval,
        }

    @staticmethod
    def _empty_analysis() -> Dict:
        """Return empty analysis for insufficient data."""
        return {
            "current_price": 0.0,
            "price_change_1h": 0.0,
            "price_change_4h": 0.0,
            "macd": {"macd": 0.0, "signal": 0.0, "histogram": 0.0},
            "rsi": 50.0,
            "ema20": 0.0,
            "ema50": None,
            "atr": 0.0,
            "volume": 0.0,
            "volume_avg": 0.0,
            "volume_ratio": 1.0,
        }

    @classmethod
    def format_market_data(
        cls,
        symbol: str,
        data_3m: Dict,
        data_4h: Optional[Dict] = None,
        language: str = "en",
    ) -> str:
        """
        Format market data for AI prompt.
        
        Args:
            symbol: Trading pair
            data_3m: 3-minute analysis data
            data_4h: 4-hour analysis data (optional)
            
        Returns:
            Formatted string for AI consumption
        """
        lines = [f"**{symbol}**"]
        
        if language == "zh":
            lines.append(f"价格：${data_3m['current_price']:.4f}")
            
            if data_3m['price_change_1h'] != 0:
                lines.append(f"1 小时涨跌：{data_3m['price_change_1h']:+.2f}%")
            
            lines.append(f"RSI(7)：{data_3m['rsi']:.1f}")
            lines.append(f"MACD：{data_3m['macd']['macd']:.4f}")
            lines.append(f"EMA20：${data_3m['ema20']:.4f}")
            
            if data_3m['volume_ratio'] > 1.5:
                lines.append(f"成交量：{data_3m['volume_ratio']:.1f} 倍均量 ⬆")
            
            if data_4h:
                lines.append(f"\n4 小时趋势：{data_4h['price_change_4h']:+.2f}%")
                lines.append(f"RSI(14)：{data_4h['rsi']:.1f}")
                if data_4h.get('ema50'):
                    lines.append(f"EMA50：${data_4h['ema50']:.4f}")
        else:
            lines.append(f"Price: ${data_3m['current_price']:.4f}")
        
        if data_3m['price_change_1h'] != 0:
            lines.append(f"1h: {data_3m['price_change_1h']:+.2f}%")
        
        lines.append(f"RSI(7): {data_3m['rsi']:.1f}")
        lines.append(f"MACD: {data_3m['macd']['macd']:.4f}")
        lines.append(f"EMA20: ${data_3m['ema20']:.4f}")
        
        if data_3m['volume_ratio'] > 1.5:
            lines.append(f"Volume: {data_3m['volume_ratio']:.1f}x avg ⬆")
        
        if data_4h:
            lines.append(f"\n4h Trend: {data_4h['price_change_4h']:+.2f}%")
            lines.append(f"RSI(14): {data_4h['rsi']:.1f}")
            if data_4h.get('ema50'):
                lines.append(f"EMA50: ${data_4h['ema50']:.4f}")
        
        return "\n".join(lines)

