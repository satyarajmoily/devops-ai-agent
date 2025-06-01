"""Configuration settings for the DevOps AI Agent."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

# Import strict config
from .simple_config import get_config


class Settings(BaseSettings):
    """Agent settings with strict .env file configuration - NO DEFAULTS."""
    
    # Application settings - NO DEFAULTS
    environment: str = Field(description="Environment name")
    log_level: str = Field(description="Logging level")
    debug: bool = Field(description="Debug mode")
    
    # API settings - NO DEFAULTS
    api_host: str = Field(description="API host")
    api_port: int = Field(description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # Service settings - NO DEFAULTS
    service_name: str = Field(description="Service name")
    service_version: str = Field(description="Service version")
    
    # LLM Configuration - NO DEFAULTS! All values from .env file
    openai_api_key: Optional[SecretStr] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, description="Anthropic API key")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider (from .env)")
    llm_model: Optional[str] = Field(default=None, description="LLM model name (from .env)")
    llm_temperature: Optional[float] = Field(default=None, description="LLM temperature (from .env)")
    llm_max_tokens: Optional[int] = Field(default=None, description="Maximum tokens (from .env)")
    llm_timeout: Optional[int] = Field(default=None, description="LLM timeout (from .env)")
    
    # External Service Configuration - NO DEFAULTS
    market_predictor_url: str = Field(description="Market predictor service URL")
    prometheus_url: str = Field(description="Prometheus URL")
    alertmanager_url: str = Field(description="Alertmanager URL")
    grafana_url: str = Field(description="Grafana URL")
    
    # GitHub Configuration - NO DEFAULTS
    github_token: str = Field(description="GitHub token")
    github_user_name: str = Field(description="GitHub user name")
    github_user_email: str = Field(description="GitHub user email")
    
    # Agent Configuration - NO DEFAULTS
    safety_mode: bool = Field(description="Safety mode enabled")
    fallback_enabled: bool = Field(description="Fallback enabled")
    monitoring_interval: int = Field(description="Monitoring interval")
    
    def __init__(self, **kwargs):
        """Initialize settings with strict config from .env file."""
        super().__init__(**kwargs)
        
        # Load configuration from .env file using strict config
        try:
            config = get_config()
            
            # Development settings
            dev_config = config.get_development_config()
            self.environment = dev_config['environment']
            self.log_level = dev_config['log_level']
            self.debug = self.environment.lower() == "development"
            
            # Agent settings
            agent_config = config.get_agent_config()
            self.api_host = "0.0.0.0"  # Standard for containers
            self.api_port = agent_config['port']
            self.service_name = agent_config['service_name']
            self.service_version = agent_config['service_version']
            self.safety_mode = agent_config['safety_mode']
            self.fallback_enabled = agent_config['fallback_enabled']
            self.monitoring_interval = agent_config['monitoring_interval']
            
            # LLM settings from .env file
            llm_config = config.get_llm_config()
            self.llm_provider = llm_config['provider']
            self.llm_model = llm_config['model']
            self.llm_temperature = llm_config['temperature']
            self.llm_max_tokens = llm_config['max_tokens']
            self.llm_timeout = llm_config['timeout']
            self.openai_api_key = SecretStr(llm_config['api_key']) if llm_config['api_key'] else None
            
            # Monitoring settings
            monitoring_config = config.get_monitoring_config()
            self.market_predictor_url = monitoring_config['market_predictor_url']
            self.prometheus_url = monitoring_config['prometheus_url']
            self.alertmanager_url = monitoring_config['alertmanager_url']
            self.grafana_url = monitoring_config['grafana_url']
            
            # GitHub settings
            github_config = config.get_github_config()
            self.github_token = github_config['token']
            self.github_user_name = github_config['user_name']
            self.github_user_email = github_config['user_email']
            
        except Exception as e:
            # FAIL FAST - No fallbacks, no defaults
            raise RuntimeError(f"❌ CRITICAL: Cannot load configuration from .env file: {e}")
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields from .env


# Global settings instance
_settings_instance = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance