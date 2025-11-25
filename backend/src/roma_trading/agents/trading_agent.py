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
from typing import Any, Dict, List, Optional
from datetime import datetime
import dspy
from loguru import logger

from roma_trading.toolkits import AsterToolkit, TechnicalAnalysisToolkit
from roma_trading.core import DecisionLogger, PerformanceAnalyzer
from roma_trading.prompts import render_prompt

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
        
        prompt_context = {
            "max_positions": risk["max_positions"],
            "max_leverage": risk["max_leverage"],
            "max_position_size_pct": risk["max_position_size_pct"],
            "max_total_position_pct": risk.get("max_total_position_pct", 80),
            "max_single_trade_pct": risk.get("max_single_trade_pct", 50),
            "max_single_trade_with_positions_pct": risk.get("max_single_trade_with_positions_pct", 30),
            "stop_loss_pct": risk["stop_loss_pct"],
            "take_profit_pct": risk["take_profit_pct"],
            "CUSTOM_SECTIONS": "",
        }

        # Build custom sections if enabled
        custom_sections_text = ""
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
                custom_sections_text = "\n".join(custom_sections)

        prompt_context["CUSTOM_SECTIONS"] = custom_sections_text or ""

        base_prompt = render_prompt(
            "system",
            lang,
            context=prompt_context,
        )

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

    async def _execute_close(self, decision: Dict, side: str) -> Optional[Dict[str, Any]]:
        """Execute close position (supports partial close)."""
        symbol = str(decision["symbol"]).upper()
        normalized_side = side.lower()
        price = await self.dex.get_market_price(symbol)
        positions = await self.dex.get_positions()
        position = next(
            (p for p in positions if p["symbol"].upper() == symbol and p["side"] == normalized_side),
            None,
        )
        if not position:
            logger.error(f"No {normalized_side} position found for {symbol} to close")
            return None

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
            # Ensure close_quantity is positive and not greater than position_amt
            close_quantity = abs(close_quantity)  # Ensure positive
            close_quantity = min(position_amt, max(0.0, close_quantity))
            if close_quantity <= 1e-12:
                logger.warning("Computed close quantity too small; skipping close action")
                return
        
        # Final validation before calling DEX
        if close_quantity is not None and close_quantity <= 0:
            logger.warning(f"Invalid close quantity {close_quantity} for {symbol} {side}; skipping")
            return
        
        result = await self.dex.close_position(symbol, normalized_side, quantity=close_quantity)
        closed_quantity = result.get("closed_quantity") if isinstance(result, dict) else None
        if closed_quantity is None:
            closed_quantity = close_quantity if close_quantity is not None else position_amt
        
        fully_closed = result.get("fully_closed") if isinstance(result, dict) else None
        if fully_closed is None:
            fully_closed = abs(closed_quantity - position_amt) < 1e-9
        
        # Record close
        self.logger_module.record_close_position(symbol, normalized_side, price, closed_quantity)
        
        # If partial close and automatic TP/SL is enabled, we can place new TP/SL orders(current version does not re-place)
        
        action_label = "partial close" if not fully_closed else "full close"
        logger.info(f"✅ {action_label} {normalized_side.upper()} {symbol}: quantity={closed_quantity:.6f}")

        return {
            "symbol": symbol,
            "side": normalized_side,
            "closed_quantity": closed_quantity,
            "fully_closed": fully_closed,
            "price": price,
        }

    async def close_position_manual(
        self,
        symbol: str,
        side: str,
        quantity: Optional[float] = None,
        quantity_pct: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Close a position manually via admin controls.

        Args:
            symbol: Trading pair symbol, e.g., BTCUSDT
            side: long/short
            quantity: Optional absolute quantity to close
            quantity_pct: Optional percentage (0-1 or 0-100) of position to close
        """
        decision: Dict[str, Any] = {"symbol": symbol}
        if quantity is not None:
            decision["close_quantity"] = quantity
        if quantity_pct is not None:
            decision["close_quantity_pct"] = quantity_pct

        async with self.trading_lock:
            return await self._execute_close(decision, side)

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

