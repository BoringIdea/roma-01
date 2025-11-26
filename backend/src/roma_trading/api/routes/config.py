"""Configuration management API routes for Settings portal."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, validator
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from roma_trading.config import get_settings
from roma_trading.core.security import (
    InvalidTokenError,
    create_jwt_token,
    decode_jwt_token,
    hash_password,
    verify_password,
)


_agent_manager: "AgentManager | None" = None


def set_agent_manager(manager: "AgentManager") -> None:
    global _agent_manager
    _agent_manager = manager


yaml = YAML()
yaml.preserve_quotes = True
yaml.indent(mapping=2, sequence=4, offset=2)

router = APIRouter(prefix="/api/config", tags=["config"])
bearer_scheme = HTTPBearer(auto_error=False)


def _resolve_config_path() -> Path:
    settings = get_settings()
    candidate = Path(settings.config_file_path)

    if candidate.is_absolute():
        return candidate

    cwd_candidate = Path.cwd() / candidate
    if cwd_candidate.exists():
        return cwd_candidate

    package_root_candidate = Path(__file__).resolve().parent
    for _ in range(4):
        package_root_candidate = package_root_candidate.parent
    return package_root_candidate / candidate


def _load_config() -> CommentedMap:
    config_path = _resolve_config_path()
    if not config_path.exists():
        raise HTTPException(status_code=500, detail="configuration file not found")
    with config_path.open("r", encoding="utf-8") as fh:
        return yaml.load(fh)


def _save_config(data: CommentedMap) -> None:
    config_path = _resolve_config_path()
    if not config_path.parent.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as fh:
        yaml.dump(data, fh)


def _convert(value: Any) -> Any:
    if isinstance(value, CommentedMap):
        return {k: _convert(v) for k, v in value.items()}
    if isinstance(value, CommentedSeq):
        return [_convert(item) for item in value]
    return value


def _to_commented(value: Any) -> Any:
    if isinstance(value, dict):
        commented = CommentedMap()
        for key, item in value.items():
            commented[key] = _to_commented(item)
        return commented
    if isinstance(value, list):
        commented_list = CommentedSeq()
        for item in value:
            commented_list.append(_to_commented(item))
        return commented_list
    return value


def _resolve_env_placeholder(value: Any) -> Any:
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_key = value[2:-1]
        env_value = os.environ.get(env_key)
        if env_value is None:
            return ""
        return env_value
    return value


def _resolve_env_mapping(record: Dict[str, Any]) -> Dict[str, Any]:
    resolved: Dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, dict):
            resolved[key] = _resolve_env_mapping(value)
        elif isinstance(value, list):
            resolved[key] = [
                _resolve_env_mapping(item) if isinstance(item, dict) else _resolve_env_placeholder(item)
                for item in value
            ]
        else:
            resolved[key] = _resolve_env_placeholder(value)
    return resolved


def _get_admin_node(config: CommentedMap) -> Dict[str, Any]:
    auth_section = config.get("auth") or {}
    admin_section = auth_section.get("admin") or {}
    return _convert(admin_section)


def _sanitize_admin_payload(admin_node: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "username": admin_node.get("username", ""),
        "has_password": bool(admin_node.get("password_hash")),
        "updated_at": admin_node.get("updated_at"),
    }


def _get_agents_snapshot(config: CommentedMap) -> Any:
    return _convert(config.get("agents") or [])


def _get_accounts_snapshot(config: CommentedMap) -> Any:
    return _convert(config.get("accounts") or [])


def _get_models_snapshot(config: CommentedMap) -> Any:
    return _convert(config.get("models") or [])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TradeHistoryAnalysisConfig(BaseModel):
    enabled: bool = True
    analysis_interval_hours: float = Field(default=12.0, ge=0.5, le=168.0)
    analysis_period_days: int = Field(default=30, ge=7, le=365)
    min_trades_required: int = Field(default=10, ge=5, le=1000)


class SystemConfig(BaseModel):
    scan_interval_minutes: int = Field(..., ge=1, le=60)
    max_concurrent_agents: int = Field(..., ge=1, le=50)
    log_level: str
    prompt_language: str
    trade_history_analysis: Optional[TradeHistoryAnalysisConfig] = None

    @validator("log_level")
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
        value_upper = value.upper()
        if value_upper not in allowed:
            raise ValueError(f"log_level must be one of {', '.join(sorted(allowed))}")
        return value_upper

    @validator("prompt_language")
    def _validate_prompt_language(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"en", "zh"}:
            raise ValueError("prompt_language must be 'en' or 'zh'")
        return normalized


class AdminUpdate(BaseModel):
    username: str
    password: Optional[str] = None

    @validator("password")
    def _normalize_password(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value or None


class AgentAdvancedOrders(BaseModel):
    model_config = ConfigDict(extra="allow")

    enable_take_profit: bool = True
    take_profit_pct: float = Field(5.0, ge=0.0)
    enable_stop_loss: bool = True
    stop_loss_pct: float = Field(2.0, ge=0.0)


class AgentCustomPrompts(BaseModel):
    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    trading_philosophy: str = ""
    entry_preferences: str = ""
    position_management: str = ""
    market_preferences: str = ""
    additional_rules: str = ""


class AgentRiskManagement(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_positions: int = Field(3, ge=0)
    max_leverage: float = Field(10.0, ge=0.0)
    max_position_size_pct: float = Field(30.0, ge=0.0)
    max_total_position_pct: float = Field(80.0, ge=0.0)
    max_single_trade_pct: float = Field(50.0, ge=0.0)
    max_single_trade_with_positions_pct: float = Field(30.0, ge=0.0)
    max_daily_loss_pct: float = Field(15.0, ge=0.0)
    stop_loss_pct: float = Field(3.0, ge=0.0)
    take_profit_pct: float = Field(10.0, ge=0.0)


class AgentStrategy(BaseModel):
    model_config = ConfigDict(extra="allow")

    initial_balance: float = Field(10000.0, ge=0.0)
    scan_interval_minutes: int = Field(3, ge=1)
    max_account_usage_pct: float = Field(100.0, ge=0.0, le=100.0)
    prompt_language: Optional[str] = None
    default_coins: List[str] = Field(default_factory=list)
    trading_style: Optional[str] = None
    risk_management: AgentRiskManagement = Field(default_factory=AgentRiskManagement)
    advanced_orders: Optional[AgentAdvancedOrders] = Field(default_factory=AgentAdvancedOrders)
    custom_prompts: Optional[AgentCustomPrompts] = Field(default_factory=AgentCustomPrompts)

    @validator("prompt_language", pre=True, always=True)
    def _normalize_lang(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = str(value).lower()
        return normalized if normalized in {"en", "zh"} else "en"

    @validator("default_coins", pre=True, always=True)
    def _ensure_default_coins(cls, value: Any) -> List[str]:
        if not value:
            return []
        if isinstance(value, str):
            parts = [item.strip() for item in value.split(",")]
        else:
            parts = [str(item).strip() for item in value]
        return [coin for coin in parts if coin]


class AgentConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    enabled: bool = True
    account_id: str
    model_id: str
    strategy: AgentStrategy

    @validator("id", "name", "account_id", "model_id")
    def _ensure_non_empty(cls, value: str, **kwargs: Any) -> str:
        trimmed = value.strip()
        if not trimmed:
            field_info = kwargs.get("field")
            field_name = getattr(field_info, "name", "value")
            raise ValueError(f"{field_name} must not be empty")
        return trimmed


class AccountConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    name: str
    dex_type: str
    testnet: Optional[bool] = None
    hedge_mode: Optional[bool] = None

    @validator("id", "name", "dex_type")
    def _ensure_non_empty(cls, value: str, **kwargs: Any) -> str:
        trimmed = value.strip()
        if not trimmed:
            field_info = kwargs.get("field")
            field_name = getattr(field_info, "name", "value")
            raise ValueError(f"{field_name} must not be empty")
        return trimmed


class ModelConfigModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    provider: str
    model: str
    temperature: Optional[float] = Field(default=None, ge=0.0)
    max_tokens: Optional[int] = Field(default=None, ge=0)

    @validator("id", "provider", "model")
    def _ensure_model_fields(cls, value: str, **kwargs: Any) -> str:
        trimmed = value.strip()
        if not trimmed:
            field_info = kwargs.get("field")
            field_name = getattr(field_info, "name", "value")
            raise ValueError(f"{field_name} must not be empty")
        return trimmed


class ConfigUpdateRequest(BaseModel):
    system: Optional[SystemConfig] = None
    admin: Optional[AdminUpdate] = None
    agents: Optional[List[AgentConfigModel]] = None
    accounts: Optional[List[AccountConfigModel]] = None
    models: Optional[List[ModelConfigModel]] = None

    def is_empty(self) -> bool:
        return (
            self.system is None
            and self.admin is None
            and self.agents is None
            and self.accounts is None
            and self.models is None
        )


class ConfigResponse(BaseModel):
    system: Dict[str, Any]
    auth: Dict[str, Any]
    agents: List[Dict[str, Any]]
    accounts: List[Dict[str, Any]]
    models: List[Dict[str, Any]]
    accounts_resolved: List[Dict[str, Any]]
    models_resolved: List[Dict[str, Any]]
    agents_resolved: List[Dict[str, Any]]
    version: Dict[str, Any]


def _require_credentials(credentials: Optional[HTTPAuthorizationCredentials]) -> str:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return credentials.credentials


def get_current_admin_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    token_str = _require_credentials(credentials)
    settings = get_settings()
    try:
        payload = decode_jwt_token(token_str, settings.config_auth_secret)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return payload


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    config = _load_config()
    admin_node = _get_admin_node(config)
    stored_username = admin_node.get("username", "")
    stored_hash = admin_node.get("password_hash", "")

    if request.username != stored_username or not verify_password(request.password, stored_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    settings = get_settings()
    token_pair = create_jwt_token(
        subject=request.username,
        secret=settings.config_auth_secret,
        expires_in_minutes=settings.config_token_exp_minutes,
    )
    return LoginResponse(access_token=token_pair.token, expires_at=token_pair.expires_at)


@router.get("", response_model=ConfigResponse)
def get_config(_: Dict[str, Any] = Depends(get_current_admin_token)) -> ConfigResponse:
    config = _load_config()
    system_node = _convert(config.get("system") or {})
    admin_node = _sanitize_admin_payload(_get_admin_node(config))
    agents_snapshot_raw = _get_agents_snapshot(config)
    agents_snapshot = agents_snapshot_raw if isinstance(agents_snapshot_raw, list) else []
    accounts_snapshot_raw = _get_accounts_snapshot(config)
    accounts_snapshot = accounts_snapshot_raw if isinstance(accounts_snapshot_raw, list) else []
    models_snapshot_raw = _get_models_snapshot(config)
    models_snapshot = models_snapshot_raw if isinstance(models_snapshot_raw, list) else []
    accounts_resolved = [_resolve_env_mapping(record) for record in accounts_snapshot]
    models_resolved = [_resolve_env_mapping(record) for record in models_snapshot]
    agents_resolved = [_resolve_env_mapping(record) for record in agents_snapshot]

    version_info = {
        "updated_at": admin_node.get("updated_at"),
    }

    return ConfigResponse(
        system=system_node,
        auth={"admin": admin_node},
        agents=agents_snapshot,
        accounts=accounts_snapshot,
        models=models_snapshot,
        accounts_resolved=accounts_resolved,
        models_resolved=models_resolved,
        agents_resolved=agents_resolved,
        version=version_info,
    )


def _update_system_config(config: CommentedMap, system: SystemConfig) -> None:
    system_dict = {
        "scan_interval_minutes": system.scan_interval_minutes,
        "max_concurrent_agents": system.max_concurrent_agents,
        "log_level": system.log_level,
        "prompt_language": system.prompt_language,
    }
    
    # Add trade history analysis config if provided
    if system.trade_history_analysis is not None:
        system_dict["trade_history_analysis"] = {
            "enabled": system.trade_history_analysis.enabled,
            "analysis_interval_hours": system.trade_history_analysis.analysis_interval_hours,
            "analysis_period_days": system.trade_history_analysis.analysis_period_days,
            "min_trades_required": system.trade_history_analysis.min_trades_required,
        }
    
    config["system"] = CommentedMap(system_dict)


def _update_admin_config(config: CommentedMap, admin: AdminUpdate) -> None:
    auth_section = config.get("auth")
    if not isinstance(auth_section, CommentedMap):
        auth_section = CommentedMap()
        config["auth"] = auth_section

    admin_section = auth_section.get("admin")
    if not isinstance(admin_section, CommentedMap):
        admin_section = CommentedMap()
        auth_section["admin"] = admin_section

    admin_section["username"] = admin.username

    if admin.password:
        admin_section["password_hash"] = hash_password(admin.password)
        admin_section["updated_at"] = datetime.now(timezone.utc).isoformat()


def _update_agents_config(config: CommentedMap, agents: List[AgentConfigModel]) -> None:
    if not agents:
        raise HTTPException(status_code=400, detail="at least one agent is required")

    seen_ids: set[str] = set()
    agent_seq = CommentedSeq()

    for agent in agents:
        payload = agent.model_dump(mode="python", exclude_none=True)
        agent_id = payload.get("id", "").strip()

        if agent_id in seen_ids:
            raise HTTPException(status_code=400, detail=f"duplicate agent id '{agent_id}'")
        seen_ids.add(agent_id)

        agent_seq.append(_to_commented(payload))

    config["agents"] = agent_seq


def _update_accounts_config(config: CommentedMap, accounts: List[AccountConfigModel]) -> None:
    if not accounts:
        raise HTTPException(status_code=400, detail="at least one account is required")

    seen_ids: set[str] = set()
    account_seq = CommentedSeq()

    for account in accounts:
        payload = account.model_dump(mode="python", exclude_none=True)
        account_id = payload.get("id", "").strip()

        if account_id in seen_ids:
            raise HTTPException(status_code=400, detail=f"duplicate account id '{account_id}'")
        seen_ids.add(account_id)

        account_seq.append(_to_commented(payload))

    config["accounts"] = account_seq


def _update_models_config(config: CommentedMap, models: List[ModelConfigModel]) -> None:
    if not models:
        raise HTTPException(status_code=400, detail="at least one model is required")

    seen_ids: set[str] = set()
    model_seq = CommentedSeq()

    for model in models:
        payload = model.model_dump(mode="python", exclude_none=True)
        model_id = payload.get("id", "").strip()

        if model_id in seen_ids:
            raise HTTPException(status_code=400, detail=f"duplicate model id '{model_id}'")
        seen_ids.add(model_id)

        model_seq.append(_to_commented(payload))

    config["models"] = model_seq


@router.put("", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    token_payload: Dict[str, Any] = Depends(get_current_admin_token),
) -> ConfigResponse:
    if request.is_empty():
        raise HTTPException(status_code=400, detail="no changes provided")

    config = _load_config()

    if request.system:
        _update_system_config(config, request.system)

    if request.admin:
        _update_admin_config(config, request.admin)

    if request.agents is not None:
        _update_agents_config(config, request.agents)
    if request.accounts is not None:
        _update_accounts_config(config, request.accounts)
    if request.models is not None:
        _update_models_config(config, request.models)

    _save_config(config)

    logger.info("Configuration updated by {}", token_payload.get("sub", "unknown"))

    if _agent_manager is not None:
        try:
            await _agent_manager.reload_agents()
        except Exception as exc:
            logger.error(f"Failed to reload agents after config update: {exc}")
            raise HTTPException(status_code=500, detail="Failed to reload agents. Check server logs.") from exc
    else:
        logger.warning("Agent manager not initialized; skipping agent reload")
    
    # Update analysis scheduler if system config was updated
    if request.system and request.system.trade_history_analysis:
        try:
            from roma_trading.api.main import analysis_scheduler
            if analysis_scheduler:
                analysis_scheduler.update_config(
                    enabled=request.system.trade_history_analysis.enabled,
                    interval_hours=request.system.trade_history_analysis.analysis_interval_hours,
                    analysis_period_days=request.system.trade_history_analysis.analysis_period_days,
                    min_trades_required=request.system.trade_history_analysis.min_trades_required,
                )
                logger.info("Analysis scheduler config updated")
        except Exception as exc:
            logger.warning(f"Failed to update analysis scheduler config: {exc}")

    return get_config(token_payload)

