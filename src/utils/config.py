"""Configuration management for the API Aggregator MCP Server."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    host: str = Field(default="localhost", env="MCP_SERVER_HOST")
    port: int = Field(default=8000, env="MCP_SERVER_PORT")
    debug: bool = Field(default=False, env="MCP_SERVER_DEBUG")
    
    # API Keys
    openweather_api_key: Optional[str] = Field(default=None, env="OPENWEATHER_API_KEY")
    news_api_key: Optional[str] = Field(default=None, env="NEWS_API_KEY")
    alpha_vantage_api_key: Optional[str] = Field(default=None, env="ALPHA_VANTAGE_API_KEY")
    
    # Authentication
    auth_enabled: bool = Field(default=False, env="MCP_AUTH_ENABLED")
    api_key: Optional[str] = Field(default=None, env="MCP_API_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the current settings instance."""
    return settings


def validate_api_keys() -> dict[str, bool]:
    """Validate which API keys are available."""
    return {
        "weather": bool(settings.openweather_api_key),
        "news": bool(settings.news_api_key),
        "stock": bool(settings.alpha_vantage_api_key),
    } 