"""Configuration settings for the Market Programmer Agent."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Agent settings with environment variable support and secret management."""
    
    # Application settings
    environment: str = Field(default="development", description="Environment name")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    
    # API settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8001, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # Service settings
    service_name: str = Field(default="market-programmer-agent", description="Service name")
    service_version: str = Field(default="0.1.0", description="Service version")
    
    # LLM Configuration
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, description="Anthropic API key")
    llm_provider: str = Field(default="openai", description="LLM provider (openai/anthropic)")
    llm_model: str = Field(default="gpt-4", description="LLM model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=4000, description="LLM max tokens")
    llm_timeout: int = Field(default=60, description="LLM request timeout")
    
    # External Service Configuration
    market_predictor_url: str = Field(default="http://localhost:8000", description="Market predictor service URL")
    prometheus_url: Optional[str] = Field(default=None, description="Prometheus server URL")
    loki_url: Optional[str] = Field(default=None, description="Loki server URL")
    
    # GitHub Integration
    github_token: Optional[SecretStr] = Field(default=None, description="GitHub personal access token")
    github_repository: Optional[str] = Field(default=None, description="Target GitHub repository")
    allowed_repositories: List[str] = Field(default_factory=list, description="Allowed repositories for agent operations")
    
    # Monitoring Configuration
    monitoring_interval: int = Field(default=30, description="Monitoring interval in seconds")
    health_check_timeout: int = Field(default=10, description="Health check timeout")
    metrics_cache_ttl: int = Field(default=60, description="Metrics cache TTL")
    
    # Agent Behavior Configuration
    max_actions_per_cycle: int = Field(default=3, description="Maximum actions per monitoring cycle")
    safety_mode: bool = Field(default=True, description="Enable safety mode (human approval required)")
    learning_enabled: bool = Field(default=True, description="Enable learning from outcomes")
    
    # Testing Configuration
    enable_testing: bool = Field(default=True, description="Enable local testing before deployment")
    test_timeout: int = Field(default=300, description="Test timeout in seconds")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()