"""
Strict Configuration Loader
Loads configuration from .env file with NO DEFAULTS - fails fast if values are missing
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class StrictConfig:
    """Strict configuration loader that requires all values from .env file"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the strict config loader
        
        Args:
            env_file: Path to .env file (defaults to .env in project root)
        """
        if env_file is None:
            # Look for .env file in devops-ai-agent root directory
            # Path: devops-ai-agent/src/agent/config/simple_config.py -> devops-ai-agent/.env
            agent_root = Path(__file__).parent.parent.parent
            env_file = agent_root / ".env"
        
        if not env_file.exists():
            raise FileNotFoundError(f"❌ CRITICAL: .env file not found at {env_file}")
        
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        self._config = {}
        self._load_config()
    
    def _require_env_var(self, var_name: str, var_type: str = "string") -> Any:
        """Get required environment variable or fail with clear error"""
        value = os.getenv(var_name)
        if value is None or value == "":
            raise ValueError(f"❌ REQUIRED: {var_name} must be set in .env file")
        
        # Type conversion
        try:
            if var_type == "int":
                return int(value)
            elif var_type == "float":
                return float(value)
            elif var_type == "bool":
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return value
        except ValueError as e:
            raise ValueError(f"❌ INVALID: {var_name} must be a valid {var_type}, got: {value}")
    
    def _load_config(self):
        """Load all configuration from environment variables - NO DEFAULTS"""
        
        # LLM Configuration - ALL REQUIRED
        self._config['llm'] = {
            'provider': self._require_env_var('LLM_PROVIDER'),
            'model': self._require_env_var('LLM_MODEL'),
            'temperature': self._require_env_var('LLM_TEMPERATURE', 'float'),
            'max_tokens': self._require_env_var('LLM_MAX_TOKENS', 'int'),
            'timeout': self._require_env_var('LLM_TIMEOUT', 'int'),
            'api_key': self._require_env_var('OPENAI_API_KEY')
        }
        
        # Agent Configuration - ALL REQUIRED
        self._config['agent'] = {
            'name': self._require_env_var('AGENT_NAME'),
            'port': self._require_env_var('AGENT_PORT', 'int'),
            'service_name': self._require_env_var('SERVICE_NAME'),
            'service_version': self._require_env_var('SERVICE_VERSION'),
            'safety_mode': self._require_env_var('SAFETY_MODE', 'bool'),
            'fallback_enabled': self._require_env_var('FALLBACK_ENABLED', 'bool'),
            'monitoring_interval': self._require_env_var('MONITORING_INTERVAL', 'int')
        }
        
        # Monitoring Services - ALL REQUIRED  
        self._config['monitoring'] = {
            'prometheus_url': self._require_env_var('PROMETHEUS_URL'),
            'alertmanager_url': self._require_env_var('ALERTMANAGER_URL'),
            'grafana_url': self._require_env_var('GRAFANA_URL'),
            'market_predictor_url': self._require_env_var('MARKET_PREDICTOR_URL')
        }
        
        # GitHub Configuration - ALL REQUIRED
        self._config['github'] = {
            'token': self._require_env_var('GITHUB_TOKEN'),
            'user_name': self._require_env_var('GITHUB_USER_NAME'),
            'user_email': self._require_env_var('GITHUB_USER_EMAIL')
        }
        
        # Repository Configuration - REQUIRED
        repos_str = self._require_env_var('TARGET_REPOSITORIES')
        self._config['repositories'] = {
            'target_repositories': repos_str.split(',') if repos_str else []
        }
        
        # Service Configuration - ALL REQUIRED
        self._config['service'] = {
            'max_actions_per_cycle': self._require_env_var('MAX_ACTIONS_PER_CYCLE', 'int'),
            'health_check_timeout': self._require_env_var('HEALTH_CHECK_TIMEOUT', 'int'),
            'metrics_cache_ttl': self._require_env_var('METRICS_CACHE_TTL', 'int'),
            'test_timeout': self._require_env_var('TEST_TIMEOUT', 'int')
        }
        
        # Development Settings - ALL REQUIRED
        self._config['development'] = {
            'enable_testing': self._require_env_var('ENABLE_TESTING', 'bool'),
            'auto_restart': self._require_env_var('AUTO_RESTART', 'bool'),
            'log_level': self._require_env_var('LOG_LEVEL'),
            'environment': self._require_env_var('ENVIRONMENT')
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

def get_config() -> StrictConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = StrictConfig()
    return _config_instance

def reload_config():
    """Reload the configuration"""
    global _config_instance
    _config_instance = None
    return get_config() 