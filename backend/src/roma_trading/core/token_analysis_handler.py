"""
Token analysis handler for chat service.

Handles token-specific analysis requests and generates comprehensive
market analysis with trading recommendations.
"""

import re
from typing import Optional, Dict, List
from loguru import logger
from roma_trading.agents import AgentManager
from roma_trading.toolkits.technical_analysis import TechnicalAnalysisToolkit


class TokenAnalysisHandler:
    """Handles token analysis requests in chat."""
    
    # Supported token symbols mapping
    TOKEN_MAPPING = {
        # Full names to symbols (English)
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "solana": "SOLUSDT",
        "binance": "BNBUSDT",
        "doge": "DOGEUSDT",
        "dogecoin": "DOGEUSDT",
        "ripple": "XRPUSDT",
        "xrp": "XRPUSDT",
        # Symbols
        "btc": "BTCUSDT",
        "eth": "ETHUSDT",
        "sol": "SOLUSDT",
        "bnb": "BNBUSDT",
        "doge": "DOGEUSDT",
        "xrp": "XRPUSDT",
        # Chinese names
        "比特币": "BTCUSDT",
        "以太坊": "ETHUSDT",
        "以太币": "ETHUSDT",
        "索拉纳": "SOLUSDT",
        "币安币": "BNBUSDT",
        "狗狗币": "DOGEUSDT",
        "瑞波币": "XRPUSDT",
    }
    
    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager
        self.ta_toolkit = TechnicalAnalysisToolkit()
    
    def detect_analysis_request(self, message: str) -> bool:
        """
        Detect if user message requests token analysis.
        
        Args:
            message: User's message
            
        Returns:
            True if analysis is requested
        """
        message_lower = message.lower()
        
        # Keywords that indicate analysis request (English and Chinese)
        analysis_keywords = [
            # English
            "analyze", "analysis", "analyze",
            "what about", "how about",
            "should i", "can i",
            "buy", "sell", "trade",
            "price", "trend", "signal",
            "recommendation", "advice",
            "what should", "what to do",
            # Chinese
            "分析", "怎么操作", "如何操作",
            "应该", "建议", "推荐",
            "买入", "卖出", "交易",
            "价格", "趋势", "信号",
            "操作", "怎么办"
        ]
        
        return any(keyword in message_lower for keyword in analysis_keywords)
    
    def extract_token_symbol(self, message: str) -> Optional[str]:
        """
        Extract token symbol from user message.
        Supports both predefined tokens and arbitrary tokens (e.g., MON -> MONUSDT).
        
        Args:
            message: User's message
            
        Returns:
            Token symbol (e.g., "BTCUSDT", "MONUSDT") or None
        """
        message_lower = message.lower()
        message_upper = message.upper()
        
        # Check for full symbol (e.g., "BTCUSDT", "MONUSDT")
        symbol_pattern = r'\b([A-Z]{2,10}USDT)\b'
        match = re.search(symbol_pattern, message_upper)
        if match:
            return match.group(1)
        
        # Check token mapping (predefined tokens with names)
        for token_name, symbol in self.TOKEN_MAPPING.items():
            if token_name in message_lower:
                return symbol
        
        # Try to find token codes (2-6 uppercase letters, not just predefined ones)
        # This allows arbitrary tokens like MON, PEPE, etc.
        # Token codes are typically 2-6 characters, all uppercase
        token_pattern = r'\b([A-Z]{2,6})\b'
        matches = re.findall(token_pattern, message_upper)
        
        # Filter out common English words that are not tokens
        excluded_words = {
            "USDT", "USD", "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
            "HER", "WAS", "ONE", "OUR", "OUT", "DAY", "GET", "HAS", "HIM", "HIS", "HOW",
            "ITS", "MAY", "NEW", "NOW", "OLD", "SEE", "TWO", "WHO", "BOY", "DID", "LET",
            "PUT", "SAY", "SHE", "TOO", "USE", "WHY", "YES", "YET", "ANY", "ASK", "BUY",
            "SELL", "TRADE", "PRICE", "TREND", "SIGNAL", "ABOUT", "SHOULD", "WHAT", "WHEN",
            "WHERE", "WHICH", "ANALYZE", "ANALYSIS"
        }
        
        for match in matches:
            # Skip if it's an excluded word
            if match in excluded_words:
                continue
            
            # If it's a known token from our mapping, return it
            if match in ["BTC", "ETH", "SOL", "BNB", "DOGE", "XRP"]:
                return f"{match}USDT"
            
            # For other uppercase codes (2-6 chars), assume it's a token and append USDT
            # This allows users to query arbitrary tokens like MON, PEPE, etc.
            # The DEX API will validate if the token exists
            # Token codes are typically 2-6 characters, all uppercase letters
            if 2 <= len(match) <= 6 and match.isalpha():
                return f"{match}USDT"
        
        return None
    
    async def fetch_token_data(
        self, 
        symbol: str, 
        timeframes: List[str] = None
    ) -> Dict:
        """
        Fetch comprehensive token data for analysis.
        
        Args:
            symbol: Token symbol (e.g., "BTCUSDT")
            timeframes: List of timeframes to analyze (default: ["15m", "1h", "4h"])
            
        Returns:
            Dictionary with market data and technical analysis
        """
        if timeframes is None:
            timeframes = ["15m", "1h", "4h"]
        
        # Get any agent to access DEX
        agents = self.agent_manager.get_all_agents()
        if not agents:
            raise RuntimeError("No agents available for data access")
        
        agent = self.agent_manager.get_agent(agents[0]["id"])
        dex = agent.dex
        
        # Fetch current price
        try:
            current_price = await dex.get_market_price(symbol)
        except ValueError as e:
            # Symbol not found on exchange
            error_msg = str(e)
            if "not found" in error_msg.lower() or "symbol" in error_msg.lower():
                raise ValueError(f"Token {symbol} is not available on this exchange. Please check if the symbol is correct.")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            raise RuntimeError(f"Failed to fetch price for {symbol}: {e}")
        
        # Fetch K-line data for each timeframe
        analysis_data = {}
        
        for timeframe in timeframes:
            try:
                klines = await dex.get_klines(symbol, interval=timeframe, limit=100)
                
                if klines and len(klines) >= 50:
                    analysis = self.ta_toolkit.analyze_klines(klines, interval=timeframe)
                    analysis_data[timeframe] = analysis
                else:
                    logger.warning(f"Insufficient data for {symbol} {timeframe}: {len(klines) if klines else 0} candles")
                    analysis_data[timeframe] = None
            except Exception as e:
                logger.error(f"Failed to fetch {timeframe} data for {symbol}: {e}")
                analysis_data[timeframe] = None
        
        # Fetch additional market data (funding rate, 24h stats, etc.)
        market_metadata = {}
        
        try:
            # Try to get funding rate (Aster)
            if hasattr(dex, 'get_premium_index'):
                try:
                    premium_data = await dex.get_premium_index(symbol)
                    if premium_data and isinstance(premium_data, list) and len(premium_data) > 0:
                        data = premium_data[0] if isinstance(premium_data[0], dict) else premium_data
                        market_metadata['funding_rate'] = float(data.get('lastFundingRate', 0)) * 100  # Convert to percentage
                        market_metadata['next_funding_time'] = data.get('nextFundingTime', 0)
                except Exception as e:
                    logger.debug(f"Could not fetch funding rate from premium_index: {e}")
            
            # Try to get funding rate (Hyperliquid)
            if hasattr(dex, 'get_meta_and_asset_ctxs'):
                try:
                    meta, asset_ctxs = await dex.get_meta_and_asset_ctxs()
                    # Find the asset context for this symbol
                    normalized_symbol = symbol.replace("USDT", "")
                    for ctx in asset_ctxs:
                        coin_name = ctx.get('coin', '')
                        if coin_name == normalized_symbol or coin_name == symbol:
                            funding_rate = ctx.get('funding', 0)
                            if funding_rate:
                                market_metadata['funding_rate'] = float(funding_rate) * 100  # Convert to percentage
                            break
                except Exception as e:
                    logger.debug(f"Could not fetch funding rate from meta_and_asset_ctxs: {e}")
            
            # Try to get 24h ticker stats (Aster)
            if hasattr(dex, 'get_ticker_24hr'):
                try:
                    ticker_data = await dex.get_ticker_24hr(symbol)
                    if ticker_data and isinstance(ticker_data, list) and len(ticker_data) > 0:
                        data = ticker_data[0] if isinstance(ticker_data[0], dict) else ticker_data
                        market_metadata['price_change_24h'] = float(data.get('priceChangePercent', 0))
                        market_metadata['volume_24h'] = float(data.get('volume', 0))
                        market_metadata['high_24h'] = float(data.get('highPrice', 0))
                        market_metadata['low_24h'] = float(data.get('lowPrice', 0))
                except Exception as e:
                    logger.debug(f"Could not fetch 24h ticker stats: {e}")
        except Exception as e:
            logger.debug(f"Failed to fetch additional market metadata: {e}")
        
        return {
            "symbol": symbol,
            "current_price": current_price,
            "analysis": analysis_data,
            "market_metadata": market_metadata
        }
    
    def format_analysis_prompt(
        self, 
        token_data: Dict, 
        language: str = "en"
    ) -> str:
        """
        Format token data into a prompt for AI analysis.
        
        Args:
            token_data: Token data dictionary from fetch_token_data
            language: Language for formatting ("en" or "zh")
            
        Returns:
            Formatted prompt string
        """
        symbol = token_data["symbol"]
        current_price = token_data["current_price"]
        analysis = token_data["analysis"]
        market_metadata = token_data.get("market_metadata", {})
        
        lines = []
        
        if language == "zh":
            lines.append(f"## {symbol} 市场数据分析")
            lines.append(f"\n当前价格: ${current_price:.4f}")
            
            # Add market metadata (funding rate, 24h stats)
            if market_metadata:
                if market_metadata.get('funding_rate') is not None:
                    funding_rate = market_metadata['funding_rate']
                    funding_sentiment = "看涨" if funding_rate > 0.01 else "看跌" if funding_rate < -0.01 else "中性"
                    lines.append(f"资金费率: {funding_rate:.4f}% ({funding_sentiment})")
                
                if market_metadata.get('price_change_24h') is not None:
                    lines.append(f"24小时涨跌: {market_metadata['price_change_24h']:+.2f}%")
                
                if market_metadata.get('volume_24h') is not None and market_metadata['volume_24h'] > 0:
                    lines.append(f"24小时成交量: ${market_metadata['volume_24h']:,.0f}")
            
            # Add analysis for each timeframe
            for timeframe, data in analysis.items():
                if data is None:
                    continue
                
                lines.append(f"\n### {timeframe} 时间框架")
                lines.append(self.ta_toolkit.format_market_data(
                    symbol, data, language="zh"
                ))
        else:
            lines.append(f"## {symbol} Market Data Analysis")
            lines.append(f"\nCurrent Price: ${current_price:.4f}")
            
            # Add market metadata (funding rate, 24h stats)
            if market_metadata:
                if market_metadata.get('funding_rate') is not None:
                    funding_rate = market_metadata['funding_rate']
                    funding_sentiment = "Bullish" if funding_rate > 0.01 else "Bearish" if funding_rate < -0.01 else "Neutral"
                    lines.append(f"Funding Rate: {funding_rate:.4f}% ({funding_sentiment})")
                
                if market_metadata.get('price_change_24h') is not None:
                    lines.append(f"24h Change: {market_metadata['price_change_24h']:+.2f}%")
                
                if market_metadata.get('volume_24h') is not None and market_metadata['volume_24h'] > 0:
                    lines.append(f"24h Volume: ${market_metadata['volume_24h']:,.0f}")
            
            # Add analysis for each timeframe
            for timeframe, data in analysis.items():
                if data is None:
                    continue
                
                lines.append(f"\n### {timeframe} Timeframe")
                lines.append(self.ta_toolkit.format_market_data(
                    symbol, data, language="en"
                ))
        
        return "\n".join(lines)

