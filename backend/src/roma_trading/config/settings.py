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
    database_url: str = "sqlite+aiosqlite:///./roma_trading.db"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    cors_origins: str = "http://localhost:3000"

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

