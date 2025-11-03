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
from roma_trading.core import DecisionLogger, PerformanceAnalyzer


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
        
        # Initialize DEX toolkit
        self.dex = AsterToolkit(
            user=config["exchange"]["user"],
            signer=config["exchange"]["signer"],
            private_key=config["exchange"]["private_key"],
            hedge_mode=config["exchange"].get("hedge_mode", False),
        )
        
        # Initialize technical analysis
        self.ta = TechnicalAnalysisToolkit()
        
        # Initialize decision logger
        self.logger_module = DecisionLogger(agent_id)
        
        # Initialize performance analyzer
        self.performance = PerformanceAnalyzer()
        
        # Initialize DSPy LLM
        self._init_llm()
        
        # Decision module
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
            # Qwen API (Alibaba Cloud)
            lm = dspy.LM(
                f"qwen/{model}" if model else "qwen/qwen-max",
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
        
        dspy.configure(lm=lm)
        logger.info(f"Configured DSPy with {provider}")

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
            system_prompt = self._build_system_prompt()
            market_context = self._build_market_context(account, positions, market_data, performance_metrics)
            
            # 6. AI Decision
            logger.info("Calling AI for decision...")
            result = self.decision_module(
                system_prompt=system_prompt,
                market_context=market_context
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

    def _build_system_prompt(self) -> str:
        """Build system prompt with trading rules and optional custom prompts."""
        risk = self.config["strategy"]["risk_management"]
        
        # Base system prompt (core rules only)
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
"""
        
        # Add custom prompts if enabled
        custom_prompts = self.config["strategy"].get("custom_prompts", {})
        
        if custom_prompts.get("enabled", False):
            custom_sections = []
            
            if custom_prompts.get("trading_philosophy"):
                custom_sections.append(f"""
**YOUR TRADING PHILOSOPHY:**
{custom_prompts['trading_philosophy']}
""")
            
            if custom_prompts.get("entry_preferences"):
                custom_sections.append(f"""
**YOUR ENTRY PREFERENCES:**
{custom_prompts['entry_preferences']}
""")
            
            if custom_prompts.get("position_management"):
                custom_sections.append(f"""
**YOUR POSITION MANAGEMENT:**
{custom_prompts['position_management']}
""")
            
            if custom_prompts.get("market_preferences"):
                custom_sections.append(f"""
**YOUR MARKET PREFERENCES:**
{custom_prompts['market_preferences']}
""")
            
            if custom_prompts.get("additional_rules"):
                custom_sections.append(f"""
**YOUR ADDITIONAL RULES:**
{custom_prompts['additional_rules']}
""")
            
            if custom_sections:
                base_prompt += "\n" + "\n".join(custom_sections)
        
        # Output format
        base_prompt += """
**OUTPUT FORMAT:**
First, provide your chain of thought analysis.
Then, output a JSON array of decisions:

[
  {{"action": "open_long", "symbol": "BTCUSDT", "leverage": 5, "position_size_usd": 1000, "stop_loss": 94000, "take_profit": 98000, "confidence": 0.75, "reasoning": "..."}},
  {{"action": "close_long", "symbol": "ETHUSDT", "confidence": 0.85, "reasoning": "Take profit"}}
]

**REQUIRED FIELDS:**
- action: open_long, open_short, close_long, close_short, hold, wait
- symbol: The trading pair (e.g., "BTCUSDT")
- confidence: Your confidence level in this decision (0.0 to 1.0, where 1.0 = 100% confident)
- reasoning: Brief explanation of why this decision
- For open positions: also include leverage, position_size_usd, stop_loss, take_profit

**CONFIDENCE GUIDELINES:**
- 0.9-1.0: Very strong conviction, clear technical/fundamental signals
- 0.7-0.9: High confidence, good setup with manageable risk
- 0.5-0.7: Moderate confidence, reasonable opportunity but uncertain
- 0.3-0.5: Low confidence, exploratory or defensive action
- Below 0.3: Very uncertain, consider "wait" instead
"""
        return base_prompt

    def _build_market_context(
        self, account: Dict, positions: List[Dict], market_data: Dict, performance: Dict
    ) -> str:
        """Build market context for AI."""
        lines = []
        
        # Calculate agent's usable balance (for multi-agent scenarios)
        available_balance = account['available_balance']
        max_usage_pct = self.config["strategy"].get("max_account_usage_pct", 100)
        agent_max_balance = available_balance * (max_usage_pct / 100)
        
        # Account info - emphasize available balance
        lines.append(f"**Account:**")
        lines.append(f"💰 Available for Trading: ${agent_max_balance:.2f} ← USE THIS FOR DECISIONS")
        if max_usage_pct < 100:
            lines.append(f"(Limited to {max_usage_pct}% of ${available_balance:.2f} for multi-agent)")
        lines.append(f"Total Balance: ${account['total_wallet_balance']:.2f}")
        lines.append(f"Unrealized P/L: ${account['total_unrealized_profit']:+.2f}\n")
        
        # Performance
        if performance["total_trades"] > 0:
            lines.append(self.performance.format_performance(performance))
            lines.append("")
        
        # Current positions
        if positions:
            lines.append("**Current Positions:**")
            for pos in positions:
                pnl_pct = ((pos["mark_price"] - pos["entry_price"]) / pos["entry_price"] * 100) if pos["side"] == "long" else ((pos["entry_price"] - pos["mark_price"]) / pos["entry_price"] * 100)
                lines.append(f"- {pos['symbol']} {pos['side'].upper()}: Entry ${pos['entry_price']:.2f}, Current ${pos['mark_price']:.2f}, P/L {pnl_pct:+.2f}%")
            lines.append("")
        
        # Market data
        lines.append("**Market Data:**")
        for symbol, data in market_data.items():
            lines.append(self.ta.format_market_data(symbol, data["3m"], data["4h"]))
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
                    await self._execute_close(symbol, "long")
                elif action == "close_short":
                    await self._execute_close(symbol, "short")
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
        
        logger.info(f"✅ Opened SHORT {symbol}: {quantity:.6f} @ {leverage}x")

    async def _execute_close(self, symbol: str, side: str):
        """Execute close position."""
        price = await self.dex.get_market_price(symbol)
        
        result = await self.dex.close_position(symbol, side)
        
        # Record close
        self.logger_module.record_close_position(symbol, side, price)
        
        logger.info(f"✅ Closed {side.upper()} {symbol}")

    def get_status(self) -> Dict:
        """Get agent status for API."""
        return {
            "agent_id": self.agent_id,
            "name": self.config["agent"]["name"],
            "is_running": self.is_running,
            "cycle_count": self.cycle_count,
            "runtime_minutes": int((datetime.now() - self.start_time).total_seconds() / 60),
        }

