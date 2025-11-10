"""
Agent Manager - Orchestrates multiple trading agents.

Handles:
- Loading agents from configuration
- Starting/stopping agents
- Providing unified access to agent data
"""

import asyncio
from typing import Dict, List
from pathlib import Path
import yaml
from loguru import logger

from .trading_agent import TradingAgent


class AgentManager:
    """
    Manages multiple trading agents running in parallel.
    
    This enables multi-model competition (e.g., DeepSeek vs Qwen).
    """

    def __init__(self):
        """Initialize agent manager."""
        self.agents: Dict[str, TradingAgent] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        
        # Global trading lock to prevent concurrent trading
        # This ensures only one agent can execute trades at a time
        self.trading_lock = asyncio.Lock()
        
        logger.info("Initialized AgentManager with trading lock")

    async def load_agents_from_config(self, config_path: str = "config/trading_config.yaml"):
        """
        Load and initialize agents from configuration file.
        
        Supports two configuration styles:
        1) Legacy: agents[].config_file -> per-agent YAML files
        2) Account-centric: top-level accounts/models/agents with references
        
        Args:
            config_path: Path to main trading configuration
        """
        # Load main config
        with open(config_path, "r") as f:
            main_config = yaml.safe_load(f)

        # Build lookups for account-centric mode if present
        accounts_by_id = {}
        models_by_id = {}
        if "accounts" in main_config:
            for acc in main_config.get("accounts", []):
                if "id" in acc:
                    accounts_by_id[acc["id"]] = acc
        if "models" in main_config:
            for mdl in main_config.get("models", []):
                if "id" in mdl:
                    models_by_id[mdl["id"]] = mdl

        # Load each agent
        for agent_spec in main_config.get("agents", []):
            if not agent_spec.get("enabled", True):
                logger.info(f"Skipping disabled agent: {agent_spec.get('id', '<no-id>')}")
                continue

            # Legacy mode: load per-agent config file
            if "config_file" in agent_spec:
                config_file = agent_spec["config_file"]
                with open(config_file, "r") as f:
                    agent_config = yaml.safe_load(f)
                self._resolve_env_vars(agent_config)
                agent = TradingAgent(
                    agent_id=agent_spec["id"],
                    config=agent_config,
                    trading_lock=self.trading_lock,
                )
                self.agents[agent_spec["id"]] = agent
                logger.info(f"Loaded agent (legacy): {agent_spec['id']} ({agent_spec.get('name','')})")
                continue

            # Account-centric mode: assemble config from accounts/models
            account_id = agent_spec.get("account_id")
            model_id = agent_spec.get("model_id")

            if not account_id or not model_id:
                logger.error(
                    f"Agent {agent_spec.get('id','<no-id>')} missing account_id/model_id and no config_file provided"
                )
                continue

            account = accounts_by_id.get(account_id)
            model = models_by_id.get(model_id)

            if account is None:
                logger.error(f"Account not found: {account_id} for agent {agent_spec.get('id','<no-id>')}")
                continue
            if model is None:
                logger.error(f"Model not found: {model_id} for agent {agent_spec.get('id','<no-id>')}")
                continue

            # Build exchange section based on account.dex_type
            dex_type = (account.get("dex_type") or account.get("type") or "aster").lower()
            exchange: Dict = {"type": dex_type}
            
            if dex_type == "aster":
                # Validate required fields
                required_fields = ["user", "signer", "private_key"]
                missing = [f for f in required_fields if not account.get(f)]
                if missing:
                    logger.error(
                        f"Account {account_id} missing required fields for Aster: {missing}"
                    )
                    continue
                
                exchange.update({
                    "user": account.get("user"),
                    "signer": account.get("signer"),
                    "private_key": account.get("private_key"),
                    "testnet": account.get("testnet", False),
                    "hedge_mode": account.get("hedge_mode", False),
                })
            elif dex_type == "hyperliquid":
                # Validate required fields
                api_secret = (
                    account.get("api_secret") or 
                    account.get("secret_key") or 
                    account.get("hl_secret_key")
                )
                if not api_secret:
                    logger.error(
                        f"Account {account_id} missing api_secret/secret_key for Hyperliquid"
                    )
                    continue
                
                exchange.update({
                    # api_key kept for consistency if provided
                    "api_key": account.get("api_key", ""),
                    "api_secret": api_secret,
                    "account_id": account.get("account_id"),
                    "testnet": account.get("testnet", False),
                    "hedge_mode": account.get("hedge_mode", False),
                })
            else:
                logger.error(f"Unsupported dex_type '{dex_type}' for account {account_id}")
                continue

            # Build llm section from model
            # Validate required fields
            required_model_fields = ["provider", "model"]
            missing_model = [f for f in required_model_fields if not model.get(f)]
            if missing_model:
                logger.error(
                    f"Model {model_id} missing required fields: {missing_model}"
                )
                continue
            
            llm: Dict = {
                "provider": model.get("provider"),
                "api_key": model.get("api_key"),
                "model": model.get("model"),
                "model_id": model_id,  # Save the model config ID for frontend
                "temperature": model.get("temperature", 0.15),
                "max_tokens": model.get("max_tokens", 4000),
            }

            # Strategy section: from agent_spec or merge with defaults
            default_strategy = {
                "initial_balance": 10000.0,
                "scan_interval_minutes": main_config.get("system", {}).get("scan_interval_minutes", 3),
                "max_account_usage_pct": 100,
                "prompt_language": main_config.get("system", {}).get("prompt_language", "en"),
                "default_coins": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"],
                "risk_management": {
                    "max_positions": 3,
                    "max_leverage": 10,
                    "max_position_size_pct": 30,
                    "max_total_position_pct": 80,
                    "max_single_trade_pct": 50,
                    "max_single_trade_with_positions_pct": 30,
                    "max_daily_loss_pct": 15,
                    "stop_loss_pct": 3,
                    "take_profit_pct": 10,
                },
                "trading_style": "balanced",
                "custom_prompts": {
                    "enabled": False,
                    "trading_philosophy": "",
                    "entry_preferences": "",
                    "position_management": "",
                    "market_preferences": "",
                    "additional_rules": "",
                },
            }
            
            # Merge agent_spec.strategy with defaults (deep merge for nested dicts)
            strategy = agent_spec.get("strategy", {})
            if strategy:
                # Deep merge risk_management
                if "risk_management" in strategy:
                    default_risk = default_strategy["risk_management"].copy()
                    default_risk.update(strategy["risk_management"])
                    strategy["risk_management"] = default_risk
                
                # Deep merge custom_prompts
                if "custom_prompts" in strategy:
                    default_prompts = default_strategy["custom_prompts"].copy()
                    default_prompts.update(strategy["custom_prompts"])
                    strategy["custom_prompts"] = default_prompts
                
                # Merge top-level
                merged = default_strategy.copy()
                merged.update(strategy)
                strategy = merged
            else:
                strategy = default_strategy

            # Assemble final agent config
            agent_config: Dict = {
                "agent": {
                    "id": agent_spec.get("id"),
                    "name": agent_spec.get("name") or agent_spec.get("id"),
                    "description": agent_spec.get("description", ""),
                },
                "llm": llm,
                "exchange": exchange,
                "strategy": strategy,
            }

            # Resolve env vars
            self._resolve_env_vars(agent_config)

            # Create agent
            agent = TradingAgent(
                agent_id=agent_spec.get("id"),
                config=agent_config,
                trading_lock=self.trading_lock,
            )
            self.agents[agent_spec.get("id")] = agent
            logger.info(f"Loaded agent (account-centric): {agent_spec.get('id')} ({agent_spec.get('name','')})")

        logger.info(f"Loaded {len(self.agents)} agents")

    def _resolve_env_vars(self, config: dict):
        """Resolve ${ENV_VAR} placeholders in config."""
        import os
        import re
        
        def resolve_value(value):
            if isinstance(value, str):
                # Match ${VAR_NAME}
                matches = re.findall(r'\$\{([^}]+)\}', value)
                for match in matches:
                    env_value = os.getenv(match, "")
                    value = value.replace(f"${{{match}}}", env_value)
                return value
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        for key, value in config.items():
            config[key] = resolve_value(value)

    async def start_all(self):
        """Start all agents in parallel."""
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(agent.start())
            self.tasks[agent_id] = task
            logger.info(f"Started agent: {agent_id}")
        
        logger.info(f"All {len(self.agents)} agents running")

    async def stop_all(self):
        """Stop all agents."""
        for agent_id, agent in self.agents.items():
            await agent.stop()
            if agent_id in self.tasks:
                self.tasks[agent_id].cancel()
        
        logger.info("All agents stopped")

    def get_agent(self, agent_id: str) -> TradingAgent:
        """Get agent by ID."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent not found: {agent_id}")
        return self.agents[agent_id]

    def get_all_agents(self) -> List[Dict]:
        """Get list of all agents with basic info."""
        result = []
        for agent_id, agent in self.agents.items():
            status = agent.get_status()
            # Flatten the structure for frontend
            result.append({
                "id": agent_id,
                "name": status.get("name", agent.config["agent"]["name"]),
                "is_running": status.get("is_running", False),
                "cycle_count": status.get("cycle_count", 0),
                "runtime_minutes": status.get("runtime_minutes", 0),
                # Added fields for multi-DEX/frontend filters
                "dex_type": agent.config.get("exchange", {}).get("type", "aster"),
                "account_id": agent.config.get("exchange", {}).get("account_id") or agent.config.get("exchange", {}).get("user"),
                "model_id": agent.config.get("llm", {}).get("model_id") or agent.config.get("llm", {}).get("model"),  # Use model_id if available, fallback to model
                "model_provider": agent.config.get("llm", {}).get("provider"),
            })
        return result

