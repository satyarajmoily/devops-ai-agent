"""
Simple Configuration Loader
Replaces the complex infrastructure config system with simple .env file loading
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class SimpleConfig:
    """Simple configuration loader that reads from .env files"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the simple config loader
        
        Args:
            env_file: Path to .env file (defaults to .env in project root)
        """
        if env_file is None:
            # Look for .env file in devops-ai-agent root directory
            # Path: devops-ai-agent/src/agent/config/simple_config.py -> devops-ai-agent/.env
            agent_root = Path(__file__).parent.parent.parent
            env_file = agent_root / ".env"
        
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load all configuration from environment variables"""
        
        # LLM Configuration
        self._config['llm'] = {
            'provider': os.getenv('LLM_PROVIDER', 'openai'),
            'model': os.getenv('LLM_MODEL', 'gpt-4.1-nano-2025-04-14'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.1')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '4000')),
            'timeout': int(os.getenv('LLM_TIMEOUT', '60')),
            'api_key': os.getenv('OPENAI_API_KEY', '')
        }
        
        # Agent Configuration
        self._config['agent'] = {
            'name': os.getenv('AGENT_NAME', 'devops-ai-agent'),
            'port': int(os.getenv('AGENT_PORT', '8001')),
            'service_name': os.getenv('SERVICE_NAME', 'devops-ai-agent'),
            'service_version': os.getenv('SERVICE_VERSION', '0.1.0'),
            'safety_mode': os.getenv('SAFETY_MODE', 'true').lower() == 'true',
            'fallback_enabled': os.getenv('FALLBACK_ENABLED', 'false').lower() == 'true',
            'monitoring_interval': int(os.getenv('MONITORING_INTERVAL', '30'))
        }
        
        # Monitoring Services
        self._config['monitoring'] = {
            'prometheus_url': os.getenv('PROMETHEUS_URL', 'http://prometheus:9090'),
            'alertmanager_url': os.getenv('ALERTMANAGER_URL', 'http://alertmanager:9093'),
            'grafana_url': os.getenv('GRAFANA_URL', 'http://grafana:3000'),
            'market_predictor_url': os.getenv('MARKET_PREDICTOR_URL', 'http://localhost:8000')
        }
        
        # GitHub Configuration
        self._config['github'] = {
            'token': os.getenv('GITHUB_TOKEN', ''),
            'user_name': os.getenv('GITHUB_USER_NAME', 'satyarajmoily'),
            'user_email': os.getenv('GITHUB_USER_EMAIL', 'satyarajmoily@gmail.com')
        }
        
        # Repository Configuration
        repos_str = os.getenv('TARGET_REPOSITORIES', '')
        self._config['repositories'] = {
            'target_repositories': repos_str.split(',') if repos_str else []
        }
        
        # Service Configuration
        self._config['service'] = {
            'max_actions_per_cycle': int(os.getenv('MAX_ACTIONS_PER_CYCLE', '3')),
            'health_check_timeout': int(os.getenv('HEALTH_CHECK_TIMEOUT', '10')),
            'metrics_cache_ttl': int(os.getenv('METRICS_CACHE_TTL', '60')),
            'test_timeout': int(os.getenv('TEST_TIMEOUT', '300'))
        }
        
        # Development Settings
        self._config['development'] = {
            'enable_testing': os.getenv('ENABLE_TESTING', 'true').lower() == 'true',
            'auto_restart': os.getenv('AUTO_RESTART', 'true').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config.get('llm', {})
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return self._config.get('agent', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        return self._config.get('monitoring', {})
    
    def get_github_config(self) -> Dict[str, Any]:
        """Get GitHub configuration"""
        return self._config.get('github', {})
    
    def get_repositories_config(self) -> Dict[str, Any]:
        """Get repositories configuration"""
        return self._config.get('repositories', {})
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service configuration"""
        return self._config.get('service', {})
    
    def get_development_config(self) -> Dict[str, Any]:
        """Get development configuration"""
        return self._config.get('development', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the entire configuration as a dictionary"""
        return self._config.copy()


# Global config instance
_config_instance = None

def get_config() -> SimpleConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SimpleConfig()
    return _config_instance

def reload_config():
    """Reload the configuration"""
    global _config_instance
    _config_instance = None
    return get_config() 