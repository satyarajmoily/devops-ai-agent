"""Configuration settings for the Market Programmer Agent."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

# Import simple config
from .simple_config import get_config


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
    service_name: str = Field(default="devops-ai-agent", description="Service name")
    service_version: str = Field(default="0.1.0", description="Service version")
    
    # LLM Configuration - NO DEFAULTS! All values from agents.yml
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, description="Anthropic API key")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider (from agents.yml)")
    llm_model: Optional[str] = Field(default=None, description="LLM model name (from agents.yml)")
    llm_temperature: Optional[float] = Field(default=None, description="LLM temperature (from agents.yml)")
    llm_max_tokens: Optional[int] = Field(default=None, description="Maximum tokens (from agents.yml)")
    llm_timeout: Optional[int] = Field(default=None, description="LLM timeout (from agents.yml)")
    
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
    fallback_enabled: bool = Field(default=True, description="Enable fallback to rule-based analysis when AI fails")
    
    # Testing Configuration
    enable_testing: bool = Field(default=True, description="Enable local testing before deployment")
    test_timeout: int = Field(default=300, description="Test timeout in seconds")
    
    def __init__(self, **kwargs):
        """Initialize settings with LLM config from .env file."""
        super().__init__(**kwargs)
        
        # Load LLM configuration from .env file
        try:
            config = get_config()
            llm_config = config.get_llm_config()
            
            # Set LLM settings from .env file
            self.llm_provider = llm_config['provider']
            self.llm_model = llm_config['model']
            self.llm_temperature = llm_config['temperature']
            self.llm_max_tokens = llm_config['max_tokens']
            self.llm_timeout = llm_config['timeout']
            
        except Exception as e:
            # FAIL FAST - No fallbacks, no defaults
            raise RuntimeError(f"❌ CRITICAL: Cannot load LLM configuration from .env file: {e}")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()