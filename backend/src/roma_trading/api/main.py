"""
FastAPI application with REST API and WebSocket support.

Endpoints:
- GET /api/agents - List all agents
- GET /api/agents/{id} - Get agent info
- GET /api/agents/{id}/account - Get account info
- GET /api/agents/{id}/positions - Get positions
- GET /api/agents/{id}/performance - Get performance metrics
- GET /api/agents/{id}/analytics - Get detailed analytics
- GET /api/agents/{id}/decisions - Get decision logs
- GET /api/agents/{id}/equity-history - Get equity curve
- GET /api/agents/{id}/trades - Get trade history
- GET /api/market/prices - Get current market prices
- WS /ws/agents/{id} - Real-time updates
"""

import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from loguru import logger
import yaml
import os

from roma_trading.config import get_settings
from roma_trading.agents import AgentManager
from roma_trading.core.analytics import TradingAnalytics
from roma_trading.core.chat_service import initialize_chat_service, get_chat_service
from roma_trading.core.trade_history_analyzer import TradeHistoryAnalyzer
from roma_trading.core.analysis_scheduler import AnalysisScheduler
from roma_trading.api.routes import config as config_routes
from roma_trading.prompts import initialize_prompt_repository


# Global agent manager
agent_manager = AgentManager()

# Global trade history analyzer and scheduler
trade_history_analyzer: Optional[TradeHistoryAnalyzer] = None
analysis_scheduler: Optional[AnalysisScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ROMA-01 Trading Platform...")
    
    global trade_history_analyzer, analysis_scheduler
    
    try:
        initialize_prompt_repository()
        await agent_manager.load_agents_from_config()
        asyncio.create_task(agent_manager.start_all())
        logger.info("All agents started successfully")
        
        # Initialize chat service
        initialize_chat_service(agent_manager)
        
        # Initialize trade history analysis system
        try:
            # Get config for analysis system
            config_path = Path("config/trading_config.yaml")
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                analysis_config = config.get("system", {}).get("trade_history_analysis", {})
            else:
                analysis_config = {}
            
            enabled = analysis_config.get("enabled", True)
            interval_hours = analysis_config.get("analysis_interval_hours", 12.0)
            analysis_period_days = analysis_config.get("analysis_period_days", 30)
            min_trades_required = analysis_config.get("min_trades_required", 10)
            
            if enabled:
                trade_history_analyzer = TradeHistoryAnalyzer(agent_manager=agent_manager)
                
                analysis_scheduler = AnalysisScheduler(
                    analyzer=trade_history_analyzer,
                    enabled=True,
                    interval_hours=float(interval_hours),
                    analysis_period_days=int(analysis_period_days),
                    min_trades_required=int(min_trades_required),
                )
                
                # Start scheduler (run immediately on startup)
                await analysis_scheduler.start(run_immediately=True)
                logger.info("Trade history analysis system initialized and started")
            else:
                logger.info("Trade history analysis is disabled")
        except Exception as e:
            logger.error(f"Failed to initialize trade history analysis: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Failed to start agents: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Stop analysis scheduler
    if analysis_scheduler:
        await analysis_scheduler.stop()
    
    await agent_manager.stop_all()


# Create FastAPI app
app = FastAPI(
    title="ROMA-01 Trading API",
    description="AI-powered cryptocurrency futures trading platform",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(config_routes.router)
config_routes.set_agent_manager(agent_manager)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "ROMA-01 Trading API",
        "version": "1.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/agents")
async def get_agents():
    """Get list of all trading agents."""
    return agent_manager.get_all_agents()


@app.get("/api/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get detailed agent information."""
    try:
        agent = agent_manager.get_agent(agent_id)
        return agent.get_status()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/agents/{agent_id}/account")
async def get_account(agent_id: str):
    """Get agent's account balance."""
    try:
        agent = agent_manager.get_agent(agent_id)
        snapshot = agent.get_account_snapshot()
        if snapshot:
            return snapshot
        account = await agent.dex.get_account_balance()
        initial_balance = agent.config.get("strategy", {}).get("initial_balance", 10000.0)
        return agent.logger_module.augment_account_balance(account, initial_balance)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/positions")
async def get_positions(agent_id: str):
    """Get agent's current positions."""
    try:
        agent = agent_manager.get_agent(agent_id)
        return await agent.dex.get_positions()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/performance")
async def get_performance(agent_id: str, lookback: int = 20):
    """Get agent's performance metrics."""
    try:
        agent = agent_manager.get_agent(agent_id)
        trades = agent.logger_module.get_trade_history()
        return agent.performance.calculate_metrics(trades, lookback=lookback)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/agents/{agent_id}/analytics")
async def get_analytics(agent_id: str):
    """
    Get agent's detailed trading analytics.
    
    Returns comprehensive analytics including:
    - Trade size statistics (avg, median)
    - Holding period statistics (avg, median)  
    - Leverage statistics (avg, median)
    - Confidence statistics (avg, median)
    - Position type distribution (% long, % short, % flat)
    - Win rate, expectancy
    - Biggest win/loss
    """
    try:
        agent = agent_manager.get_agent(agent_id)
        trades = agent.logger_module.get_trade_history()
        decisions = agent.logger_module.get_recent_decisions(limit=100)
        
        analytics = TradingAnalytics.calculate_analytics(trades, decisions)
        
        return analytics
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/decisions")
async def get_decisions(agent_id: str, limit: int = 20):
    """Get agent's recent decision logs."""
    try:
        agent = agent_manager.get_agent(agent_id)
        return agent.logger_module.get_recent_decisions(limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/agents/{agent_id}/equity-history")
async def get_equity_history(agent_id: str, limit: Optional[int] = None):
    """Get agent's equity curve history."""
    try:
        agent = agent_manager.get_agent(agent_id)
        return agent.logger_module.get_equity_history(limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/agents/{agent_id}/trades")
async def get_trade_history(
    agent_id: str, 
    limit: Optional[int] = None,
    source: str = "local"  # "local" (from logs, recommended) or "api" (from exchange, requires HMAC auth)
):
    """
    Get agent's completed trade history.
    
    Args:
        agent_id: Agent identifier
        limit: Max number of trades to return
        source: Data source - "local" (from logs, recommended) or "api" (from exchange)
    
    Returns:
        List of completed trades with PnL, prices, quantities, etc.
    
    Note:
        - "local" mode uses our persistent trade logs (recommended)
        - "api" mode requires HMAC SHA256 authentication (not yet implemented for V3 wallets)
    """
    try:
        agent = agent_manager.get_agent(agent_id)
        
        if source == "api":
            # Note: /fapi/v1/userTrades requires HMAC SHA256 signature
            # Our V3 wallet uses EIP-191 signature, which is incompatible
            # This would need separate HMAC API key configuration
            logger.warning(
                f"API source requested but not supported with V3 wallet authentication. "
                f"Falling back to local logs."
            )
            return agent.logger_module.get_trade_history(limit=limit)
        else:
            # Get trades from local persistent logs (recommended)
            logger.debug(f"Fetching trades from local logs for agent {agent_id}")
            return agent.logger_module.get_trade_history(limit=limit)
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch trade history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/prices")
async def get_market_prices(symbols: Optional[str] = None):
    """
    Get current market prices for specified symbols.
    
    Args:
        symbols: Comma-separated list of symbols (e.g., "BTCUSDT,ETHUSDT")
                 If not provided, returns default trading pairs.
    """
    try:
        # Get default symbols from any active agent
        if not symbols:
            default_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"]
        else:
            default_symbols = [s.strip() for s in symbols.split(",")]
        
        # Get any agent to access DEX
        agents_list = agent_manager.get_all_agents()
        if not agents_list:
            raise HTTPException(status_code=503, detail="No agents available")
        
        agent = agent_manager.get_agent(agents_list[0]["id"])
        
        prices = []
        for symbol in default_symbols:
            try:
                price = await agent.dex.get_market_price(symbol)
                prices.append({
                    "symbol": symbol.replace("USDT", ""),  # BTC, ETH, etc.
                    "fullSymbol": symbol,
                    "price": price
                })
            except Exception as e:
                logger.warning(f"Failed to fetch price for {symbol}: {e}")
        
        return prices
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch market prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/agents/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Pushes account, positions, and performance data every 5 seconds.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for agent {agent_id}")
    
    try:
        agent = agent_manager.get_agent(agent_id)
        
        while True:
            try:
                # Fetch current data
                account = await agent.dex.get_account_balance()
                positions = await agent.dex.get_positions()
                trades = agent.logger_module.get_trade_history()
                performance = agent.performance.calculate_metrics(trades)
                
                # Send to client
                data = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "account": account,
                    "positions": positions,
                    "performance": performance,
                    "status": agent.get_status(),
                }
                
                await websocket.send_json(data)
                
                # Wait 5 seconds
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for agent {agent_id}")
    except ValueError as e:
        logger.error(f"Agent not found: {e}")
        await websocket.close(code=1008, reason=str(e))
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011, reason="Internal error")


# ============================================
# Custom Prompts API
# ============================================

class CustomPromptUpdate(BaseModel):
    """Custom prompt update request model"""
    enabled: Optional[bool] = None
    trading_philosophy: Optional[str] = None
    entry_preferences: Optional[str] = None
    position_management: Optional[str] = None
    market_preferences: Optional[str] = None
    additional_rules: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message request model"""
    message: str


class ClosePositionRequest(BaseModel):
    """Manual close position payload."""
    symbol: str
    side: str
    quantity: Optional[float] = None
    quantity_pct: Optional[float] = None

    @staticmethod
    def _normalize_side(value: str) -> str:
        normalized = value.lower()
        if normalized not in {"long", "short"}:
            raise ValueError("side must be 'long' or 'short'")
        return normalized

    @staticmethod
    def _normalize_symbol(value: str) -> str:
        return value.upper()

    @staticmethod
    def _normalize_pct(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("quantity_pct must be positive")
        return value

    @staticmethod
    def _normalize_quantity(value: Optional[float]) -> Optional[float]:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("quantity must be positive")
        return value

    def normalized(self) -> "ClosePositionRequest":
        return self.copy(
            update={
                "symbol": self._normalize_symbol(self.symbol),
                "side": self._normalize_side(self.side),
                "quantity": self._normalize_quantity(self.quantity),
                "quantity_pct": self._normalize_pct(self.quantity_pct),
            }
        )


class CloseAllPositionsRequest(BaseModel):
    """Payload for closing all positions across agents."""
    agent_ids: Optional[List[str]] = None


@app.post("/api/admin/agents/{agent_id}/positions/close")
async def admin_close_position(
    agent_id: str,
    payload: ClosePositionRequest,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """Manually close a single position for an agent."""
    normalized = payload.normalized()
    try:
        agent = agent_manager.get_agent(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        result = await agent.close_position_manual(
            symbol=normalized.symbol,
            side=normalized.side,
            quantity=normalized.quantity,
            quantity_pct=normalized.quantity_pct,
        )
    except Exception as exc:
        logger.error(f"Failed to close position {normalized.symbol} for {agent_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))

    if not result:
        raise HTTPException(status_code=404, detail="Position not found or already closed")

    return {"status": "success", "data": result}


@app.post("/api/admin/positions/close-all")
async def admin_close_all_positions(
    request: CloseAllPositionsRequest,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """Close every open position across the provided agents (or all agents by default)."""
    target_agent_ids = request.agent_ids or [agent["id"] for agent in agent_manager.get_all_agents()]
    summary: List[Dict[str, Any]] = []

    for agent_id in target_agent_ids:
        try:
            agent = agent_manager.get_agent(agent_id)
        except ValueError:
            summary.append({"agent_id": agent_id, "closed": [], "error": "Agent not found"})
            continue

        try:
            positions = await agent.dex.get_positions()
        except Exception as exc:
            logger.error(f"Failed to fetch positions for {agent_id}: {exc}")
            summary.append({"agent_id": agent_id, "closed": [], "error": str(exc)})
            continue

        closed_results: List[Dict[str, Any]] = []
        for position in positions:
            try:
                result = await agent.close_position_manual(position["symbol"], position["side"])
                if result:
                    closed_results.append(result)
            except Exception as exc:
                logger.error(f"Failed to close {position['symbol']} for {agent_id}: {exc}")
                closed_results.append(
                    {
                        "symbol": position["symbol"],
                        "side": position["side"],
                        "error": str(exc),
                    }
                )

        summary.append({"agent_id": agent_id, "closed": closed_results})

    return {"status": "success", "data": summary}


@app.get("/api/agents/{agent_id}/prompts")
async def get_custom_prompts(
    agent_id: str,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """
    Get agent's custom prompt configuration
    
    Args:
        agent_id: Agent identifier
    
    Returns:
        Custom prompts configuration object
    """
    try:
        agent = agent_manager.get_agent(agent_id)
        
        custom_prompts = agent.config.get("strategy", {}).get("custom_prompts", {
            "enabled": False,
            "trading_philosophy": "",
            "entry_preferences": "",
            "position_management": "",
            "market_preferences": "",
            "additional_rules": ""
        })
        
        return {
            "status": "success",
            "data": custom_prompts
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get custom prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/prompts/system")
async def get_system_prompt(agent_id: str, language: Optional[str] = Query(None)):
    """
    Get core system prompt without custom sections. Publicly accessible.
    """
    try:
        agent = agent_manager.get_agent(agent_id)
        system_prompt = agent._build_system_prompt(language=language, include_custom=False)
        return {
            "status": "success",
            "data": {
                "system_prompt": system_prompt,
                "length": len(system_prompt),
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to build system prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/prompts/preview")
async def get_full_prompt_preview(
    agent_id: str,
    language: Optional[str] = Query(None),
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """
    Get the complete system prompt that will be sent to AI
    
    Args:
        agent_id: Agent identifier
    
    Returns:
        Complete system prompt including core rules and custom prompts
    """
    try:
        agent = agent_manager.get_agent(agent_id)
        
        # Build the actual system prompt using agent's method
        full_prompt = agent._build_system_prompt(language=language, include_custom=True)
        
        return {
            "status": "success",
            "data": {
                "full_prompt": full_prompt,
                "length": len(full_prompt)
            }
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to build prompt preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_with_ai(
    chat_request: ChatMessage,
    language: Optional[str] = Query("en", description="Language preference (en or zh)")
):
    """
    Chat with AI assistant about trading strategies, prompts, and platform features.
    Now supports token analysis requests (e.g., "analyze BTC", "what about ETH?").
    
    Args:
        chat_request: Chat message from user
        language: Language preference ("en" or "zh", default: "en")
    
    Returns:
        AI assistant's response
    """
    try:
        # Validate language parameter
        if language not in ["en", "zh"]:
            language = "en"
        
        chat_service = get_chat_service()
        response = await chat_service.chat(chat_request.message, language=language)
        
        return {
            "status": "success",
            "message": response
        }
    
    except RuntimeError as e:
        logger.error(f"Chat service error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process chat message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@app.put("/api/agents/{agent_id}/prompts")
async def update_custom_prompts(
    agent_id: str,
    prompts: CustomPromptUpdate,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """
    Update agent's custom prompts
    
    For account-centric configuration: Updates in-memory config (takes effect immediately)
    For legacy configuration: Updates both in-memory and config file
    
    Args:
        agent_id: Agent identifier
        prompts: Custom prompts configuration
    
    Returns:
        Update result and new configuration
    """
    try:
        # Get agent
        agent = agent_manager.get_agent(agent_id)
        
        # Ensure custom_prompts section exists in agent config
        if "strategy" not in agent.config:
            agent.config["strategy"] = {}
        if "custom_prompts" not in agent.config["strategy"]:
            agent.config["strategy"]["custom_prompts"] = {}
        
        # Update fields in memory configuration
        for field, value in prompts.dict(exclude_unset=True).items():
            if value is not None:
                agent.config["strategy"]["custom_prompts"][field] = value
        
        # Try to save to file for legacy mode (if config file exists)
        # For account-centric mode, we only update in-memory config
        # Users can manually update trading_config.yaml if they want persistence
        from pathlib import Path
        
        # Try to find legacy config file
        config_path = Path("config/models") / f"{agent_id}.yaml"
        if not config_path.exists():
            config_path = Path("backend/config/models") / f"{agent_id}.yaml"
        
        if config_path.exists():
            # Legacy mode: update config file
            logger.debug(f"Updating legacy config file: {config_path.absolute()}")
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = yaml.safe_load(f)
            
            if "strategy" not in file_config:
                file_config["strategy"] = {}
            if "custom_prompts" not in file_config["strategy"]:
                file_config["strategy"]["custom_prompts"] = {}
            
            # Sync with in-memory config
            file_config["strategy"]["custom_prompts"] = agent.config["strategy"]["custom_prompts"]
            
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(file_config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Updated custom prompts for agent {agent_id} (legacy mode - saved to file)")
        else:
            # Account-centric mode: only update in-memory
            logger.info(
                f"Updated custom prompts for agent {agent_id} (account-centric mode - in-memory only). "
                f"Update trading_config.yaml manually if you want persistence."
            )
        
        return {
            "status": "success",
            "message": f"Custom prompts updated for agent {agent_id}. Will take effect in next trading cycle.",
            "data": agent.config["strategy"]["custom_prompts"]
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update custom prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Trade History Analysis API
# ============================================

class AnalysisRequest(BaseModel):
    """Request payload for triggering analysis."""
    analysis_period_days: Optional[int] = 30
    min_trades_required: Optional[int] = 10


@app.get("/api/agents/{agent_id}/analysis/history")
async def get_agent_analysis_history(
    agent_id: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get analysis history for a specific agent."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        history = await trade_history_analyzer.get_analysis_history(
            agent_id=agent_id,
            limit=limit,
        )
        
        return {
            "status": "success",
            "data": {
                "history": [job.to_dict() for job in history]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get analysis history for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/history/global")
async def get_global_analysis_history(
    limit: int = Query(20, ge=1, le=100),
):
    """Get global analysis history."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        history = await trade_history_analyzer.get_analysis_history(
            agent_id=None,
            limit=limit,
        )
        
        return {
            "status": "success",
            "data": {
                "history": [job.to_dict() for job in history]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get global analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/{agent_id}/insights")
async def get_agent_insights(
    agent_id: str,
    limit: int = Query(10, ge=1, le=50),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
):
    """Get latest insights for a specific agent."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        insights = await trade_history_analyzer.get_latest_insights(
            agent_id=agent_id,
            limit=limit,
        )
        
        # Filter by confidence
        filtered = [ins for ins in insights if ins.confidence_score >= min_confidence]
        
        return {
            "status": "success",
            "data": {
                "insights": [ins.to_dict() for ins in filtered]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get insights for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/global")
async def get_global_insights(
    limit: int = Query(10, ge=1, le=50),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0),
):
    """Get global (shared) insights."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        insights = await trade_history_analyzer.get_latest_insights(
            agent_id=None,
            limit=limit,
        )
        
        # Filter by confidence
        filtered = [ins for ins in insights if ins.confidence_score >= min_confidence]
        
        return {
            "status": "success",
            "data": {
                "insights": [ins.to_dict() for ins in filtered]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get global insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/agents/{agent_id}/analyze")
async def trigger_agent_analysis(
    agent_id: str,
    request: AnalysisRequest,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """Manually trigger analysis for an agent."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        job = await trade_history_analyzer.run_analysis(
            agent_id=agent_id,
            analysis_period_days=request.analysis_period_days or 30,
            min_trades_required=request.min_trades_required or 10,
            use_snapshot=True,
        )
        
        return {
            "status": "success",
            "data": job.to_dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to run analysis for {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/analyze/global")
async def trigger_global_analysis(
    request: AnalysisRequest,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """Manually trigger global analysis."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        # Note: Global analysis would need aggregation logic
        # For now, we'll analyze all agents individually
        agents = agent_manager.get_all_agents()
        results = []
        
        for agent_info in agents:
            if not agent_info.get("is_running", False):
                continue
            try:
                job = await trade_history_analyzer.run_analysis(
                    agent_id=agent_info["id"],
                    analysis_period_days=request.analysis_period_days or 30,
                    min_trades_required=request.min_trades_required or 10,
                    use_snapshot=True,
                )
                results.append(job.to_dict())
            except Exception as e:
                logger.error(f"Failed to analyze agent {agent_info['id']}: {e}")
                results.append({
                    "agent_id": agent_info["id"],
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        logger.error(f"Failed to run global analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/analysis/jobs")
async def get_analysis_jobs(
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """Get all analysis jobs."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    try:
        all_jobs = list(trade_history_analyzer.jobs.values())
        all_jobs.sort(key=lambda x: x.scheduled_at, reverse=True)
        
        return {
            "status": "success",
            "data": {
                "jobs": [job.to_dict() for job in all_jobs[:limit]]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get analysis jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/analysis/jobs/{job_id}")
async def get_analysis_job(
    job_id: str,
    _: dict = Depends(config_routes.get_current_admin_token),
):
    """Get specific analysis job details."""
    if not trade_history_analyzer:
        raise HTTPException(status_code=503, detail="Analysis system not initialized")
    
    if job_id not in trade_history_analyzer.jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": "success",
        "data": trade_history_analyzer.jobs[job_id].to_dict()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "roma_trading.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )

