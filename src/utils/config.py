"""Configuration management for the API Aggregator MCP Server."""

import os
from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration - using field names that match env vars
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8000
    mcp_server_debug: bool = False
    mcp_server_mode: Literal["api", "mcp", "both"] = "both"
    
    # API Keys
    openweather_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    # Authentication
    mcp_auth_enabled: bool = False
    mcp_api_key: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    # Provide access to settings with original names for backward compatibility
    @property
    def host(self) -> str:
        return self.mcp_server_host
    
    @property
    def port(self) -> int:
        return self.mcp_server_port
    
    @property
    def debug(self) -> bool:
        return self.mcp_server_debug
    
    @property
    def server_mode(self) -> Literal["api", "mcp", "both"]:
        return self.mcp_server_mode
    
    @property
    def auth_enabled(self) -> bool:
        return self.mcp_auth_enabled
    
    @property
    def api_key(self) -> Optional[str]:
        return self.mcp_api_key
    
    model_config = dict(env_file=".env", case_sensitive=False, extra="ignore")


# Global settings instance - will be created when get_settings() is first called
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the current settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def validate_api_keys() -> dict[str, bool]:
    """Validate which API keys are available."""
    settings = get_settings()
    return {
        "weather": bool(settings.openweather_api_key),
        "news": bool(settings.news_api_key),
        "stock": bool(settings.alpha_vantage_api_key),
    } 