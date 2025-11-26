"""
Trade History Analysis & Self-Optimization System

Analyzes trading history using AI to generate actionable insights
that improve future trading decisions.
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import yaml

from loguru import logger


class InsightCategory(str, Enum):
    """Categories of trading insights."""
    ENTRY_TIMING = "entry_timing"
    EXIT_TIMING = "exit_timing"
    POSITION_SIZING = "position_sizing"
    RISK_MANAGEMENT = "risk_management"
    MARKET_CONDITIONS = "market_conditions"
    LEVERAGE_USAGE = "leverage_usage"


@dataclass
class TradeHistory:
    """Enhanced trade history record with analysis context."""
    trade_id: str
    agent_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    quantity: float
    leverage: int
    pnl_usdt: float
    pnl_pct: float
    commission: float
    
    # Market conditions at entry
    entry_market_data: Dict[str, Any]
    entry_decision_reasoning: str
    
    # Market conditions at exit
    exit_market_data: Optional[Dict[str, Any]]
    exit_decision_reasoning: Optional[str]
    
    # Performance metrics
    holding_period_minutes: int
    max_favorable_excursion: Optional[float] = None
    max_adverse_excursion: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["entry_time"] = self.entry_time.isoformat()
        result["exit_time"] = self.exit_time.isoformat()
        return result


@dataclass
class AnalysisInsight:
    """Analysis insight extracted from trade history."""
    insight_id: str
    agent_id: Optional[str]  # None for global insights
    analysis_period_start: datetime
    analysis_period_end: datetime
    created_at: datetime
    
    # Insight content
    category: InsightCategory
    title: str
    summary: str
    detailed_findings: str
    recommendations: List[str]
    confidence_score: float  # 0.0 - 1.0
    
    # Supporting evidence
    supporting_trade_ids: List[str]
    trade_count: int
    
    # Validation
    times_applied: int = 0
    effectiveness_score: Optional[float] = None
    is_active: bool = True
    deprecated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["category"] = self.category.value
        result["analysis_period_start"] = self.analysis_period_start.isoformat()
        result["analysis_period_end"] = self.analysis_period_end.isoformat()
        result["created_at"] = self.created_at.isoformat()
        if self.deprecated_at:
            result["deprecated_at"] = self.deprecated_at.isoformat()
        return result


@dataclass
class AnalysisSnapshot:
    """Snapshot of analysis state for incremental analysis."""
    snapshot_id: str
    agent_id: Optional[str]
    created_at: datetime
    analysis_period_start: datetime
    analysis_period_end: datetime
    
    # Trade data summary
    total_trades: int
    analyzed_trade_ids: List[str]
    last_trade_timestamp: datetime
    
    # Analysis results summary
    insights_generated: int
    insight_ids: List[str]
    
    # Statistics
    win_rate: float
    profit_factor: float
    avg_pnl: float
    total_pnl: float
    
    # State for incremental analysis
    snapshot_state: Dict[str, Any]
    
    # Metadata
    job_id: str
    is_latest: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["created_at"] = self.created_at.isoformat()
        result["analysis_period_start"] = self.analysis_period_start.isoformat()
        result["analysis_period_end"] = self.analysis_period_end.isoformat()
        result["last_trade_timestamp"] = self.last_trade_timestamp.isoformat()
        return result


@dataclass
class AnalysisJob:
    """Analysis job metadata."""
    job_id: str
    agent_id: Optional[str]
    status: str  # "pending" | "running" | "completed" | "failed"
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Configuration
    analysis_period_days: int = 30
    min_trades_required: int = 10
    
    # Results
    trades_analyzed: int = 0
    insights_generated: int = 0
    insight_ids: List[str] = None
    
    # Snapshot reference
    snapshot_id: Optional[str] = None
    
    def __post_init__(self):
        if self.insight_ids is None:
            self.insight_ids = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["scheduled_at"] = self.scheduled_at.isoformat()
        if self.started_at:
            result["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()
        return result


class TradeHistoryCollector:
    """Collects and enriches trade history from DecisionLogger."""
    
    def __init__(self, log_dir: str = "logs/decisions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_trades(
        self,
        agent_id: str,
        start_date: datetime,
        end_date: datetime,
        decision_logger: Any,  # DecisionLogger instance
    ) -> List[TradeHistory]:
        """
        Collect and enrich trades from DecisionLogger.
        
        Args:
            agent_id: Agent identifier
            start_date: Start of analysis period
            end_date: End of analysis period
            decision_logger: DecisionLogger instance
            
        Returns:
            List of enriched trade history records
        """
        # Get raw trades from DecisionLogger
        all_trades = decision_logger.get_trade_history(limit=None)
        
        logger.debug(
            f"Total trades available: {len(all_trades)}, "
            f"filtering from {start_date.isoformat()} to {end_date.isoformat()}"
        )
        
        # Filter by date range
        # Use <= for start (inclusive) and < for end (exclusive) to avoid edge cases
        # But actually, we want to include trades that closed exactly at end_date
        filtered_trades = []
        for trade in all_trades:
            try:
                close_time_str = trade.get("close_time", "")
                if not close_time_str:
                    logger.warning(f"Trade missing close_time: {trade.get('symbol', 'unknown')}")
                    continue
                
                close_time = datetime.fromisoformat(close_time_str)
                # Include trades that closed between start_date (inclusive) and end_date (inclusive)
                # Add 1 second buffer to end_date to include trades closed exactly at end_date
                if start_date <= close_time <= (end_date + timedelta(seconds=1)):
                    filtered_trades.append(trade)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse trade close_time: {e}, trade: {trade.get('symbol', 'unknown')}")
                continue
        
        logger.debug(f"Filtered to {len(filtered_trades)} trades in date range")
        
        # Enrich with decision context from decision logs
        enriched_trades = []
        decision_logs = self._load_decision_logs(agent_id, start_date, end_date)
        
        logger.debug(f"Loaded {len(decision_logs)} decision logs for enrichment")
        
        enrichment_failures = 0
        for trade in filtered_trades:
            enriched = self._enrich_trade(trade, decision_logs, agent_id)
            if enriched:
                enriched_trades.append(enriched)
            else:
                enrichment_failures += 1
        
        if enrichment_failures > 0:
            logger.warning(
                f"Failed to enrich {enrichment_failures} out of {len(filtered_trades)} trades. "
                f"This may be normal if decision logs are missing."
            )
        
        logger.info(
            f"Collected {len(enriched_trades)} enriched trades for {agent_id} "
            f"(from {len(filtered_trades)} filtered trades) "
            f"from {start_date.date()} to {end_date.date()}"
        )
        
        return enriched_trades
    
    def _load_decision_logs(
        self,
        agent_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict]:
        """Load decision logs for the period."""
        agent_log_dir = self.log_dir / agent_id
        if not agent_log_dir.exists():
            return []
        
        logs = []
        for log_file in agent_log_dir.glob("decision_*.json"):
            try:
                with open(log_file, "r") as f:
                    log_data = json.load(f)
                log_time = datetime.fromisoformat(log_data.get("timestamp", ""))
                if start_date <= log_time <= end_date:
                    logs.append(log_data)
            except Exception as e:
                logger.warning(f"Failed to load decision log {log_file}: {e}")
        
        return sorted(logs, key=lambda x: x.get("timestamp", ""))
    
    def _enrich_trade(
        self,
        trade: Dict,
        decision_logs: List[Dict],
        agent_id: str,
    ) -> Optional[TradeHistory]:
        """Enrich trade with market data and decision context."""
        try:
            # Parse required fields
            entry_time = datetime.fromisoformat(trade.get("open_time", ""))
            exit_time = datetime.fromisoformat(trade.get("close_time", ""))
            holding_minutes = int((exit_time - entry_time).total_seconds() / 60)
            
            # Find decision log for entry
            entry_log = None
            for log in decision_logs:
                try:
                    log_time = datetime.fromisoformat(log.get("timestamp", ""))
                    # Find log closest to entry time
                    if abs((log_time - entry_time).total_seconds()) < 3600:  # Within 1 hour
                        entry_log = log
                        break
                except (ValueError, KeyError):
                    continue
            
            # Extract market data and reasoning from decision log
            entry_market_data = {}
            entry_reasoning = ""
            
            if entry_log:
                decisions = entry_log.get("decisions", [])
                for decision in decisions:
                    if decision.get("symbol") == trade.get("symbol"):
                        entry_reasoning = decision.get("reasoning", "")
                        break
                
                positions = entry_log.get("positions", [])
                for pos in positions:
                    if pos.get("symbol") == trade.get("symbol"):
                        entry_market_data = {
                            "mark_price": pos.get("mark_price"),
                            "leverage": pos.get("leverage"),
                        }
                        break
            
            return TradeHistory(
                trade_id=f"{agent_id}_{trade.get('symbol', 'unknown')}_{trade.get('open_time', '')}",
                agent_id=agent_id,
                symbol=trade.get("symbol", "UNKNOWN"),
                side=trade.get("side", "long"),
                entry_price=float(trade.get("entry_price", 0.0)),
                exit_price=float(trade.get("close_price", 0.0)),
                entry_time=entry_time,
                exit_time=exit_time,
                quantity=float(trade.get("quantity", 0.0)),
                leverage=int(trade.get("leverage", 1)),
                pnl_usdt=float(trade.get("pnl_usdt", 0.0)),
                pnl_pct=float(trade.get("pnl_pct", 0.0)),
                commission=float(trade.get("commission", 0.0)),
                entry_market_data=entry_market_data,
                entry_decision_reasoning=entry_reasoning,
                exit_market_data=None,
                exit_decision_reasoning=None,
                holding_period_minutes=holding_minutes,
            )
        except Exception as e:
            logger.warning(f"Failed to enrich trade {trade.get('symbol', 'unknown')}: {e}")
            logger.debug(f"Trade data: {trade}")
            return None


class SnapshotManager:
    """Manages analysis snapshots for incremental analysis."""
    
    def __init__(self, storage_dir: str = "logs/analysis_snapshots"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_snapshot(
        self,
        agent_id: Optional[str],
        analysis_job: AnalysisJob,
        trades: List[TradeHistory],
        insights: List[AnalysisInsight],
    ) -> str:
        """Create and save analysis snapshot."""
        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
        
        # Calculate statistics
        if trades:
            winning_trades = [t for t in trades if t.pnl_usdt > 0]
            win_rate = len(winning_trades) / len(trades) if trades else 0.0
            total_profit = sum(t.pnl_usdt for t in winning_trades)
            total_loss = abs(sum(t.pnl_usdt for t in trades if t.pnl_usdt < 0))
            profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")
            avg_pnl = sum(t.pnl_usdt for t in trades) / len(trades)
            total_pnl = sum(t.pnl_usdt for t in trades)
            last_trade_time = max(t.exit_time for t in trades)
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_pnl = 0.0
            total_pnl = 0.0
            last_trade_time = datetime.now()
        
        snapshot = AnalysisSnapshot(
            snapshot_id=snapshot_id,
            agent_id=agent_id,
            created_at=datetime.now(),
            analysis_period_start=analysis_job.scheduled_at - timedelta(days=analysis_job.analysis_period_days),
            analysis_period_end=analysis_job.scheduled_at,
            total_trades=len(trades),
            analyzed_trade_ids=[t.trade_id for t in trades],
            last_trade_timestamp=last_trade_time,
            insights_generated=len(insights),
            insight_ids=[ins.insight_id for ins in insights],
            win_rate=win_rate,
            profit_factor=profit_factor,
            avg_pnl=avg_pnl,
            total_pnl=total_pnl,
            snapshot_state={
                "trades_analyzed": len(trades),
                "insights_generated": len(insights),
            },
            job_id=analysis_job.job_id,
            is_latest=True,
        )
        
        # Mark previous snapshot as not latest
        await self._mark_previous_not_latest(agent_id)
        
        # Save snapshot
        await self._save_snapshot(snapshot)
        
        logger.info(f"Created snapshot {snapshot_id} for agent {agent_id or 'global'}")
        
        return snapshot_id
    
    async def get_latest_snapshot(self, agent_id: Optional[str]) -> Optional[AnalysisSnapshot]:
        """Get the latest snapshot for agent or global."""
        snapshot_file = self._get_snapshot_file(agent_id, latest=True)
        if snapshot_file.exists():
            return await self._load_snapshot(snapshot_file)
        return None
    
    async def get_trades_since_snapshot(
        self,
        snapshot: AnalysisSnapshot,
        decision_logger: Any,
    ) -> List[TradeHistory]:
        """Get trades that occurred after snapshot for incremental analysis."""
        collector = TradeHistoryCollector()
        
        # Get trades after snapshot period
        start_date = snapshot.analysis_period_end
        end_date = datetime.now()
        
        return await collector.collect_trades(
            snapshot.agent_id or "unknown",
            start_date,
            end_date,
            decision_logger,
        )
    
    def _get_snapshot_file(self, agent_id: Optional[str], latest: bool = False) -> Path:
        """Get snapshot file path."""
        if agent_id:
            agent_dir = self.storage_dir / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            if latest:
                return agent_dir / "latest_snapshot.json"
            return agent_dir
        else:
            global_dir = self.storage_dir / "global"
            global_dir.mkdir(parents=True, exist_ok=True)
            if latest:
                return global_dir / "latest_snapshot.json"
            return global_dir
    
    async def _save_snapshot(self, snapshot: AnalysisSnapshot) -> None:
        """Save snapshot to disk."""
        snapshot_file = self._get_snapshot_file(snapshot.agent_id, latest=True)
        with open(snapshot_file, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2)
    
    async def _load_snapshot(self, snapshot_file: Path) -> Optional[AnalysisSnapshot]:
        """Load snapshot from disk."""
        try:
            with open(snapshot_file, "r") as f:
                data = json.load(f)
            
            # Reconstruct datetime fields
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            data["analysis_period_start"] = datetime.fromisoformat(data["analysis_period_start"])
            data["analysis_period_end"] = datetime.fromisoformat(data["analysis_period_end"])
            data["last_trade_timestamp"] = datetime.fromisoformat(data["last_trade_timestamp"])
            
            # Reconstruct category enum
            if "category" in data:
                data["category"] = InsightCategory(data["category"])
            
            return AnalysisSnapshot(**{k: v for k, v in data.items() if k != "category"})
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_file}: {e}")
            return None
    
    async def _mark_previous_not_latest(self, agent_id: Optional[str]) -> None:
        """Mark previous snapshot as not latest."""
        # This is simplified - in production, you'd want to track all snapshots
        pass


class InsightRepository:
    """Stores and retrieves analysis insights."""
    
    def __init__(self, storage_dir: str = "logs/insights"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_insight(self, insight: AnalysisInsight) -> str:
        """Save insight and return insight_id."""
        agent_dir = self.storage_dir / (insight.agent_id or "global")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        insight_file = agent_dir / f"{insight.insight_id}.json"
        with open(insight_file, "w") as f:
            json.dump(insight.to_dict(), f, indent=2)
        
        logger.debug(f"Saved insight {insight.insight_id}")
        return insight.insight_id
    
    async def get_latest_insights(
        self,
        agent_id: Optional[str],
        limit: int = 10,
        min_confidence: float = 0.7,
    ) -> List[AnalysisInsight]:
        """Get most recent active insights."""
        agent_dir = self.storage_dir / (agent_id or "global")
        if not agent_dir.exists():
            return []
        
        insights = []
        for insight_file in agent_dir.glob("*.json"):
            try:
                with open(insight_file, "r") as f:
                    data = json.load(f)
                
                # Reconstruct datetime fields
                data["created_at"] = datetime.fromisoformat(data["created_at"])
                data["analysis_period_start"] = datetime.fromisoformat(data["analysis_period_start"])
                data["analysis_period_end"] = datetime.fromisoformat(data["analysis_period_end"])
                
                if data.get("deprecated_at"):
                    data["deprecated_at"] = datetime.fromisoformat(data["deprecated_at"])
                
                # Reconstruct category enum
                data["category"] = InsightCategory(data["category"])
                
                insight = AnalysisInsight(**data)
                
                if (
                    insight.is_active
                    and insight.confidence_score >= min_confidence
                ):
                    insights.append(insight)
            except Exception as e:
                logger.warning(f"Failed to load insight {insight_file}: {e}")
        
        # Sort by recency and confidence
        insights.sort(
            key=lambda x: (x.created_at, x.confidence_score),
            reverse=True
        )
        
        return insights[:limit]
    
    async def get_insights_by_category(
        self,
        agent_id: Optional[str],
        category: InsightCategory,
        limit: int = 10,
    ) -> List[AnalysisInsight]:
        """Get insights by category."""
        all_insights = await self.get_latest_insights(agent_id, limit=1000)
        filtered = [ins for ins in all_insights if ins.category == category]
        return filtered[:limit]


class AnalysisEngine:
    """AI-powered analysis engine for generating insights."""
    
    def __init__(self, agent_manager: Any = None, llm_provider: Any = None):
        self.agent_manager = agent_manager
        self.llm_provider = llm_provider
    
    def _get_llm(self, agent_id: Optional[str] = None):
        """Get LLM instance from agent or use default."""
        if agent_id and self.agent_manager:
            try:
                agent = self.agent_manager.get_agent(agent_id)
                return agent.lm
            except Exception as e:
                logger.warning(f"Could not get LLM from agent {agent_id}: {e}")
        
        # Fallback: use first available agent's LLM
        if self.agent_manager:
            agents = self.agent_manager.get_all_agents()
            if agents:
                try:
                    agent = self.agent_manager.get_agent(agents[0]["id"])
                    return agent.lm
                except Exception:
                    pass
        
        return None
    
    async def analyze_trades(
        self,
        trades: List[TradeHistory],
        agent_id: Optional[str],
        analysis_period_start: datetime,
        analysis_period_end: datetime,
        language: str = "en",
    ) -> List[AnalysisInsight]:
        """
        Analyze trades and generate insights using AI.
        """
        if not trades:
            return []
        
        # Calculate summary statistics
        winning_trades = [t for t in trades if t.pnl_usdt > 0]
        losing_trades = [t for t in trades if t.pnl_usdt < 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0.0
        
        total_profit = sum(t.pnl_usdt for t in winning_trades)
        total_loss = abs(sum(t.pnl_usdt for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")
        
        avg_pnl = sum(t.pnl_usdt for t in trades) / len(trades)
        
        # Format trade summary for LLM
        trade_summary = self._format_trade_summary(trades)
        
        # Normalize language (default to English)
        prompt_language = (language or "en").lower()
        if not prompt_language.startswith(("en", "zh")):
            prompt_language = "en"
        
        # Get LLM
        lm = self._get_llm(agent_id)
        if not lm:
            logger.warning("No LLM available for analysis, using rule-based insights")
            return self._generate_rule_based_insights(
                trades,
                agent_id,
                analysis_period_start,
                analysis_period_end,
                win_rate,
                profit_factor,
                avg_pnl,
                prompt_language,
            )
        
        # Generate analysis prompt
        from roma_trading.prompts import get_prompt_template
        
        try:
            # Get raw template (without formatting) to avoid KeyError
            prompt_template = get_prompt_template("trade_analysis", language=prompt_language)
        except ValueError:
            # Fallback if prompt not found
            prompt_template = self._get_fallback_prompt(prompt_language)
        
        # Replace placeholders manually
        analysis_prompt = prompt_template.replace("{TRADE_SUMMARY}", trade_summary)
        analysis_prompt = analysis_prompt.replace("{WIN_RATE}", f"{win_rate * 100:.1f}")
        analysis_prompt = analysis_prompt.replace("{PROFIT_FACTOR}", f"{profit_factor:.2f}")
        analysis_prompt = analysis_prompt.replace("{AVG_PNL}", f"{avg_pnl:.2f}")
        
        # Run LLM analysis
        try:
            logger.debug(f"Running LLM analysis with prompt length: {len(analysis_prompt)}")
            insights_json = await asyncio.to_thread(
                self._run_llm_analysis,
                lm,
                analysis_prompt
            )
            
            if not insights_json:
                logger.warning("LLM returned empty insights JSON, falling back to rule-based insights")
                return self._generate_rule_based_insights(
                    trades,
                    agent_id,
                    analysis_period_start,
                    analysis_period_end,
                    win_rate,
                    profit_factor,
                    avg_pnl,
                    prompt_language,
                )
            
            # Parse insights
            insights = self._parse_insights(
                insights_json,
                trades,
                agent_id,
                analysis_period_start,
                analysis_period_end,
            )
            
            # If parsing failed and no insights generated, fall back to rule-based
            if not insights:
                logger.warning("No insights parsed from LLM response, falling back to rule-based insights")
                return self._generate_rule_based_insights(
                    trades,
                    agent_id,
                    analysis_period_start,
                    analysis_period_end,
                    win_rate,
                    profit_factor,
                    avg_pnl,
                    prompt_language,
                )
            
            logger.info(f"Generated {len(insights)} insights from {len(trades)} trades")
            return insights
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            logger.info("Falling back to rule-based insights")
            # Fallback to rule-based
            return self._generate_rule_based_insights(
                trades,
                agent_id,
                analysis_period_start,
                analysis_period_end,
                win_rate,
                profit_factor,
                avg_pnl,
                prompt_language,
            )
    
    def _run_llm_analysis(self, lm: Any, prompt: str) -> str:
        """Run LLM analysis synchronously."""
        import dspy
        
        class AnalysisResponse(dspy.Signature):
            """LLM analysis response signature."""
            analysis_prompt: str = dspy.InputField(desc="Analysis instructions and trade data")
            insights_json: str = dspy.OutputField(desc="JSON object with insights array")
        
        with dspy.context(lm=lm):
            module = dspy.ChainOfThought(AnalysisResponse)
            result = module(analysis_prompt=prompt)
            return result.insights_json
    
    def _format_trade_summary(self, trades: List[TradeHistory]) -> str:
        """Format trades into summary text for LLM."""
        lines = []
        lines.append(f"Total Trades: {len(trades)}")
        lines.append(f"Analysis Period: {trades[0].entry_time.date()} to {trades[-1].exit_time.date()}")
        lines.append("")
        
        # Group by symbol
        by_symbol: Dict[str, List[TradeHistory]] = {}
        for trade in trades:
            if trade.symbol not in by_symbol:
                by_symbol[trade.symbol] = []
            by_symbol[trade.symbol].append(trade)
        
        for symbol, symbol_trades in by_symbol.items():
            lines.append(f"**{symbol}**:")
            wins = [t for t in symbol_trades if t.pnl_usdt > 0]
            losses = [t for t in symbol_trades if t.pnl_usdt < 0]
            lines.append(f"  - Total: {len(symbol_trades)} trades")
            lines.append(f"  - Wins: {len(wins)} ({len(wins)/len(symbol_trades)*100:.1f}%)")
            lines.append(f"  - Losses: {len(losses)} ({len(losses)/len(symbol_trades)*100:.1f}%)")
            if wins:
                avg_win = sum(t.pnl_usdt for t in wins) / len(wins)
                lines.append(f"  - Avg Win: ${avg_win:.2f}")
            if losses:
                avg_loss = sum(t.pnl_usdt for t in losses) / len(losses)
                lines.append(f"  - Avg Loss: ${avg_loss:.2f}")
            lines.append("")
        
        # Sample trades (winning and losing)
        lines.append("**Sample Winning Trades:**")
        winning_samples = sorted([t for t in trades if t.pnl_usdt > 0], key=lambda x: x.pnl_usdt, reverse=True)[:5]
        for trade in winning_samples:
            lines.append(
                f"  - {trade.symbol} {trade.side.upper()}: "
                f"Entry ${trade.entry_price:.2f}, Exit ${trade.exit_price:.2f}, "
                f"P&L ${trade.pnl_usdt:.2f} ({trade.pnl_pct:+.2f}%), "
                f"Held {trade.holding_period_minutes}min"
            )
        
        lines.append("")
        lines.append("**Sample Losing Trades:**")
        losing_samples = sorted([t for t in trades if t.pnl_usdt < 0], key=lambda x: x.pnl_usdt)[:5]
        for trade in losing_samples:
            lines.append(
                f"  - {trade.symbol} {trade.side.upper()}: "
                f"Entry ${trade.entry_price:.2f}, Exit ${trade.exit_price:.2f}, "
                f"P&L ${trade.pnl_usdt:.2f} ({trade.pnl_pct:+.2f}%), "
                f"Held {trade.holding_period_minutes}min"
            )
        
        return "\n".join(lines)
    
    def _parse_insights(
        self,
        insights_json: str,
        trades: List[TradeHistory],
        agent_id: Optional[str],
        analysis_period_start: datetime,
        analysis_period_end: datetime,
    ) -> List[AnalysisInsight]:
        """Parse insights from LLM JSON response."""
        import json
        import re
        
        insights = []
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            # Try multiple patterns to find JSON
            json_str = None
            
            # Pattern 1: Look for JSON code block
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', insights_json, re.DOTALL)
            if code_block_match:
                json_str = code_block_match.group(1)
            
            # Pattern 2: Look for JSON object with insights array
            if not json_str:
                json_match = re.search(r'\{[^{}]*"insights"[^{}]*\[.*?\]\s*\}', insights_json, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            # Pattern 3: Try to find any JSON object
            if not json_str:
                json_match = re.search(r'\{.*"insights".*\[.*?\].*?\}', insights_json, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
            
            # Fallback: use entire response
            if not json_str:
                json_str = insights_json.strip()
            
            # Clean up JSON string
            json_str = json_str.strip()
            # Remove markdown formatting if present
            json_str = re.sub(r'^```(?:json)?\s*', '', json_str)
            json_str = re.sub(r'\s*```$', '', json_str)
            
            # Try to parse
            data = None
            parse_attempts = [
                # Attempt 1: Direct parse
                lambda s: json.loads(s),
                # Attempt 2: Fix trailing commas
                lambda s: json.loads(re.sub(r',\s*}', '}', re.sub(r',\s*]', ']', s))),
                # Attempt 3: Fix single quotes
                lambda s: json.loads(s.replace("'", '"')),
                # Attempt 4: Fix both
                lambda s: json.loads(re.sub(r',\s*}', '}', re.sub(r',\s*]', ']', s.replace("'", '"')))),
                # Attempt 5: Try to extract just the insights array
                lambda s: {"insights": json.loads(re.search(r'\[.*?\]', s, re.DOTALL).group(0)) if re.search(r'\[.*?\]', s, re.DOTALL) else []},
            ]
            
            for i, attempt in enumerate(parse_attempts):
                try:
                    data = attempt(json_str)
                    if data:
                        logger.debug(f"Successfully parsed JSON on attempt {i+1}")
                        break
                except (json.JSONDecodeError, AttributeError) as e:
                    if i == len(parse_attempts) - 1:
                        logger.warning(f"All JSON parse attempts failed. Last error: {e}")
                        logger.debug(f"JSON string (first 1000 chars): {json_str[:1000]}")
                    continue
            
            if not data:
                logger.error("Could not parse JSON from LLM response")
                return []
            
            # Parse insights from data
            insights_list = data.get("insights", [])
            if not isinstance(insights_list, list):
                logger.warning("'insights' is not a list in JSON response")
                return []
            
            for insight_data in insights_list:
                try:
                    if not isinstance(insight_data, dict):
                        continue
                    
                    category_str = insight_data.get("category", "entry_timing")
                    try:
                        category = InsightCategory(category_str)
                    except ValueError:
                        logger.warning(f"Invalid category '{category_str}', using entry_timing")
                        category = InsightCategory.ENTRY_TIMING
                    
                    # Map trade IDs to actual trades
                    supporting_ids = insight_data.get("supporting_trade_ids", [])
                    if not isinstance(supporting_ids, list):
                        supporting_ids = []
                    
                    # If trade IDs are not in format, try to match by pattern
                    valid_ids = []
                    for trade in trades[:10]:  # Limit to first 10 for matching
                        if any(str(sid).lower() in trade.trade_id.lower() for sid in supporting_ids):
                            valid_ids.append(trade.trade_id)
                    
                    if not valid_ids and trades:
                        # Default to first few trades as examples
                        valid_ids = [t.trade_id for t in trades[:3]]
                    
                    # Ensure recommendations is a list
                    recommendations = insight_data.get("recommendations", [])
                    if not isinstance(recommendations, list):
                        recommendations = []
                    
                    insight = AnalysisInsight(
                        insight_id=f"ins_{uuid.uuid4().hex[:12]}",
                        agent_id=agent_id,
                        analysis_period_start=analysis_period_start,
                        analysis_period_end=analysis_period_end,
                        created_at=datetime.now(),
                        category=category,
                        title=str(insight_data.get("title", "Untitled Insight")),
                        summary=str(insight_data.get("summary", "")),
                        detailed_findings=str(insight_data.get("detailed_findings", "")),
                        recommendations=recommendations,
                        confidence_score=float(insight_data.get("confidence_score", 0.7)),
                        supporting_trade_ids=valid_ids,
                        trade_count=len(trades),
                    )
                    insights.append(insight)
                except Exception as e:
                    logger.warning(f"Failed to parse individual insight: {e}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Failed to parse insights JSON: {e}", exc_info=True)
            logger.debug(f"JSON string (first 1000 chars): {insights_json[:1000] if insights_json else 'None'}")
        
        return insights
    
    def _generate_rule_based_insights(
        self,
        trades: List[TradeHistory],
        agent_id: Optional[str],
        analysis_period_start: datetime,
        analysis_period_end: datetime,
        win_rate: float,
        profit_factor: float,
        avg_pnl: float,
        language: str = "en",
    ) -> List[AnalysisInsight]:
        """Generate rule-based insights as fallback."""
        insights = []
        
        winning_trades = [t for t in trades if t.pnl_usdt > 0]
        losing_trades = [t for t in trades if t.pnl_usdt < 0]
        
        is_zh = (language or "en").lower().startswith("zh")
        
        def t(en_text: str, zh_text: str) -> str:
            return zh_text if is_zh else en_text
        
        # Insight 1: Win rate analysis
        if win_rate > 0.6:
            insights.append(AnalysisInsight(
                insight_id=f"ins_{uuid.uuid4().hex[:12]}",
                agent_id=agent_id,
                analysis_period_start=analysis_period_start,
                analysis_period_end=analysis_period_end,
                created_at=datetime.now(),
                category=InsightCategory.ENTRY_TIMING,
                title=t("Strong Win Rate Maintained", "胜率表现稳健"),
                summary=t(
                    f"Win rate of {win_rate*100:.1f}% indicates effective entry timing",
                    f"胜率达到 {win_rate*100:.1f}% ，显示入场节奏有效"
                ),
                detailed_findings=t(
                    f"Analysis of {len(trades)} trades shows a {win_rate*100:.1f}% win rate, which is above average. Continue following current entry strategies.",
                    f"共分析 {len(trades)} 笔交易，胜率 {win_rate*100:.1f}% ，高于常规水平，说明现有入场规则有效，可继续保持。"
                ),
                recommendations=[
                    t("Maintain current entry criteria", "保持当前入场条件"),
                    t("Review winning trades for common patterns", "回顾盈利交易，提炼共同模式"),
                ],
                confidence_score=0.75,
                supporting_trade_ids=[t.trade_id for t in winning_trades[:5]],
                trade_count=len(trades),
            ))
        elif win_rate < 0.4:
            insights.append(AnalysisInsight(
                insight_id=f"ins_{uuid.uuid4().hex[:12]}",
                agent_id=agent_id,
                analysis_period_start=analysis_period_start,
                analysis_period_end=analysis_period_end,
                created_at=datetime.now(),
                category=InsightCategory.ENTRY_TIMING,
                title=t("Low Win Rate - Review Entry Criteria", "胜率较低，需重新评估入场条件"),
                summary=t(
                    f"Win rate of {win_rate*100:.1f}% suggests entry timing needs improvement",
                    f"当前胜率 {win_rate*100:.1f}% 偏低，需要优化入场策略"
                ),
                detailed_findings=t(
                    "Win rate is below 40%, indicating entry criteria may need adjustment. Review losing trades for common patterns.",
                    "胜率低于 40%，说明入场条件过于宽松或与行情不匹配，应重点回顾亏损交易寻找共性问题。"
                ),
                recommendations=[
                    t("Review and tighten entry criteria", "重新审视并收紧入场条件"),
                    t("Wait for stronger confirmation signals", "等待更强的多维确认信号"),
                    t("Analyze losing trades for common mistakes", "分析亏损交易定位常见错误"),
                ],
                confidence_score=0.8,
                supporting_trade_ids=[t.trade_id for t in losing_trades[:5]],
                trade_count=len(trades),
            ))
        
        # Insight 2: Profit factor analysis
        if profit_factor > 1.5:
            insights.append(AnalysisInsight(
                insight_id=f"ins_{uuid.uuid4().hex[:12]}",
                agent_id=agent_id,
                analysis_period_start=analysis_period_start,
                analysis_period_end=analysis_period_end,
                created_at=datetime.now(),
                category=InsightCategory.EXIT_TIMING,
                title=t("Strong Profit Factor", "盈亏比表现优秀"),
                summary=t(
                    f"Profit factor of {profit_factor:.2f} indicates good exit timing",
                    f"盈亏比 {profit_factor:.2f} 显示出场策略表现良好"
                ),
                detailed_findings=t(
                    f"Profit factor of {profit_factor:.2f} shows that profits significantly outweigh losses. This suggests effective position management.",
                    f"盈亏比 {profit_factor:.2f} 说明盈利远大于亏损，现有出场 / 仓位管理策略有效，可继续保持并适度放宽盈利空间。"
                ),
                recommendations=[
                    t("Continue current exit strategies", "保持当前出场策略"),
                    t("Consider letting winners run longer", "尝试让盈利单持有更久以延伸收益"),
                ],
                confidence_score=0.7,
                supporting_trade_ids=[t.trade_id for t in winning_trades[:5]],
                trade_count=len(trades),
            ))
        
        return insights
    
    def _get_fallback_prompt(self, language: str = "en") -> str:
        """Get fallback analysis prompt if template not found."""
        if (language or "en").lower().startswith("zh"):
            return """请分析以下交易历史，提取可执行的洞察，并以 JSON 格式返回。

交易数据：
{TRADE_SUMMARY}

胜率：{WIN_RATE}%
盈亏比：{PROFIT_FACTOR}
平均单笔盈亏：${AVG_PNL}

输出格式：
{{
  "insights": [
    {{
      "category": "entry_timing",
      "title": "洞察标题",
      "summary": "一句话摘要",
      "detailed_findings": "详细发现",
      "recommendations": ["建议1", "建议2"],
      "confidence_score": 0.8,
      "supporting_trade_ids": ["trade_id1", "trade_id2"]
    }}
  ]
}}
"""
        return """Analyze the following trade history and generate actionable insights in JSON format.

Trade Data:
{TRADE_SUMMARY}

Win Rate: {WIN_RATE}%
Profit Factor: {PROFIT_FACTOR}
Average P&L: ${AVG_PNL}

Provide insights in this format:
{{
  "insights": [
    {{
      "category": "entry_timing",
      "title": "Insight title",
      "summary": "Brief summary",
      "detailed_findings": "Detailed analysis",
      "recommendations": ["Recommendation 1", "Recommendation 2"],
      "confidence_score": 0.8,
      "supporting_trade_ids": ["trade_id1", "trade_id2"]
    }}
  ]
}}
"""


class TradeHistoryAnalyzer:
    """Main analyzer class that orchestrates all components."""
    
    def __init__(
        self,
        agent_manager: Any,
        storage_dir: str = "logs/analysis",
        llm_provider: Any = None,
    ):
        self.agent_manager = agent_manager
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.collector = TradeHistoryCollector()
        self.snapshot_manager = SnapshotManager(storage_dir=str(self.storage_dir / "snapshots"))
        self.insight_repo = InsightRepository(storage_dir=str(self.storage_dir / "insights"))
        self.analysis_engine = AnalysisEngine(agent_manager=agent_manager, llm_provider=llm_provider)
        self._system_prompt_language: Optional[str] = None
        
        # Job tracking
        self.jobs_file = self.storage_dir / "jobs.json"
        self.jobs: Dict[str, AnalysisJob] = {}
        self._load_jobs()
    
    def _load_jobs(self) -> None:
        """Load analysis jobs from disk."""
        if self.jobs_file.exists():
            try:
                with open(self.jobs_file, "r") as f:
                    jobs_data = json.load(f)
                    for job_data in jobs_data:
                        # Reconstruct datetime fields
                        job_data["scheduled_at"] = datetime.fromisoformat(job_data["scheduled_at"])
                        if job_data.get("started_at"):
                            job_data["started_at"] = datetime.fromisoformat(job_data["started_at"])
                        if job_data.get("completed_at"):
                            job_data["completed_at"] = datetime.fromisoformat(job_data["completed_at"])
                        
                        job = AnalysisJob(**job_data)
                        self.jobs[job.job_id] = job
            except Exception as e:
                logger.error(f"Failed to load analysis jobs: {e}")
    
    def _save_jobs(self) -> None:
        """Save analysis jobs to disk."""
        jobs_data = [job.to_dict() for job in self.jobs.values()]
        with open(self.jobs_file, "w") as f:
            json.dump(jobs_data, f, indent=2)
    
    async def run_analysis(
        self,
        agent_id: Optional[str] = None,
        analysis_period_days: int = 30,
        min_trades_required: int = 10,
        use_snapshot: bool = True,
    ) -> AnalysisJob:
        """
        Run analysis job for an agent or globally.
        
        Args:
            agent_id: Agent ID or None for global analysis
            analysis_period_days: Number of days to analyze
            min_trades_required: Minimum trades needed
            use_snapshot: Whether to use snapshot for incremental analysis
            
        Returns:
            AnalysisJob with results
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = AnalysisJob(
            job_id=job_id,
            agent_id=agent_id,
            status="running",
            scheduled_at=datetime.now(),
            started_at=datetime.now(),
            analysis_period_days=analysis_period_days,
            min_trades_required=min_trades_required,
        )
        
        self.jobs[job_id] = job
        self._save_jobs()
        
        try:
            # Get agent's DecisionLogger
            if agent_id:
                agent = self.agent_manager.get_agent(agent_id)
                decision_logger = agent.logger_module
                analysis_language = self._resolve_analysis_language(agent)
            else:
                # Global analysis - analyze all agents
                decision_logger = None  # Will need to aggregate
                analysis_language = self._resolve_analysis_language(None)
            
            if not decision_logger:
                raise ValueError(f"Agent {agent_id} not found or no decision logger available")
            
            # Determine analysis period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            # Check for snapshot
            snapshot = None
            if use_snapshot:
                snapshot = await self.snapshot_manager.get_latest_snapshot(agent_id)
                if snapshot:
                    # Use snapshot end time as start, but ensure we have a reasonable time range
                    snapshot_end = snapshot.analysis_period_end
                    # If snapshot is very recent (within last hour), use full period instead
                    time_since_snapshot = (end_date - snapshot_end).total_seconds() / 3600
                    if time_since_snapshot < 1.0:  # Less than 1 hour since snapshot
                        logger.info(
                            f"Snapshot is very recent ({time_since_snapshot:.1f} hours ago), "
                            f"using full analysis period instead"
                        )
                        start_date = end_date - timedelta(days=analysis_period_days)
                    else:
                        start_date = snapshot_end
                        job.snapshot_id = snapshot.snapshot_id
                        logger.info(
                            f"Using snapshot for incremental analysis: "
                            f"from {start_date.date()} to {end_date.date()}"
                        )
            
            # Collect trades
            trades = await self.collector.collect_trades(
                agent_id or "global",
                start_date,
                end_date,
                decision_logger,
            )
            
            logger.info(
                f"Collected {len(trades)} trades for analysis "
                f"(required: {min_trades_required}, period: {start_date.date()} to {end_date.date()})"
            )
            
            if len(trades) < min_trades_required:
                error_msg = (
                    f"Not enough trades for analysis: {len(trades)} < {min_trades_required}. "
                    f"Analysis period: {start_date.date()} to {end_date.date()}"
                )
                logger.warning(error_msg)
                raise ValueError(error_msg)
            
            job.trades_analyzed = len(trades)
            
            # Analyze trades
            insights = await self.analysis_engine.analyze_trades(
                trades,
                agent_id,
                start_date,
                end_date,
                language=analysis_language,
            )
            
            # Save insights
            insight_ids = []
            for insight in insights:
                await self.insight_repo.save_insight(insight)
                insight_ids.append(insight.insight_id)
            
            job.insights_generated = len(insights)
            job.insight_ids = insight_ids
            
            # Create snapshot
            snapshot_id = await self.snapshot_manager.create_snapshot(
                agent_id,
                job,
                trades,
                insights,
            )
            
            job.status = "completed"
            job.completed_at = datetime.now()
            
            logger.info(
                f"Analysis completed for {agent_id or 'global'}: "
                f"{len(insights)} insights generated from {len(trades)} trades"
            )
            
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Analysis failed for {agent_id or 'global'}: {e}", exc_info=True)
        
        self._save_jobs()
        return job
    
    def _resolve_analysis_language(self, agent: Optional[Any]) -> str:
        """
        Determine which language to use for analysis prompts based on configuration.
        Priority:
            1. Agent strategy prompt_language
            2. Agent default prompt language
            3. System prompt_language (from config)
            4. English fallback
        """
        lang: Optional[str] = None
        
        if agent:
            strategy = agent.config.get("strategy", {})
            lang = strategy.get("prompt_language") or getattr(agent, "default_prompt_language", None)
        
        if not lang:
            lang = self._get_system_prompt_language()
        
        if not lang:
            return "en"
        
        lang = str(lang).lower()
        if lang.startswith("zh"):
            return "zh"
        return "en"
    
    def _get_system_prompt_language(self) -> Optional[str]:
        """Load system prompt language from trading configuration if available."""
        if self._system_prompt_language:
            return self._system_prompt_language
        
        config_path = getattr(self.agent_manager, "config_path", None)
        if not config_path:
            return None
        
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            lang = config.get("system", {}).get("prompt_language")
            if lang:
                self._system_prompt_language = lang
                return lang
        except Exception as exc:
            logger.debug(f"Failed to load system prompt language: {exc}")
        
        return None
    
    async def get_analysis_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[AnalysisJob]:
        """Get analysis history for agent or global."""
        filtered_jobs = [
            job for job in self.jobs.values()
            if job.agent_id == agent_id
        ]
        
        # Sort by scheduled_at (most recent first)
        filtered_jobs.sort(key=lambda x: x.scheduled_at, reverse=True)
        
        return filtered_jobs[:limit]
    
    async def get_latest_insights(
        self,
        agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[AnalysisInsight]:
        """Get latest insights for agent or global."""
        return await self.insight_repo.get_latest_insights(agent_id, limit=limit)

