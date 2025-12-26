"""Application settings and configuration."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # LLM API Keys
    deepseek_api_key: Optional[str] = None
    qwen_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    # Custom LLM
    custom_llm_base_url: Optional[str] = None
    custom_llm_api_key: Optional[str] = None

    # Aster DEX Configuration - Multi-Account Support
    # Each model has its own account, loaded from model config files
    # These are kept as optional for backward compatibility
    aster_user: Optional[str] = None
    aster_signer: Optional[str] = None
    aster_private_key: Optional[str] = None
    
    # DeepSeek Account
    aster_user_deepseek: Optional[str] = None
    aster_signer_deepseek: Optional[str] = None
    aster_private_key_deepseek: Optional[str] = None
    
    # Qwen Account
    aster_user_qwen: Optional[str] = None
    aster_signer_qwen: Optional[str] = None
    aster_private_key_qwen: Optional[str] = None
    
    # Claude Account
    aster_user_claude: Optional[str] = None
    aster_signer_claude: Optional[str] = None
    aster_private_key_claude: Optional[str] = None
    
    # Grok Account
    aster_user_grok: Optional[str] = None
    aster_signer_grok: Optional[str] = None
    aster_private_key_grok: Optional[str] = None
    
    # Gemini Account
    aster_user_gemini: Optional[str] = None
    aster_signer_gemini: Optional[str] = None
    aster_private_key_gemini: Optional[str] = None
    
    # GPT Account
    aster_user_gpt: Optional[str] = None
    aster_signer_gpt: Optional[str] = None
    aster_private_key_gpt: Optional[str] = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/roma_trading.db"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout: float = 30.0
    database_pool_recycle: int = 1800

    # Trade execution controls
    max_concurrent_trades: int = 2
    trade_execution_timeout_seconds: float = 300.0

    # LLM concurrency controls
    llm_max_concurrent_requests: int = 4

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    cors_origins: str = "http://localhost:3000"

    # x402 Integration
    x402_enabled: bool = False
    x402_price_usdc: float = 5.0
    x402_network: str = "base-sepolia"
    x402_pay_to_address: Optional[str] = None
    x402_payment_description: str = "roma-01 strategy recommendation"
    x402_resource_description: str = "AI-generated trading strategy advice"
    x402_resource_mime_type: str = "application/json"
    x402_max_deadline_seconds: int = 120
    x402_discoverable: bool = True
    x402_facilitator_url: Optional[str] = None
    x402_cdp_api_key_id: Optional[str] = None
    x402_cdp_api_key_secret: Optional[str] = None

    # Strategy advisory configuration
    strategy_model_id: Optional[str] = None
    strategy_disclaimer_text: Optional[str] = (
        "These AI-generated trading suggestions are provided for informational purposes only and do not constitute financial advice."
    )

    # Remote strategy (Buyer) configuration
    remote_strategy_enabled: bool = False
    remote_x402_endpoint: Optional[str] = None
    remote_x402_network: Optional[str] = None
    remote_x402_payment_asset: str = "USDC"
    remote_x402_account: Optional[str] = None
    remote_x402_private_key: Optional[str] = None
    remote_x402_price_cap: Optional[float] = None
    remote_x402_discovery: Optional[str] = None
    remote_fallback_mode: str = "local"
    remote_timeout_seconds: int = 10
    remote_retry_limit: int = 1
    # Config Portal Auth
    config_auth_secret: str = "roma-config-secret"
    config_token_exp_minutes: int = 120
    config_file_path: str = "config/trading_config.yaml"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins into a list."""
        # Handle wildcard for all origins
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
