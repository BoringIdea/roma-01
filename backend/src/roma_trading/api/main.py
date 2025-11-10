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
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
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


# Global agent manager
agent_manager = AgentManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ROMA-01 Trading Platform...")
    
    try:
        await agent_manager.load_agents_from_config()
        asyncio.create_task(agent_manager.start_all())
        logger.info("All agents started successfully")
        
        # Initialize chat service
        initialize_chat_service(agent_manager)
    except Exception as e:
        logger.error(f"Failed to start agents: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
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
        return agent.logger_module.augment_account_balance(account)
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


@app.get("/api/agents/{agent_id}/prompts")
async def get_custom_prompts(agent_id: str):
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


@app.get("/api/agents/{agent_id}/prompts/preview")
async def get_full_prompt_preview(agent_id: str, language: Optional[str] = Query(None)):
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
        full_prompt = agent._build_system_prompt(language=language)
        
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
async def chat_with_ai(chat_request: ChatMessage):
    """
    Chat with AI assistant about trading strategies, prompts, and platform features.
    
    Args:
        chat_request: Chat message from user
    
    Returns:
        AI assistant's response
    """
    try:
        chat_service = get_chat_service()
        response = await chat_service.chat(chat_request.message)
        
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
async def update_custom_prompts(agent_id: str, prompts: CustomPromptUpdate):
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


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "roma_trading.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )

