"""
Analysis Scheduler for Trade History Analysis

Manages scheduled analysis jobs with configurable intervals.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict
from loguru import logger

from .trade_history_analyzer import TradeHistoryAnalyzer


class AnalysisScheduler:
    """Schedules and manages periodic analysis jobs."""
    
    def __init__(
        self,
        analyzer: TradeHistoryAnalyzer,
        enabled: bool = True,
        interval_hours: float = 12.0,
        analysis_period_days: int = 30,
        min_trades_required: int = 10,
    ):
        self.analyzer = analyzer
        self.enabled = enabled
        self.interval_hours = interval_hours
        self.analysis_period_days = analysis_period_days
        self.min_trades_required = min_trades_required
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_analysis: Dict[str, datetime] = {}  # agent_id -> last_analysis_time
    
    async def start(self, run_immediately: bool = True, initial_delay_seconds: int = 30):
        """
        Start the scheduler.
        
        Args:
            run_immediately: If True, run analysis immediately on start. Otherwise wait for first interval.
            initial_delay_seconds: Delay before running initial analysis (to allow agents to start)
        """
        if not self.enabled:
            logger.info("Analysis scheduler is disabled")
            return
        
        if self._running:
            logger.warning("Analysis scheduler is already running")
            return
        
        self._running = True
        
        # Run immediate analysis if requested
        if run_immediately:
            async def run_initial_analysis():
                # Wait for agents to start
                logger.info(f"Waiting {initial_delay_seconds} seconds for agents to start before initial analysis...")
                await asyncio.sleep(initial_delay_seconds)
                logger.info("Running initial analysis on startup...")
                try:
                    await self._run_scheduled_analyses()
                except Exception as e:
                    logger.error(f"Failed to run initial analysis: {e}", exc_info=True)
            
            # Run initial analysis in background
            asyncio.create_task(run_initial_analysis())
        
        self._task = asyncio.create_task(self._schedule_loop())
        logger.info(f"Analysis scheduler started (interval: {self.interval_hours} hours)")
    
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Analysis scheduler stopped")
    
    async def _schedule_loop(self):
        """Main scheduling loop."""
        while self._running:
            try:
                await self._run_scheduled_analyses()
                
                # Wait for next interval
                await asyncio.sleep(self.interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis scheduler loop: {e}", exc_info=True)
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def _run_scheduled_analyses(self):
        """Run analysis for all agents that need it."""
        if not self.enabled:
            logger.debug("Analysis scheduler is disabled, skipping")
            return
        
        # Get all running agents
        agents = self.analyzer.agent_manager.get_all_agents()
        running_agents = [a for a in agents if a.get("is_running", False)]
        
        if not running_agents:
            logger.info("No running agents found for analysis. Agents may not have started yet.")
            return
        
        logger.info(f"Running scheduled analysis for {len(running_agents)} agent(s): {[a['id'] for a in running_agents]}")
        
        # Run analysis for each agent
        for agent_info in running_agents:
            agent_id = agent_info["id"]
            
            # Check if enough time has passed since last analysis
            last_analysis = self._last_analysis.get(agent_id)
            if last_analysis:
                time_since = datetime.now() - last_analysis
                if time_since.total_seconds() < (self.interval_hours * 3600 * 0.9):  # 90% of interval
                    continue
            
            try:
                logger.info(f"Running analysis for agent {agent_id}")
                job = await self.analyzer.run_analysis(
                    agent_id=agent_id,
                    analysis_period_days=self.analysis_period_days,
                    min_trades_required=self.min_trades_required,
                    use_snapshot=True,
                )
                
                if job.status == "completed":
                    self._last_analysis[agent_id] = datetime.now()
                    logger.info(
                        f"✅ Analysis completed for {agent_id}: "
                        f"{job.insights_generated} insights generated from {job.trades_analyzed} trades"
                    )
                elif job.status == "failed":
                    logger.warning(
                        f"⚠️ Analysis failed for {agent_id}: {job.error_message}. "
                        f"This may be normal if there are not enough trades yet."
                    )
                else:
                    logger.warning(f"Analysis status for {agent_id}: {job.status}")
                    
            except ValueError as e:
                # This is expected when there aren't enough trades
                logger.info(f"ℹ️ Skipping analysis for {agent_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to run analysis for {agent_id}: {e}", exc_info=True)
        
        # Also run global analysis (aggregate across all agents)
        # Note: Global analysis is currently not fully implemented
        # It would need to aggregate trades from all agents
        logger.debug("Global analysis skipped (not yet implemented - would require aggregating trades from all agents)")
    
    def update_config(
        self,
        enabled: Optional[bool] = None,
        interval_hours: Optional[float] = None,
        analysis_period_days: Optional[int] = None,
        min_trades_required: Optional[int] = None,
    ):
        """Update scheduler configuration."""
        if enabled is not None:
            self.enabled = enabled
        if interval_hours is not None:
            self.interval_hours = interval_hours
        if analysis_period_days is not None:
            self.analysis_period_days = analysis_period_days
        if min_trades_required is not None:
            self.min_trades_required = min_trades_required
        
        logger.info(
            f"Analysis scheduler config updated: "
            f"enabled={self.enabled}, interval={self.interval_hours}h"
        )

