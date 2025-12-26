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

    @staticmethod
    def calculate_bollinger_bands(
        prices: List[float], period: int = 20, std_dev: float = 2.0
    ) -> Dict:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: List of closing prices
            period: Moving average period
            std_dev: Standard deviation multiplier
            
        Returns:
            Dict with upper, middle, lower bands
        """
        prices_array = np.array(prices, dtype=float)
        upper, middle, lower = talib.BBANDS(
            prices_array, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev, matype=0
        )
        
        return {
            "upper": float(upper[-1]) if not np.isnan(upper[-1]) else 0.0,
            "middle": float(middle[-1]) if not np.isnan(middle[-1]) else 0.0,
            "lower": float(lower[-1]) if not np.isnan(lower[-1]) else 0.0,
        }

    @staticmethod
    def calculate_adx(
        highs: List[float], lows: List[float], closes: List[float], period: int = 14
    ) -> float:
        """
        Calculate ADX (Average Directional Index) - trend strength indicator.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            period: ADX period
            
        Returns:
            ADX value (0-100, higher = stronger trend)
        """
        highs_array = np.array(highs, dtype=float)
        lows_array = np.array(lows, dtype=float)
        closes_array = np.array(closes, dtype=float)
        
        adx = talib.ADX(highs_array, lows_array, closes_array, timeperiod=period)
        return float(adx[-1]) if not np.isnan(adx[-1]) else 0.0

    @staticmethod
    def calculate_obv(prices: List[float], volumes: List[float]) -> Dict:
        """
        Calculate OBV (On-Balance Volume) and its trend.
        
        Args:
            prices: List of closing prices
            volumes: List of volumes
            
        Returns:
            Dict with obv value and trend direction
        """
        prices_array = np.array(prices, dtype=float)
        volumes_array = np.array(volumes, dtype=float)
        
        obv = talib.OBV(prices_array, volumes_array)
        obv_value = float(obv[-1]) if not np.isnan(obv[-1]) else 0.0
        
        # Calculate trend (comparing last 10 periods)
        if len(obv) >= 10:
            recent_obv = obv[-10:]
            obv_trend = "up" if recent_obv[-1] > recent_obv[0] else "down"
        else:
            obv_trend = "neutral"
        
        return {
            "obv": obv_value,
            "trend": obv_trend,
        }

    @staticmethod
    def calculate_support_resistance(
        highs: List[float], lows: List[float], closes: List[float], lookback: int = 50
    ) -> Dict:
        """
        Calculate support and resistance levels based on recent price action.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of closing prices
            lookback: Number of periods to look back
            
        Returns:
            Dict with support and resistance levels
        """
        if len(highs) < lookback:
            lookback = len(highs)
        
        # Get recent price data
        recent_highs = highs[-lookback:]
        recent_lows = lows[-lookback:]
        recent_closes = closes[-lookback:]
        
        # Resistance: recent highs (top 3)
        sorted_highs = sorted(recent_highs, reverse=True)
        resistance_levels = sorted_highs[:3]
        
        # Support: recent lows (bottom 3)
        sorted_lows = sorted(recent_lows)
        support_levels = sorted_lows[:3]
        
        # Current price position relative to support/resistance
        current_price = closes[-1]
        nearest_resistance = min([r for r in resistance_levels if r > current_price], default=None)
        nearest_support = max([s for s in support_levels if s < current_price], default=None)
        
        return {
            "resistance_levels": resistance_levels,
            "support_levels": support_levels,
            "nearest_resistance": nearest_resistance,
            "nearest_support": nearest_support,
        }

    @classmethod
    def analyze_klines(cls, klines: List[Dict], interval: str = "15m") -> Dict:
        """
        Comprehensive analysis of kline data.
        
        Args:
            klines: List of kline dicts with OHLCV data
            interval: Timeframe ("15m", "1h", "4h")
            
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
        # Use shorter RSI period for shorter timeframes
        rsi_period = 7 if interval in ["15m", "3m", "5m"] else 14
        
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
        
        # Bollinger Bands
        bb_data = cls.calculate_bollinger_bands(closes)
        
        # ADX (trend strength)
        adx = cls.calculate_adx(highs, lows, closes)
        
        # OBV (volume trend)
        obv_data = cls.calculate_obv(closes, volumes)
        
        # Support and Resistance levels
        sr_levels = cls.calculate_support_resistance(highs, lows, closes)
        
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
            "bb_upper": bb_data["upper"],
            "bb_middle": bb_data["middle"],
            "bb_lower": bb_data["lower"],
            "adx": adx,
            "obv": obv_data["obv"],
            "obv_trend": obv_data["trend"],
            "support_levels": sr_levels["support_levels"],
            "resistance_levels": sr_levels["resistance_levels"],
            "nearest_support": sr_levels["nearest_support"],
            "nearest_resistance": sr_levels["nearest_resistance"],
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
            "bb_upper": None,
            "bb_middle": None,
            "bb_lower": None,
            "adx": 0.0,
            "obv": 0.0,
            "obv_trend": "neutral",
            "support_levels": [],
            "resistance_levels": [],
            "nearest_support": None,
            "nearest_resistance": None,
            "volume": 0.0,
            "volume_avg": 0.0,
            "volume_ratio": 1.0,
        }

    @classmethod
    def format_market_data(
        cls,
        symbol: str,
        data_short: Dict,
        data_4h: Optional[Dict] = None,
        language: str = "en",
    ) -> str:
        """
        Format market data for AI prompt.
        
        Args:
            symbol: Trading pair
            data_short: Short timeframe analysis data (15m, 1h, etc.)
            data_4h: 4-hour analysis data (optional)
            
        Returns:
            Formatted string for AI consumption
        """
        lines = [f"**{symbol}**"]
        
        if language == "zh":
            lines.append(f"价格：${data_short['current_price']:.4f}")
            
            if data_short['price_change_1h'] != 0:
                lines.append(f"1 小时涨跌：{data_short['price_change_1h']:+.2f}%")
            
            rsi_period = 7 if data_short.get('interval', '') in ['15m', '3m', '5m'] else 14
            lines.append(f"RSI({rsi_period})：{data_short['rsi']:.1f}")
            lines.append(f"MACD：{data_short['macd']['macd']:.4f}")
            lines.append(f"EMA20：${data_short['ema20']:.4f}")
            
            # Add ATR if available
            if data_short.get('atr', 0) > 0:
                atr_pct = (data_short['atr'] / data_short['current_price']) * 100
                lines.append(f"ATR：${data_short['atr']:.4f} ({atr_pct:.2f}%)")
            
            # Add Bollinger Bands if available
            if data_short.get('bb_upper') and data_short.get('bb_lower'):
                bb_position = ((data_short['current_price'] - data_short['bb_lower']) / 
                              (data_short['bb_upper'] - data_short['bb_lower'])) * 100
                lines.append(f"布林带位置：{bb_position:.1f}% (上轨：${data_short['bb_upper']:.4f}, 下轨：${data_short['bb_lower']:.4f})")
            
            # Add ADX if available
            if data_short.get('adx', 0) > 0:
                trend_strength = "强" if data_short['adx'] > 25 else "中等" if data_short['adx'] > 20 else "弱"
                lines.append(f"ADX：{data_short['adx']:.1f} (趋势强度：{trend_strength})")
            
            volume_ratio = data_short.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                lines.append(f"成交量：{volume_ratio:.2f} 倍均量 ⬆")
            elif volume_ratio > 1.0:
                lines.append(f"成交量：{volume_ratio:.2f} 倍均量 ↗")
            elif volume_ratio < 0.5:
                lines.append(f"成交量：{volume_ratio:.2f} 倍均量 ⬇")
            else:
                lines.append(f"成交量：{volume_ratio:.2f} 倍均量")
            
            # Add support/resistance if available
            if data_short.get('nearest_support') or data_short.get('nearest_resistance'):
                if data_short.get('nearest_support'):
                    support_pct = ((data_short['current_price'] - data_short['nearest_support']) / data_short['current_price']) * 100
                    lines.append(f"最近支撑位：${data_short['nearest_support']:.4f} (距离：{support_pct:.2f}%)")
                if data_short.get('nearest_resistance'):
                    resistance_pct = ((data_short['nearest_resistance'] - data_short['current_price']) / data_short['current_price']) * 100
                    lines.append(f"最近阻力位：${data_short['nearest_resistance']:.4f} (距离：{resistance_pct:.2f}%)")
            
            if data_4h:
                lines.append(f"\n4 小时趋势：{data_4h['price_change_4h']:+.2f}%")
                lines.append(f"RSI(14)：{data_4h['rsi']:.1f}")
                if data_4h.get('ema50'):
                    lines.append(f"EMA50：${data_4h['ema50']:.4f}")
        else:
            lines.append(f"Price: ${data_short['current_price']:.4f}")
            
            if data_short['price_change_1h'] != 0:
                lines.append(f"1h: {data_short['price_change_1h']:+.2f}%")
            
            rsi_period = 7 if data_short.get('interval', '') in ['15m', '3m', '5m'] else 14
            lines.append(f"RSI({rsi_period}): {data_short['rsi']:.1f}")
            lines.append(f"MACD: {data_short['macd']['macd']:.4f}")
            lines.append(f"EMA20: ${data_short['ema20']:.4f}")
            
            # Add ATR if available
            if data_short.get('atr', 0) > 0:
                atr_pct = (data_short['atr'] / data_short['current_price']) * 100
                lines.append(f"ATR: ${data_short['atr']:.4f} ({atr_pct:.2f}%)")
            
            # Add Bollinger Bands if available
            if data_short.get('bb_upper') and data_short.get('bb_lower'):
                bb_position = ((data_short['current_price'] - data_short['bb_lower']) / 
                              (data_short['bb_upper'] - data_short['bb_lower'])) * 100
                lines.append(f"BB Position: {bb_position:.1f}% (Upper: ${data_short['bb_upper']:.4f}, Lower: ${data_short['bb_lower']:.4f})")
            
            # Add ADX if available
            if data_short.get('adx', 0) > 0:
                trend_strength = "Strong" if data_short['adx'] > 25 else "Moderate" if data_short['adx'] > 20 else "Weak"
                lines.append(f"ADX: {data_short['adx']:.1f} (Trend: {trend_strength})")
            
            volume_ratio = data_short.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                lines.append(f"Volume: {volume_ratio:.2f}x avg ⬆")
            elif volume_ratio > 1.0:
                lines.append(f"Volume: {volume_ratio:.2f}x avg ↗")
            elif volume_ratio < 0.5:
                lines.append(f"Volume: {volume_ratio:.2f}x avg ⬇")
            else:
                lines.append(f"Volume: {volume_ratio:.2f}x avg")
            
            # Add support/resistance if available
            if data_short.get('nearest_support') or data_short.get('nearest_resistance'):
                if data_short.get('nearest_support'):
                    support_pct = ((data_short['current_price'] - data_short['nearest_support']) / data_short['current_price']) * 100
                    lines.append(f"Nearest Support: ${data_short['nearest_support']:.4f} ({support_pct:.2f}% away)")
                if data_short.get('nearest_resistance'):
                    resistance_pct = ((data_short['nearest_resistance'] - data_short['current_price']) / data_short['current_price']) * 100
                    lines.append(f"Nearest Resistance: ${data_short['nearest_resistance']:.4f} ({resistance_pct:.2f}% away)")
            
            if data_4h:
                lines.append(f"\n4h Trend: {data_4h['price_change_4h']:+.2f}%")
                lines.append(f"RSI(14): {data_4h['rsi']:.1f}")
                if data_4h.get('ema50'):
                    lines.append(f"EMA50: ${data_4h['ema50']:.4f}")
        
        return "\n".join(lines)

