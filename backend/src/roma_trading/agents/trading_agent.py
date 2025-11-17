"""
Trading Agent with DSPy-powered AI decision making.

This agent orchestrates the complete trading cycle:
1. Fetch market data and technical indicators
2. Analyze account state and positions
3. Get AI decision via DSPy
4. Execute trades
5. Log everything for performance analysis
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import dspy
from loguru import logger

from roma_trading.toolkits import AsterToolkit, TechnicalAnalysisToolkit
from roma_trading.config import get_settings
from roma_trading.core import (
    DecisionLogger,
    PerformanceAnalyzer,
    build_strategy_request,
    get_remote_strategy_client,
    RemoteStrategyError,
    RemoteStrategyPaymentError,
    RemoteStrategyConfigError,
)

# Import HyperliquidToolkit if available
try:
    from roma_trading.toolkits.hyperliquid_toolkit import HyperliquidToolkit
except ImportError:
    HyperliquidToolkit = None


class TradingDecision(dspy.Signature):
    """
    AI Trading Decision Signature.
    
    The AI receives comprehensive market data and must decide whether to:
    - Close existing positions
    - Open new positions (long/short)
    - Hold current positions
    - Wait for better opportunities
    """
    
    # Inputs
    system_prompt: str = dspy.InputField(desc="Trading rules and constraints")
    market_context: str = dspy.InputField(desc="Current market state, account, positions, performance")
    
    # Outputs
    chain_of_thought: str = dspy.OutputField(desc="Reasoning process and analysis")
    decisions_json: str = dspy.OutputField(desc="JSON array of trading decisions")


class TradingAgent:
    """
    AI-powered trading agent with complete lifecycle management.
    
    Features:
    - Automated market scanning
    - Technical analysis
    - AI-driven decision making
    - Risk management
    - Performance tracking
    """

    def __init__(self, agent_id: str, config: Dict, trading_lock: asyncio.Lock = None):
        """
        Initialize trading agent.
        
        Args:
            agent_id: Unique agent identifier
            config: Agent configuration dict
            trading_lock: Shared lock to prevent concurrent trading
        """
        self.agent_id = agent_id
        self.config = config
        self.trading_lock = trading_lock or asyncio.Lock()  # Use shared or create own
        
        # Initialize DEX toolkit based on exchange.type
        exchange_cfg = config.get("exchange", {})
        dex_type = exchange_cfg.get("type", "aster").lower()
        if dex_type == "hyperliquid":
            if HyperliquidToolkit is None:
                raise ImportError(
                    "HyperliquidToolkit not available. "
                    "Install hyperliquid-python-sdk: pip install hyperliquid-python-sdk"
                )
            self.dex = HyperliquidToolkit(
                api_key=exchange_cfg.get("api_key", ""),
                api_secret=exchange_cfg.get("api_secret", ""),
                account_id=exchange_cfg.get("account_id"),
                testnet=exchange_cfg.get("testnet", False),
                hedge_mode=exchange_cfg.get("hedge_mode", False),
            )
            logger.info(f"TradingAgent {agent_id}: using Hyperliquid toolkit")
        else:
            self.dex = AsterToolkit(
                user=exchange_cfg["user"],
                signer=exchange_cfg["signer"],
                private_key=exchange_cfg["private_key"],
                hedge_mode=exchange_cfg.get("hedge_mode", False),
            )
            logger.info(f"TradingAgent {agent_id}: using Aster toolkit")
        
        # Initialize technical analysis
        self.ta = TechnicalAnalysisToolkit()
        
        # Initialize decision logger
        self.logger_module = DecisionLogger(agent_id)
        
        # Initialize performance analyzer
        self.performance = PerformanceAnalyzer()
        self.default_prompt_language = self._normalize_language(
            self.config["strategy"].get("prompt_language")
        )
        self.config["strategy"]["prompt_language"] = self.default_prompt_language
        self.last_account_snapshot: Dict = {}

        # Advanced order configuration
        self.advanced_orders = self.config["strategy"].get("advanced_orders", {})
        
        # Initialize DSPy LLM and decision module
        self.lm = self._init_llm()
        self.decision_module = dspy.ChainOfThought(TradingDecision)
        
        # Trading state - restore cycle count from previous logs
        self.cycle_count = self.logger_module.get_last_cycle_number()
        self.start_time = datetime.now()
        self.is_running = False
        
        if self.cycle_count > 0:
            logger.info(f"Initialized TradingAgent: {agent_id} ({config['agent']['name']}) - Resuming from cycle #{self.cycle_count}")
        else:
            logger.info(f"Initialized TradingAgent: {agent_id} ({config['agent']['name']}) - Starting fresh")

    def _init_llm(self):
        """Initialize DSPy LLM based on configuration."""
        llm_config = self.config["llm"]
        provider = llm_config["provider"]
        model = llm_config.get("model", "")
        
        if provider == "deepseek":
            # DeepSeek API
            lm = dspy.LM(
                f"deepseek/{model}" if model else "deepseek/deepseek-chat",
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        elif provider == "qwen":
            # Qwen API (Alibaba Cloud DashScope)
            # Support different regions: china uses dashscope.aliyuncs.com, others use dashscope-intl.aliyuncs.com
            model_name = model if model else "qwen-max"
            location = llm_config.get("location", "china").lower()
            if location == "china":
                api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            else:
                api_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            
            # Use "dashscope/" prefix for DashScope models
            lm = dspy.LM(
                f"dashscope/{model_name}",
                api_base=api_base,
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        elif provider == "anthropic":
            # Anthropic Claude API
            lm = dspy.LM(
                f"anthropic/{model}" if model else "anthropic/claude-sonnet-4.5",
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        elif provider == "xai":
            # xAI Grok API
            lm = dspy.LM(
                f"xai/{model}" if model else "xai/grok-4",
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        elif provider == "google":
            # Google Gemini API
            lm = dspy.LM(
                f"gemini/{model}" if model else "gemini/gemini-2.5-pro",
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        elif provider == "openai":
            # OpenAI GPT API
            lm = dspy.LM(
                f"openai/{model}" if model else "openai/gpt-5",
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        elif provider == "custom":
            # Custom LLM endpoint
            lm = dspy.LM(
                model=llm_config["model"],
                api_base=llm_config.get("base_url"),
                api_key=llm_config["api_key"],
                temperature=llm_config.get("temperature", 0.15),
                max_tokens=llm_config.get("max_tokens", 4000),
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        logger.info(f"Initialized DSPy LM for provider '{provider}'")
        return lm

    async def start(self):
        """Start the trading loop."""
        self.is_running = True
        scan_interval = self.config["strategy"]["scan_interval_minutes"] * 60
        
        logger.info(f"Starting trading loop for {self.agent_id}, interval={scan_interval}s")
        
        while self.is_running:
            try:
                await self.trading_cycle()
            except Exception as e:
                logger.error(f"Error in trading cycle: {e}", exc_info=True)
            
            await asyncio.sleep(scan_interval)

    async def stop(self):
        """Stop the trading loop."""
        self.is_running = False
        await self.dex.close()
        logger.info(f"Stopped trading agent {self.agent_id}")

    async def trading_cycle(self):
        """Execute one complete trading cycle."""
        self.cycle_count += 1
        runtime_minutes = int((datetime.now() - self.start_time).total_seconds() / 60)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Agent {self.agent_id} - Cycle #{self.cycle_count} | Runtime: {runtime_minutes}min")
        logger.info(f"{'='*60}\n")
        
        # Acquire trading lock to prevent concurrent trading
        # This ensures only one agent trades at a time
        async with self.trading_lock:
            logger.debug(f"🔒 {self.agent_id} acquired trading lock")
            
            # 1. Clean up any stale orders first (free up margin)
            logger.debug("Checking for stale orders to cancel...")
            for symbol in self.config["strategy"]["default_coins"]:
                try:
                    await self.dex._cancel_all_orders(symbol)
                except Exception as e:
                    logger.debug(f"No orders to cancel for {symbol}: {e}")
            
            # 2. Fetch account and positions
            account = await self.dex.get_account_balance()
            positions = await self.dex.get_positions()

            settings = get_settings()

            if settings.remote_strategy_enabled:
                remote_handled = await self._handle_remote_strategy(
                    settings=settings,
                    account=account,
                    positions=positions,
                )
                if remote_handled:
                    logger.info(
                        "Remote strategy fulfilled for agent %s cycle %s; skipping local execution",
                        self.agent_id,
                        self.cycle_count,
                    )
                    return
            
            # Calculate this agent's budget
            max_usage_pct = self.config["strategy"].get("max_account_usage_pct", 100)
            agent_budget = account['available_balance'] * (max_usage_pct / 100)
            
            logger.info(
                f"Account: Total=${account['total_wallet_balance']:.2f}, "
                f"Available=${account['available_balance']:.2f}, "
                f"Agent Budget=${agent_budget:.2f} ({max_usage_pct}%), "
                f"Positions: {len(positions)}"
            )
            
            # 3. Fetch market data
            market_data = await self._fetch_market_data(positions)
            
            # 4. Get performance metrics
            trades = self.logger_module.get_trade_history()
            performance_metrics = self.performance.calculate_metrics(trades)
            
            # 5. Build prompts
            prompt_language = self._resolve_prompt_language()
            system_prompt = self._build_system_prompt(language=prompt_language)
            market_context = self._build_market_context(
                account,
                positions,
                market_data,
                performance_metrics,
                language=prompt_language,
            )
            
            # 6. AI Decision
            logger.info("Calling AI for decision...")
            result = await asyncio.to_thread(
                self._run_decision_module,
                system_prompt,
                market_context,
            )
            
            # 7. Parse and execute decisions
            decisions = self._parse_decisions(result.decisions_json)
            
            logger.info(f"AI Decision: {len(decisions)} actions")
            logger.debug(f"Chain of Thought:\n{result.chain_of_thought}")
            
            await self._execute_decisions(decisions)
            
            # 8. Log everything
            self.logger_module.log_decision(
                cycle=self.cycle_count,
                chain_of_thought=result.chain_of_thought,
                decisions=decisions,
                account=account,
                positions=positions,
            )

            self.last_account_snapshot = dict(account)
            
            logger.debug(f"🔓 {self.agent_id} released trading lock")
        
        logger.info(f"Cycle #{self.cycle_count} complete\n")

    async def _handle_remote_strategy(self, settings, account: Dict, positions: List[Dict]) -> bool:
        """Attempt to fetch remote strategy; return True if handled and local cycle should stop."""

        try:
            remote_client = await get_remote_strategy_client()
        except RemoteStrategyConfigError as exc:
            logger.error("Remote strategy disabled due to configuration error: {}", exc)
            return False

        strategy_cfg = self.config.get("strategy", {})
        exchange_cfg = self.config.get("exchange", {})

        try:
            request_payload = build_strategy_request(
                agent_id=self.agent_id,
                exchange_cfg=exchange_cfg,
                strategy_cfg=strategy_cfg,
                account_snapshot=account,
                positions=positions,
                cycle=self.cycle_count,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to construct remote strategy request: {}", exc)
            fallback_mode = (settings.remote_fallback_mode or "local").lower()
            return fallback_mode != "local"

        try:
            result = await remote_client.request_strategy(request_payload)
        except RemoteStrategyPaymentError as exc:
            logger.error("Remote strategy payment failed: {}", exc)
            fallback_mode = (settings.remote_fallback_mode or "local").lower()
            if fallback_mode == "error":
                raise
            if fallback_mode == "wait":
                return True
            return False
        except RemoteStrategyError as exc:
            logger.error("Remote strategy request failed: {}", exc)
            fallback_mode = (settings.remote_fallback_mode or "local").lower()
            if fallback_mode == "error":
                raise
            if fallback_mode == "wait":
                return True
            return False
        except Exception as exc:  # pragma: no cover - unexpected
            logger.exception("Unexpected error while requesting remote strategy: {}", exc)
            fallback_mode = (settings.remote_fallback_mode or "local").lower()
            if fallback_mode == "error":
                raise
            if fallback_mode == "wait":
                return True
            return False

        self.logger_module.log_remote_strategy(
            cycle=self.cycle_count,
            account=account,
            positions=positions,
            payload=result.to_logging_payload(),
        )

        strategy = result.response.strategy
        logger.info("Remote strategy summary: %s", strategy.summary)
        if strategy.steps:
            for idx, step in enumerate(strategy.steps, start=1):
                logger.info("Remote step %d: %s", idx, step)

        fallback_mode = (settings.remote_fallback_mode or "local").lower()
        if fallback_mode == "local":
            # After successful remote strategy we simply skip local execution.
            return True
        if fallback_mode == "wait":
            return True

        return True

    async def _fetch_market_data(self, positions: List[Dict]) -> Dict:
        """Fetch market data for relevant symbols."""
        symbols = self.config["strategy"]["default_coins"]
        
        # Add position symbols
        for pos in positions:
            if pos["symbol"] not in symbols:
                symbols.append(pos["symbol"])
        
        market_data = {}
        
        for symbol in symbols:
            try:
                # Get 3m and 4h klines
                klines_3m = await self.dex.get_klines(symbol, interval="3m", limit=100)
                klines_4h = await self.dex.get_klines(symbol, interval="4h", limit=100)
                
                # Analyze
                data_3m = self.ta.analyze_klines(klines_3m, interval="3m")
                data_4h = self.ta.analyze_klines(klines_4h, interval="4h")
                
                market_data[symbol] = {
                    "3m": data_3m,
                    "4h": data_4h,
                }
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
        
        return market_data

    def _normalize_language(self, language: Optional[str]) -> str:
        """Normalize user-provided language codes to supported values."""
        if not language:
            return "en"
        lang = language.lower()
        if lang.startswith("zh"):
            return "zh"
        return "en"

    def _resolve_prompt_language(self, language: Optional[str] = None) -> str:
        """Resolve prompt language using override or default configuration."""
        if language:
            return self._normalize_language(language)
        return self.default_prompt_language or "en"

    def _run_decision_module(self, system_prompt: str, market_context: str):
        """Execute DSPy decision module in a worker thread to avoid blocking event loop."""
        with dspy.context(lm=self.lm):
            return self.decision_module(
                system_prompt=system_prompt,
                market_context=market_context,
            )

    def _build_system_prompt(self, language: Optional[str] = None, include_custom: bool = True) -> str:
        """Build system prompt with trading rules and optional custom prompts."""
        lang = self._resolve_prompt_language(language)
        risk = self.config["strategy"]["risk_management"]
        
        # Base system prompt (core rules only)
        if lang == "zh":
            base_prompt = f"""你是一名专业的加密货币永续合约交易AI。

**核心规则：**
1. 最大持仓数量：{risk['max_positions']}
2. 最大杠杆倍数：{risk['max_leverage']}x
3. 单笔持仓规模上限：账户资金的 {risk['max_position_size_pct']}%
4. 总持仓规模上限：账户总余额的 {risk.get('max_total_position_pct', 80)}%
5. 无持仓时单笔下单上限：可用资金的 {risk.get('max_single_trade_pct', 50)}%
6. 有持仓时单笔加仓上限：可用资金的 {risk.get('max_single_trade_with_positions_pct', 30)}%
7. 止损阈值：{risk['stop_loss_pct']}%
8. 止盈阈值：{risk['take_profit_pct']}%
9. 风险回报比：必须 ≥ 1:3

**关键步骤——先判断市场结构：**
在做出任何交易决策之前，必须先识别市场所处的状态：

1. **上升趋势**：价格不断创新高且高点抬高，价格位于 EMA(20) 之上，RSI 向上
   - 方向偏向：优先考虑做多，但仍需确认
   - 入场方式：回踩支撑或放量突破阻力
   
2. **下降趋势**：价格不断创新低且高点降低，价格位于 EMA(20) 之下，RSI 向下
   - 方向偏向：优先考虑做空（在下跌趋势中这是默认策略）
   - 入场方式：反弹到阻力位或放量跌破支撑
   - 不要忽视做空机会
   
3. **震荡/盘整**：价格在支撑与阻力之间来回波动，信号混杂
   - 方向偏向：缩小仓位或保持观望
   - 入场方式：仅在放量突破时考虑

**多空平衡提醒：**
- 禁止只做多！必须保持做多与做空的客观性
- 在明显下跌趋势中，应主动寻找做空机会
- 只有在出现强烈反转信号时（RSI 超卖 + 看涨背离 + 成交量放大）才考虑逆势做多
- 记住：下跌同样可以盈利，做空与做多同样重要

**入场信号要求（多维确认）：**
在开仓前需要多维度的信号匹配，但同时保持灵活：

1. **趋势方向（核心维度）**： 
   - 做多：价格位于 EMA(20) 上方并创新高
   - 做空：价格位于 EMA(20) 下方并创新低
   - 这是最重要的信号

2. **动量（次要维度）**：
   - 做多：RSI(14) > 50（温和多头动量），RSI > 55（强劲）
   - 做空：RSI(14) < 50（温和空头动量），RSI < 45（强劲）
   - RSI 极值（超买/超卖）也可提示反转

3. **MACD 辅助确认**：
   - 尽量让 MACD 柱状图方向与交易方向一致
   - 做多：MACD 线在信号线之上更佳，但不是硬性要求
   - 做空：MACD 线在信号线之下更佳，但不是硬性要求
   - MACD 背离可提示反转

4. **成交量（辅助维度）**：
   - 突破/跌破时的放量最理想
   - 但不能仅因量能较低就放弃交易

**最低入场标准：**
- 四个信号中至少满足两个（趋势 + 任意一个辅助信号）
- 强趋势配合 RSI 确认即可入场
- MACD 与成交量属于加分项，但不是必需条件

**拒绝交易的情形：**
- 核心信号严重冲突（如强势上升但 RSI < 30 且 MACD 明显看空）
- 市场明显震荡且没有放量突破
- 只有单一信号、缺少确认且信心不足

**持仓管理原则：**
- 每笔交易初始风险控制在权益的 0.5%-1.0%
- 先设定止损，再计算仓位规模
- 当盈利达到 1R 后可将止损移动至保本
- 2R 时可部分止盈，剩余仓位目标 3R
- 严禁对亏损仓位补仓
- 只允许对盈利仓位加仓

**最小下单要求：**
- 所有合约最小下单数量为 0.001
- 10 倍杠杆下的参考保证金需求：
  * BTCUSDT @ $110k：约 $11
  * ETHUSDT @ $3.9k：约 $0.4
  * BNBUSDT @ $1.1k：约 $0.11
  * SOLUSDT @ $190：约 $0.02

**品种选择提醒：**
- 可用资金低于 $15 时不要交易 BTCUSDT（成本过高）
- 可用资金低于 $5 时聚焦 SOLUSDT、BNBUSDT、DOGEUSDT、XRPUSDT（更容易满足最小仓位）
- 选择你确实能够满足最小下单要求的合约
- 若无法满足保证金要求，请放弃该机会

**交易频率：**
- 在积极寻找机会与保持纪律之间取得平衡
- 每小时最多 3 笔交易（由 2 提高）
- 每日最多 12 笔交易（由 8 提高）
- 若出现连续 4 笔亏损（由 3 提高），暂停并重新评估
- 空仓是允许的，但要主动寻找机会
- 不要过度保守，只要看到合适机会就执行
"""
        else:
            base_prompt = f"""You are a professional cryptocurrency futures trading AI.

**CORE RULES:**
1. Max positions: {risk['max_positions']}
2. Max leverage: {risk['max_leverage']}x
3. Single position limit: {risk['max_position_size_pct']}% of account
4. Total positions limit: {risk.get('max_total_position_pct', 80)}% of total balance
5. Single trade limit (no positions): {risk.get('max_single_trade_pct', 50)}% of available
6. Single trade limit (with positions): {risk.get('max_single_trade_with_positions_pct', 30)}% of available
7. Stop loss: {risk['stop_loss_pct']}%
8. Take profit: {risk['take_profit_pct']}%
9. Risk-reward ratio: Must be >= 1:3

**CRITICAL - MARKET REGIME CLASSIFICATION (MUST DO FIRST):**
Before making ANY trading decision, you MUST first classify the market regime:

1. **UPTREND**: Price making higher highs and higher lows, price above EMA(20), RSI trending up
   - Bias: LONG preferred, but still require confirmation
   - Entry: Look for pullbacks to support, breakouts above resistance
   
2. **DOWNTREND**: Price making lower highs and lower lows, price below EMA(20), RSI trending down
   - Bias: SHORT preferred (this is your default in downtrends!)
   - Entry: Look for rallies to resistance, breakdowns below support
   - DO NOT ignore short opportunities in downtrends
   
3. **RANGING/SIDEWAYS**: Price bouncing between support/resistance, mixed signals
   - Bias: Reduce position size or stay flat
   - Entry: Only trade clear breakouts with volume confirmation

**ANTI-BIAS - LONG/SHORT BALANCE:**
- NO LONG BIAS! You must be equally willing to trade SHORT as LONG
- In downtrends, SHORT is the default strategy - actively look for short opportunities
- If market is clearly downtrending, you should prefer short positions over long
- Only open long positions in downtrends if you see very strong reversal signals (RSI oversold + bullish divergence + volume spike)
- Remember: Shorting is just as valid as longing - profit from price going down

**ENTRY REQUIREMENTS - SIGNAL CONFIRMATION:**
You should have alignment across multiple dimensions before opening a position, but be flexible:

1. **Trend Direction** (Primary): 
   - Long: Price above EMA(20), making higher highs
   - Short: Price below EMA(20), making lower lows
   - This is the most important signal

2. **Momentum** (Secondary):
   - Long: RSI(14) > 50 (moderate bullish momentum) or RSI > 55 (strong)
   - Short: RSI(14) < 50 (moderate bearish momentum) or RSI < 45 (strong)
   - RSI extremes (oversold/overbought) can also signal reversals

3. **MACD Confirmation** (Supporting):
   - MACD histogram should align with your direction when possible
   - For longs: MACD line above signal line preferred, but not required
   - For shorts: MACD line below signal line preferred, but not required
   - MACD divergence can signal reversals

4. **Volume** (Supporting):
   - Volume spikes on breakouts/breakdowns are ideal
   - But don't reject trades solely due to lower volume

**Minimum Entry Requirements:**
- At least 2 out of 4 signals should align (trend + one other)
- Strong trend with RSI confirmation is sufficient
- MACD and volume are nice-to-have but not mandatory

**REJECT TRADES IF:**
- Strong signal conflicts (e.g., strong uptrend but RSI < 30 and MACD strongly bearish)
- Market is clearly ranging AND no clear breakout signal
- Single-dimension signal with no confirmation AND low confidence

**POSITION MANAGEMENT:**
- Initial risk per trade: 0.5-1.0% of equity
- Set stop loss FIRST, then position size
- Move stop to breakeven only after position is profitable by 1R
- Take partial profits at 2R, let runners go to 3R
- NEVER average down on losing positions
- Only pyramid/add to WINNING positions

**IMPORTANT - Minimum Order Requirements:**
- ALL coins have 0.001 minimum quantity
- Minimum margin needed (@ 10x leverage):
  * BTCUSDT @ $110k: ~$11 margin
  * ETHUSDT @ $3.9k: ~$0.4 margin  
  * BNBUSDT @ $1.1k: ~$0.11 margin
  * SOLUSDT @ $190: ~$0.02 margin

**CRITICAL - Coin Selection:**
- If available balance < $15: DO NOT trade BTCUSDT (too expensive)
- If available balance < $5: Focus on SOLUSDT, BNBUSDT, DOGEUSDT, XRPUSDT (cheaper)
- Choose coins you can ACTUALLY afford at minimum order size
- Better to skip than request impossible trades

**TRADING FREQUENCY:**
- Balance quality and quantity - be proactive but not reckless
- Maximum 3 trades per hour (increased from 2)
- Maximum 12 trades per day (increased from 8)
- If you've made 4 consecutive losing trades (increased from 3), pause and reassess
- Flat/empty portfolio is acceptable, but actively look for opportunities
- Don't be overly conservative - if you see a good setup, take it
"""
        
        # Add custom prompts if enabled
        custom_prompts = self.config["strategy"].get("custom_prompts", {})
        
        if include_custom and custom_prompts.get("enabled", False):
            custom_sections = []
            heading_map = {
                "trading_philosophy": {
                    "en": "**YOUR TRADING PHILOSOPHY:**",
                    "zh": "**你的交易理念：**",
                },
                "entry_preferences": {
                    "en": "**YOUR ENTRY PREFERENCES:**",
                    "zh": "**你的入场偏好：**",
                },
                "position_management": {
                    "en": "**YOUR POSITION MANAGEMENT:**",
                    "zh": "**你的持仓管理：**",
                },
                "market_preferences": {
                    "en": "**YOUR MARKET PREFERENCES:**",
                    "zh": "**你的市场偏好：**",
                },
                "additional_rules": {
                    "en": "**YOUR ADDITIONAL RULES:**",
                    "zh": "**你的附加规则：**",
                },
            }
            
            if custom_prompts.get("trading_philosophy"):
                custom_sections.append(
                    f"\n{heading_map['trading_philosophy'][lang]}\n{custom_prompts['trading_philosophy']}\n"
                )
            
            if custom_prompts.get("entry_preferences"):
                custom_sections.append(
                    f"\n{heading_map['entry_preferences'][lang]}\n{custom_prompts['entry_preferences']}\n"
                )
            
            if custom_prompts.get("position_management"):
                custom_sections.append(
                    f"\n{heading_map['position_management'][lang]}\n{custom_prompts['position_management']}\n"
                )
            
            if custom_prompts.get("market_preferences"):
                custom_sections.append(
                    f"\n{heading_map['market_preferences'][lang]}\n{custom_prompts['market_preferences']}\n"
                )
            
            if custom_prompts.get("additional_rules"):
                custom_sections.append(
                    f"\n{heading_map['additional_rules'][lang]}\n{custom_prompts['additional_rules']}\n"
                )
            
            if custom_sections:
                base_prompt += "\n" + "\n".join(custom_sections)
        
        # Output format
        if lang == "zh":
            base_prompt += """
**输出格式：**
首先提供你的链式推理分析，必须包含：
1. 市场结构判断（上升/下降/震荡）
2. 多维信号核查（趋势、动量、MACD、成交量）
3. 风险评估
4. 决策理由

然后输出一个 JSON 数组列出所有决策：

示例（做多）：
{{"action": "open_long", "symbol": "BTCUSDT", "leverage": 5, "position_size_usd": 1000, "stop_loss": 94000, "take_profit": 98000, "confidence": 0.75, "reasoning": "上涨趋势确认，RSI 58，MACD 看多，突破伴随放量"}}

示例（做空——下跌趋势中务必使用）：
{{"action": "open_short", "symbol": "ETHUSDT", "leverage": 5, "position_size_usd": 800, "stop_loss": 4100, "take_profit": 3700, "confidence": 0.80, "reasoning": "下降趋势确认，RSI 42，MACD 看空，跌破支撑伴随放量"}}

示例（平仓）：
{{"action": "close_long", "symbol": "SOLUSDT", "confidence": 0.85, "reasoning": "达到止盈目标"}}

示例（部分平仓）：
{{"action": "close_short", "symbol": "ETHUSDT", "close_quantity_pct": 0.4, "confidence": 0.70, "reasoning": "阶段目标达成，降低风险敞口"}}

**必填字段：**
- action：open_long、open_short、close_long、close_short、hold、wait
- symbol：交易品种（例如 "BTCUSDT"）
- confidence：决策信心（0.0 到 1.0，1.0 = 100%）
- reasoning：简要说明，需包含市场结构与信号确认
- 开仓时需额外包含：leverage、position_size_usd、stop_loss、take_profit
- 平仓时可选包含：close_quantity（绝对数量）或 close_quantity_pct（0-1 或 0-100），两者都省略则默认全仓平仓

**做空特别提醒：**
- 在下跌趋势中必须主动考虑 open_short
- 做空止损价必须高于入场价
- 做空止盈价必须低于入场价
- 示例：入场 4000，stop_loss 4100，take_profit 3700

**信心等级指南：**
- 0.9-1.0：高度确定，信号全部对齐
- 0.7-0.9：信心较高，2-3 个信号一致且风险可控
- 0.5-0.7：信心中等，趋势明确且至少一个辅助信号支持
- 0.3-0.5：信心较低，仅在趋势非常清晰且风控到位时执行
- <0.3：不确定性高，倾向使用 "wait"

**提示：** 趋势明确且风险回报合理时，0.5-0.7 的信心即可执行交易。

**决策优先顺序：**
1. 判断市场结构
2. 确认趋势是否清晰（最关键）
3. 寻找至少一个辅助信号（RSI、MACD 或成交量）
4. 评估风险回报比（目标 ≥ 1:3，可接受 1:2）
5. 检查持仓限制与可用资金
6. 最终决定（开仓/平仓/观望）

**交易心态：**
- 保持主动，看到符合条件的机会就执行
- 不必等待所有信号完美重叠
- 趋势 + RSI 确认通常足以入场
- 宁愿执行经过评估的机会，也不要错失
- 趋势清晰时，0.5-0.7 的信心即可出手
"""
        else:
            base_prompt += """
**OUTPUT FORMAT:**
First, provide your chain of thought analysis. MUST include:
1. Market regime classification (uptrend/downtrend/ranging)
2. Multi-signal confirmation check (trend, momentum, MACD, volume)
3. Risk assessment
4. Decision rationale

Then, output a JSON array of decisions:

Examples:
LONG example:
{{"action": "open_long", "symbol": "BTCUSDT", "leverage": 5, "position_size_usd": 1000, "stop_loss": 94000, "take_profit": 98000, "confidence": 0.75, "reasoning": "Uptrend confirmed, RSI 58, MACD bullish, volume spike on breakout"}}

SHORT example (important - use this in downtrends!):
{{"action": "open_short", "symbol": "ETHUSDT", "leverage": 5, "position_size_usd": 800, "stop_loss": 4100, "take_profit": 3700, "confidence": 0.80, "reasoning": "Downtrend confirmed, RSI 42, MACD bearish, breakdown below support with volume"}}

Closing example:
{{"action": "close_long", "symbol": "SOLUSDT", "confidence": 0.85, "reasoning": "Take profit target reached"}}

Partial close example:
{{"action": "close_short", "symbol": "ETHUSDT", "close_quantity_pct": 0.4, "confidence": 0.70, "reasoning": "Reduce exposure after partial target hit"}}

**REQUIRED FIELDS:**
- action: open_long, open_short, close_long, close_short, hold, wait
- symbol: The trading pair (e.g., "BTCUSDT")
- confidence: Your confidence level in this decision (0.0 to 1.0, where 1.0 = 100% confident)
- reasoning: Brief explanation including market regime and signal confirmation
- For open positions: also include leverage, position_size_usd, stop_loss, take_profit
- For closing positions: optionally include close_quantity (absolute size) or close_quantity_pct (0-1 or 0-100) to execute a partial close; omit both to close the full position

**IMPORTANT - SHORT POSITIONS:**
- In downtrends, you should actively consider open_short actions
- Stop loss for shorts: price level ABOVE entry (if price goes up, you lose)
- Take profit for shorts: price level BELOW entry (if price goes down, you profit)
- Example: Entry at 4000, stop_loss at 4100 (max loss), take_profit at 3700 (profit target)

**CONFIDENCE GUIDELINES:**
- 0.9-1.0: Very strong conviction, clear technical signals, all dimensions aligned
- 0.7-0.9: High confidence, good setup with manageable risk, 2-3 signals confirming
- 0.5-0.7: Moderate confidence, reasonable opportunity, trend + one confirming signal
- 0.3-0.5: Lower confidence, but acceptable if trend is clear and risk is controlled
- Below 0.3: Very uncertain, consider "wait" instead

**Note:** You can trade with 0.5-0.7 confidence if the trend is clear and risk/reward is favorable. Don't wait for perfect setups.

**DECISION PRIORITY:**
1. First: Classify market regime
2. Second: Check if trend is clear (this is the most important)
3. Third: Look for at least one confirming signal (RSI, MACD, or volume)
4. Fourth: Evaluate risk/reward ratio (aim for >= 1:3, but 1:2 is acceptable)
5. Fifth: Check position limits and available balance
6. Sixth: Make decision (open/close/hold)

**Trading Attitude:**
- Be proactive: If you see a reasonable opportunity with clear trend, take it
- Don't wait for perfect alignment of all 4 signals
- Trend + RSI confirmation is often sufficient for entry
- Better to take a calculated risk than to miss opportunities
- You can trade with 0.5-0.7 confidence if trend is clear - don't wait for 0.8+
"""
        return base_prompt

    def _build_market_context(
        self,
        account: Dict,
        positions: List[Dict],
        market_data: Dict,
        performance: Dict,
        language: Optional[str] = None,
    ) -> str:
        """Build market context for AI."""
        lang = self._resolve_prompt_language(language)
        lines = []
        
        available_balance = account['available_balance']
        max_usage_pct = self.config["strategy"].get("max_account_usage_pct", 100)
        agent_max_balance = available_balance * (max_usage_pct / 100)
        total_balance = account['total_wallet_balance']
        unrealized = account['total_unrealized_profit']
        
        if lang == "zh":
            lines.append("**账户信息：**")
            lines.append(f"💰 可用于交易的资金：${agent_max_balance:.2f} ← 决策请使用该数值")
            if max_usage_pct < 100:
                lines.append(f"（多智能体模式下仅可使用可用资金的 {max_usage_pct}% ，当前可用金额约 ${available_balance:.2f}）")
            lines.append(f"总资产：${total_balance:.2f}")
            lines.append(f"未实现盈亏：${unrealized:+.2f}\n")
        else:
            lines.append("**Account:**")
        lines.append(f"💰 Available for Trading: ${agent_max_balance:.2f} ← USE THIS FOR DECISIONS")
        if max_usage_pct < 100:
            lines.append(f"(Limited to {max_usage_pct}% of ${available_balance:.2f} for multi-agent)")
            lines.append(f"Total Balance: ${total_balance:.2f}")
            lines.append(f"Unrealized P/L: ${unrealized:+.2f}\n")
        
        if performance["total_trades"] > 0:
            lines.append(self.performance.format_performance(performance, language=lang))
            lines.append("")
        
        if positions:
            if lang == "zh":
                lines.append("**当前持仓：**")
            else:
                lines.append("**Current Positions:**")
            for pos in positions:
                pnl_pct = (
                    (pos["mark_price"] - pos["entry_price"]) / pos["entry_price"] * 100
                    if pos["side"] == "long"
                    else (pos["entry_price"] - pos["mark_price"]) / pos["entry_price"] * 100
                )
                if lang == "zh":
                    side_label = "多" if pos["side"] == "long" else "空"
                    lines.append(
                        f"- {pos['symbol']} {side_label}单：入场 ${pos['entry_price']:.2f} | 当前 ${pos['mark_price']:.2f} | 浮动盈亏 {pnl_pct:+.2f}%"
                    )
                else:
                    lines.append(
                        f"- {pos['symbol']} {pos['side'].upper()}: Entry ${pos['entry_price']:.2f}, Current ${pos['mark_price']:.2f}, P/L {pnl_pct:+.2f}%"
                    )
            lines.append("")
        
        if lang == "zh":
            lines.append("**市场数据：**")
        else:
            lines.append("**Market Data:**")
        for symbol, data in market_data.items():
            lines.append(self.ta.format_market_data(symbol, data["3m"], data["4h"], language=lang))
            lines.append("")
        
        return "\n".join(lines)

    def _parse_decisions(self, decisions_json: str) -> List[Dict]:
        """Parse AI decisions from JSON string."""
        import json
        
        try:
            # Extract JSON array from response
            start = decisions_json.find("[")
            end = decisions_json.rfind("]") + 1
            
            if start == -1 or end == 0:
                logger.warning("No JSON array found in AI response")
                return []
            
            json_str = decisions_json[start:end]
            decisions = json.loads(json_str)
            
            return decisions
        except Exception as e:
            logger.error(f"Failed to parse decisions: {e}")
            return []

    async def _execute_decisions(self, decisions: List[Dict]):
        """Execute AI decisions."""
        for decision in decisions:
            action = decision.get("action")
            symbol = decision.get("symbol")
            
            try:
                if action == "open_long":
                    await self._execute_open_long(decision)
                elif action == "open_short":
                    await self._execute_open_short(decision)
                elif action == "close_long":
                    await self._execute_close(decision, "long")
                elif action == "close_short":
                    await self._execute_close(decision, "short")
                elif action in ["hold", "wait"]:
                    logger.info(f"{action.upper()}: {decision.get('reasoning', '')}")
            except Exception as e:
                logger.error(f"Failed to execute {action} for {symbol}: {e}")

    async def _execute_open_long(self, decision: Dict):
        """Execute open long order."""
        symbol = decision["symbol"]
        leverage = decision["leverage"]
        position_size_usd = decision["position_size_usd"]
        
        # Get current account state
        account = await self.dex.get_account_balance()
        positions = await self.dex.get_positions()
        available = account['available_balance']
        
        # Check single trade limit
        risk = self.config["strategy"]["risk_management"]
        if positions:
            # Already have positions, use conservative limit
            max_trade_pct = risk.get("max_single_trade_with_positions_pct", 30)
        else:
            # No positions, can be more aggressive
            max_trade_pct = risk.get("max_single_trade_pct", 50)
        
        max_trade_amount = available * (max_trade_pct / 100)
        
        if position_size_usd > max_trade_amount:
            logger.warning(
                f"⚠️ Requested ${position_size_usd:.2f} exceeds {max_trade_pct}% limit "
                f"(${max_trade_amount:.2f}). Reducing position size."
            )
            position_size_usd = max_trade_amount
        
        # Check total position limit
        total_margin_used = sum(
            abs(p.get('position_amt', 0)) * p.get('entry_price', 0) / p.get('leverage', 1)
            for p in positions
        )
        max_total_pct = risk.get("max_total_position_pct", 80)
        max_total_margin = account['total_wallet_balance'] * (max_total_pct / 100)
        
        if (total_margin_used + position_size_usd) > max_total_margin:
            remaining = max_total_margin - total_margin_used
            if remaining < 0.1:  # Less than $0.1 available
                logger.error(
                    f"❌ Total position limit reached: {total_margin_used:.2f}/"
                    f"{max_total_margin:.2f} ({max_total_pct}%). Skipping trade."
                )
                return
            logger.warning(
                f"⚠️ Total position limit: reducing from ${position_size_usd:.2f} "
                f"to ${remaining:.2f} to stay within {max_total_pct}% limit."
            )
            position_size_usd = remaining
        
        # Calculate quantity
        # position_size_usd is the margin we want to use
        # Contract value = margin × leverage
        # Quantity = contract value / price
        price = await self.dex.get_market_price(symbol)
        contract_value = position_size_usd * leverage
        quantity = contract_value / price
        
        # Validate minimum quantity
        if quantity < 0.001:
            logger.warning(f"Quantity too small ({quantity:.6f}), adjusting to minimum 0.001")
            quantity = 0.001
            
            # CRITICAL: After adjusting to minimum, recalculate actual margin needed
            # This might be MUCH higher than originally planned!
            min_contract_value = quantity * price
            min_margin_needed = min_contract_value / leverage
            
            logger.info(
                f"Minimum quantity adjustment impact: "
                f"planned margin=${position_size_usd:.2f}, "
                f"actual needed=${min_margin_needed:.2f}"
            )
            
            # Check if minimum order is affordable
            if min_margin_needed > available:
                logger.error(
                    f"❌ Minimum order (0.001) requires ${min_margin_needed:.2f} margin, "
                    f"but only ${available:.2f} available. Cannot trade {symbol}."
                )
                return
            
            # Check if minimum order exceeds our risk limits
            current_max_trade = max_trade_amount
            if min_margin_needed > current_max_trade:
                logger.error(
                    f"❌ Minimum order requires ${min_margin_needed:.2f}, "
                    f"exceeds single trade limit ${current_max_trade:.2f}. "
                    f"Coin price too high for current balance."
                )
                return
            
            # Update position_size_usd to actual required amount
            position_size_usd = min_margin_needed
        
        # IMPORTANT: Exchange will format quantity (e.g., 0.074 -> 0.07 due to step_size)
        # Add 5% safety buffer for rounding
        estimated_formatted_qty = round(quantity * 0.95, 3)
        
        # Calculate actual margin needed (with buffer)
        actual_contract_value = estimated_formatted_qty * price
        required_margin = actual_contract_value / leverage
        
        # Final validation: Do we have enough balance?
        if required_margin > available:
            logger.error(
                f"❌ Final check: need ${required_margin:.2f} margin (after formatting), "
                f"but only ${available:.2f} available. Skipping trade."
            )
            return
        
        logger.info(
            f"Opening LONG {symbol}: margin=${position_size_usd:.2f}, leverage={leverage}x, "
            f"quantity={quantity:.6f} (estimated formatted: {estimated_formatted_qty:.6f})"
        )
        
        # Execute
        result = await self.dex.open_long(symbol, quantity, leverage)
        
        # Record
        self.logger_module.record_open_position(
            symbol=symbol,
            side="long",
            entry_price=price,
            quantity=quantity,
            leverage=leverage,
        )

        await self._maybe_place_protective_orders(
            symbol=symbol,
            side="long",
            order_result=result,
            fallback_quantity=quantity,
            fallback_price=price,
        )
        
        logger.info(f"✅ Opened LONG {symbol}: {quantity:.6f} @ {leverage}x")

    async def _execute_open_short(self, decision: Dict):
        """Execute open short order."""
        symbol = decision["symbol"]
        leverage = decision["leverage"]
        position_size_usd = decision["position_size_usd"]
        
        # Get current account state
        account = await self.dex.get_account_balance()
        positions = await self.dex.get_positions()
        available = account['available_balance']
        
        # Check single trade limit
        risk = self.config["strategy"]["risk_management"]
        if positions:
            # Already have positions, use conservative limit
            max_trade_pct = risk.get("max_single_trade_with_positions_pct", 30)
        else:
            # No positions, can be more aggressive
            max_trade_pct = risk.get("max_single_trade_pct", 50)
        
        max_trade_amount = available * (max_trade_pct / 100)
        
        if position_size_usd > max_trade_amount:
            logger.warning(
                f"⚠️ Requested ${position_size_usd:.2f} exceeds {max_trade_pct}% limit "
                f"(${max_trade_amount:.2f}). Reducing position size."
            )
            position_size_usd = max_trade_amount
        
        # Check total position limit
        total_margin_used = sum(
            abs(p.get('position_amt', 0)) * p.get('entry_price', 0) / p.get('leverage', 1)
            for p in positions
        )
        max_total_pct = risk.get("max_total_position_pct", 80)
        max_total_margin = account['total_wallet_balance'] * (max_total_pct / 100)
        
        if (total_margin_used + position_size_usd) > max_total_margin:
            remaining = max_total_margin - total_margin_used
            if remaining < 0.1:  # Less than $0.1 available
                logger.error(
                    f"❌ Total position limit reached: {total_margin_used:.2f}/"
                    f"{max_total_margin:.2f} ({max_total_pct}%). Skipping trade."
                )
                return
            logger.warning(
                f"⚠️ Total position limit: reducing from ${position_size_usd:.2f} "
                f"to ${remaining:.2f} to stay within {max_total_pct}% limit."
            )
            position_size_usd = remaining
        
        # Calculate quantity
        price = await self.dex.get_market_price(symbol)
        contract_value = position_size_usd * leverage
        quantity = contract_value / price
        
        # Validate minimum quantity
        if quantity < 0.001:
            logger.warning(f"Quantity too small ({quantity:.6f}), adjusting to minimum 0.001")
            quantity = 0.001
            
            # CRITICAL: After adjusting to minimum, recalculate actual margin needed
            # This might be MUCH higher than originally planned!
            min_contract_value = quantity * price
            min_margin_needed = min_contract_value / leverage
            
            logger.info(
                f"Minimum quantity adjustment impact: "
                f"planned margin=${position_size_usd:.2f}, "
                f"actual needed=${min_margin_needed:.2f}"
            )
            
            # Check if minimum order is affordable
            if min_margin_needed > available:
                logger.error(
                    f"❌ Minimum order (0.001) requires ${min_margin_needed:.2f} margin, "
                    f"but only ${available:.2f} available. Cannot trade {symbol}."
                )
                return
            
            # Check if minimum order exceeds our risk limits
            current_max_trade = max_trade_amount
            if min_margin_needed > current_max_trade:
                logger.error(
                    f"❌ Minimum order requires ${min_margin_needed:.2f}, "
                    f"exceeds single trade limit ${current_max_trade:.2f}. "
                    f"Coin price too high for current balance."
                )
                return
            
            # Update position_size_usd to actual required amount
            position_size_usd = min_margin_needed
        
        # IMPORTANT: Exchange will format quantity (e.g., 0.074 -> 0.07 due to step_size)
        # Add 5% safety buffer for rounding
        estimated_formatted_qty = round(quantity * 0.95, 3)
        
        # Calculate actual margin needed (with buffer)
        actual_contract_value = estimated_formatted_qty * price
        required_margin = actual_contract_value / leverage
        
        # Final validation: Do we have enough balance?
        if required_margin > available:
            logger.error(
                f"❌ Final check: need ${required_margin:.2f} margin (after formatting), "
                f"but only ${available:.2f} available. Skipping trade."
            )
            return
        
        logger.info(
            f"Opening SHORT {symbol}: margin=${position_size_usd:.2f}, leverage={leverage}x, "
            f"quantity={quantity:.6f} (estimated formatted: {estimated_formatted_qty:.6f})"
        )
        
        result = await self.dex.open_short(symbol, quantity, leverage)
        
        self.logger_module.record_open_position(
            symbol=symbol,
            side="short",
            entry_price=price,
            quantity=quantity,
            leverage=leverage,
        )

        await self._maybe_place_protective_orders(
            symbol=symbol,
            side="short",
            order_result=result,
            fallback_quantity=quantity,
            fallback_price=price,
        )
        
        logger.info(f"✅ Opened SHORT {symbol}: {quantity:.6f} @ {leverage}x")

    async def _execute_close(self, decision: Dict, side: str):
        """Execute close position (supports partial close)."""
        symbol = decision["symbol"]
        price = await self.dex.get_market_price(symbol)
        positions = await self.dex.get_positions()
        position = next((p for p in positions if p["symbol"] == symbol and p["side"] == side), None)
        if not position:
            logger.error(f"No {side} position found for {symbol} to close")
            return

        position_amt = position["position_amt"]

        close_quantity = None
        if "close_quantity" in decision:
            try:
                close_quantity = float(decision["close_quantity"])
            except (TypeError, ValueError):
                logger.warning("Invalid close_quantity provided; defaulting to full close")
                close_quantity = None
        elif "close_quantity_pct" in decision:
            try:
                pct = float(decision["close_quantity_pct"])
                if pct <= 0:
                    close_quantity = None
                else:
                    if pct > 1:
                        pct = pct / 100.0
                    close_quantity = position_amt * min(pct, 1.0)
            except (TypeError, ValueError):
                logger.warning("Invalid close_quantity_pct provided; defaulting to full close")
                close_quantity = None

        if close_quantity is not None:
            close_quantity = min(position_amt, max(0.0, close_quantity))
            if close_quantity <= 1e-12:
                logger.warning("Computed close quantity too small; skipping close action")
                return
        
        result = await self.dex.close_position(symbol, side, quantity=close_quantity)
        closed_quantity = result.get("closed_quantity") if isinstance(result, dict) else None
        if closed_quantity is None:
            closed_quantity = close_quantity if close_quantity is not None else position_amt
        
        fully_closed = result.get("fully_closed") if isinstance(result, dict) else None
        if fully_closed is None:
            fully_closed = abs(closed_quantity - position_amt) < 1e-9
        
        # Record close
        self.logger_module.record_close_position(symbol, side, price, closed_quantity)
        
        # If partial close and automatic TP/SL is enabled, we can place new TP/SL orders(current version does not re-place)
        
        action_label = "partial close" if not fully_closed else "full close"
        logger.info(f"✅ {action_label} {side.upper()} {symbol}: quantity={closed_quantity:.6f}")

    async def _maybe_place_protective_orders(
        self,
        symbol: str,
        side: str,
        order_result: Dict,
        fallback_quantity: float,
        fallback_price: float,
    ) -> None:
        """Conditionally place take-profit / stop-loss orders after opening a position."""
        if not self.advanced_orders:
            return

        tp_enabled = self.advanced_orders.get("enable_take_profit", False)
        sl_enabled = self.advanced_orders.get("enable_stop_loss", False)

        take_profit_pct = self.advanced_orders.get("take_profit_pct") if tp_enabled else None
        stop_loss_pct = self.advanced_orders.get("stop_loss_pct") if sl_enabled else None

        if take_profit_pct in (None, 0) and stop_loss_pct in (None, 0):
            return

        # Parse executed quantity and entry price from order result
        quantity = fallback_quantity
        entry_price = fallback_price

        try:
            quantity_str = order_result.get("quantity") if order_result else None
            price_str = order_result.get("price") if order_result else None

            if quantity_str is not None:
                quantity = float(quantity_str)
            if price_str is not None:
                entry_price = float(price_str)
        except (TypeError, ValueError):
            logger.debug("Unable to parse quantity/price from order result; using fallback values")

        try:
            await self.dex.place_take_profit_stop_loss(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                take_profit_pct=take_profit_pct,
                stop_loss_pct=stop_loss_pct,
            )
        except Exception as exc:  # pragma: no cover - runtime safety
            logger.error(f"Failed to place protective orders for {symbol}: {exc}")

    def get_status(self) -> Dict:
        """Get agent status for API."""
        exchange_cfg = self.config.get("exchange", {})
        llm_cfg = self.config.get("llm", {})
        
        return {
            "agent_id": self.agent_id,
            "name": self.config["agent"]["name"],
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "runtime_minutes": int((datetime.now() - self.start_time).total_seconds() / 60),
            # Multi-DEX support fields
            "dex_type": exchange_cfg.get("type", "aster"),
            "account_id": exchange_cfg.get("account_id") or exchange_cfg.get("user"),
            "model_id": llm_cfg.get("model"),
            "model_provider": llm_cfg.get("provider"),
        }

    def get_account_snapshot(self) -> Dict:
        """Return the most recent account snapshot with adjustments."""
        snapshot = dict(self.last_account_snapshot) if self.last_account_snapshot else {}
        if snapshot:
            # Add initial_balance if not present
            if "initial_balance" not in snapshot:
                snapshot["initial_balance"] = self.config.get("strategy", {}).get("initial_balance", 10000.0)
        return snapshot

