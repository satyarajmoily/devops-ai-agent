"""Configuration settings for the DevOps AI Agent."""

# Import strict config
from .simple_config import get_config
from typing import List
from pydantic import Field


class Settings:
    """Agent settings with strict .env file configuration - NO DEFAULTS."""
    
    def __init__(self):
        """Initialize settings with strict config from .env file."""
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
            self.api_prefix = "/api/v1"
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
            self.openai_api_key = llm_config['api_key']
            self.anthropic_api_key = None  # Not used currently
            
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
            
            # AI Command Gateway settings
            gateway_config = config.get_gateway_config()
            self.ai_command_gateway_url = gateway_config['url']
            self.ai_command_gateway_timeout = gateway_config['timeout']
            self.ai_command_gateway_source_id = gateway_config['source_id']
            
            # AI Command Gateway Configuration (REQUIRED - no defaults)
            self.ai_command_gateway_url = gateway_config['url']
            self.ai_command_gateway_timeout = gateway_config['timeout']
            self.ai_command_gateway_source_id = gateway_config['source_id']
            
            # Gateway Operation Defaults (REQUIRED - no code fallbacks)
            self.gateway_default_timeout_seconds = gateway_config['default_timeout_seconds']
            self.gateway_default_log_lines = gateway_config['default_log_lines']
            self.gateway_default_restart_strategy = gateway_config['default_restart_strategy']
            self.gateway_default_health_retries = gateway_config['default_health_retries']
            self.gateway_default_priority = gateway_config['default_priority']
            self.gateway_default_metrics = gateway_config['default_metrics']
            self.gateway_default_health_endpoints = gateway_config['default_health_endpoints']
            
        except Exception as e:
            # FAIL FAST - No fallbacks, no defaults
            raise RuntimeError(f"❌ CRITICAL: Cannot load configuration from .env file: {e}")

    # Computed properties for parsed defaults
    @property
    def gateway_default_metrics_list(self) -> List[str]:
        """Parse metrics string into list"""
        return [metric.strip() for metric in self.gateway_default_metrics.split(',')]
    
    @property  
    def gateway_default_health_endpoints_list(self) -> List[str]:
        """Parse health endpoints string into list"""
        return [endpoint.strip() for endpoint in self.gateway_default_health_endpoints.split(',')]


# Global settings instance
_settings_instance = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance