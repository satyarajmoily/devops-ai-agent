"""Agent Configuration Loader with Universal Configuration Integration."""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Import the new universal config loader
try:
    from .universal_config import UniversalConfigLoader
    UNIVERSAL_CONFIG_AVAILABLE = True
except ImportError:
    UNIVERSAL_CONFIG_AVAILABLE = False
    UniversalConfigLoader = None


class AgentsConfigLoader:
    """Load agent-specific configuration with universal config integration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config loader.
        
        Args:
            config_path: Path to agents.yml file. If None, uses AGENTS_CONFIG env var.
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize universal config loader if available
        self.universal_config = None
        if UNIVERSAL_CONFIG_AVAILABLE:
            try:
                self.universal_config = UniversalConfigLoader()
                self.logger.info("✅ Universal configuration system loaded")
            except Exception as e:
                self.logger.warning(f"⚠️  Universal config not available, falling back to legacy: {e}")
        
        # Legacy agents.yml loading for backward compatibility
        if config_path:
            self.config_path = Path(config_path)
        else:
            config_env = os.getenv('AGENTS_CONFIG', '/config/agents.yml')
            self.config_path = Path(config_env)
            
        self.config_data = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from agents.yml file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config_data = yaml.safe_load(f)
                self.logger.info(f"✅ Loaded agents configuration from {self.config_path}")
            else:
                raise FileNotFoundError(f"❌ CRITICAL: agents.yml not found at {self.config_path}")
        except Exception as e:
            self.logger.error(f"❌ CRITICAL: Failed to load agents config: {e}")
            raise RuntimeError(f"Cannot start without agents.yml configuration: {e}")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent using universal config first.
        
        Args:
            agent_name: Name of the agent (e.g., 'devops-ai-agent')
            
        Returns:
            Dictionary containing agent configuration
        """
        # Try universal config first
        if self.universal_config:
            try:
                return self.universal_config.get_agent_config(agent_name)
            except ValueError:
                self.logger.debug(f"Agent '{agent_name}' not found in universal config, trying legacy")
        
        # Fallback to legacy agents.yml
        if not self.config_data:
            raise RuntimeError("❌ CRITICAL: No configuration data loaded from agents.yml")
            
        # Look in platform_agents section
        platform_agents = self.config_data.get('platform_agents', {})
        agent_config = platform_agents.get(agent_name, {})
        
        if not agent_config:
            raise KeyError(f"❌ CRITICAL: Agent '{agent_name}' not found in any configuration")
        
        return agent_config
    
    def get_agent_environment_vars(self, agent_name: str) -> Dict[str, str]:
        """Get environment variables for a specific agent from configuration.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary of environment variables as key-value pairs
        """
        agent_config = self.get_agent_config(agent_name)
        env_list = agent_config.get('environment', [])
        
        env_dict = {}
        for env_var in env_list:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                env_dict[key] = value
        
        return env_dict
    
    def get_llm_config(self, agent_name: str) -> Dict[str, Any]:
        """Get LLM configuration for a specific agent using universal config.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary containing LLM configuration
        """
        # Try universal config first (preferred method)
        if self.universal_config:
            try:
                llm_config = self.universal_config.get_llm_config()
                self.logger.info(f"🤖 Agent {agent_name} using universal LLM config: {llm_config['provider']}:{llm_config['model']}")
                return llm_config
            except Exception as e:
                self.logger.warning(f"⚠️  Universal LLM config failed, falling back to legacy: {e}")
        
        # Fallback to legacy environment variables from agents.yml
        env_vars = self.get_agent_environment_vars(agent_name)
        
        # NO DEFAULTS! Everything must come from configuration
        required_keys = ['LLM_PROVIDER', 'LLM_MODEL', 'LLM_TEMPERATURE', 'LLM_MAX_TOKENS', 'LLM_TIMEOUT']
        missing_keys = [key for key in required_keys if key not in env_vars]
        
        if missing_keys:
            raise KeyError(f"❌ CRITICAL: Missing required LLM configuration in agents.yml for {agent_name}: {missing_keys}")
        
        llm_config = {
            'provider': env_vars['LLM_PROVIDER'],
            'model': env_vars['LLM_MODEL'], 
            'temperature': float(env_vars['LLM_TEMPERATURE']),
            'max_tokens': int(env_vars['LLM_MAX_TOKENS']),
            'timeout': int(env_vars['LLM_TIMEOUT'])
        }
        
        self.logger.info(f"🤖 Agent {agent_name} legacy LLM config: {llm_config['provider']}:{llm_config['model']}")
        return llm_config
    
    # New universal configuration methods
    def get_environment_config(self) -> Dict[str, Any]:
        """Get current environment configuration if universal config is available."""
        if self.universal_config:
            return {
                'current': self.universal_config.get_current_environment(),
                'type': self.universal_config.get_environment_type(),
                'capabilities': self.universal_config.get_environment_capabilities(
                    self.universal_config.get_current_environment()
                )
            }
        return {'current': 'local_docker', 'type': 'docker_compose', 'capabilities': []}
    
    def get_available_operations(self) -> list:
        """Get list of available operations for current environment."""
        if self.universal_config:
            return self.universal_config.get_available_operations()
        return ['restart_service', 'get_logs', 'check_resources']  # Legacy fallback
    
    def get_operation_schema(self, operation_name: str) -> Dict[str, Any]:
        """Get parameter schema for specific operation."""
        if self.universal_config:
            try:
                return self.universal_config.get_operation_schema(operation_name)
            except ValueError:
                pass
        return {}  # Legacy fallback
    
    def get_diagnostic_context(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic context for AI reasoning."""
        if self.universal_config:
            return self.universal_config.get_diagnostic_context()
        
        # Legacy fallback context
        return {
            'platform': {'name': 'Autonomous Trading Builder', 'environment': 'development'},
            'environment': {'current': 'local_docker', 'type': 'docker_compose'},
            'operations': {'available': ['restart_service', 'get_logs', 'check_resources']},
            'services': {'all': ['market-predictor', 'devops-ai-agent']},
            'network': {}
        }
    
    def validate_operation_request(self, operation: str) -> bool:
        """Validate if operation is supported in current environment."""
        if self.universal_config:
            return self.universal_config.validate_operation_request(operation)
        
        # Legacy validation
        legacy_operations = ['restart_service', 'get_logs', 'check_resources', 'execute_command']
        return operation in legacy_operations


# Global instance for easy access
_config_loader = None


def get_agents_config() -> AgentsConfigLoader:
    """Get the global agents config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = AgentsConfigLoader()
    return _config_loader


def get_agent_llm_config(agent_name: str) -> Dict[str, Any]:
    """Convenience function to get LLM config for an agent."""
    return get_agents_config().get_llm_config(agent_name) 

# New convenience functions for universal configuration
def get_universal_config() -> Optional[UniversalConfigLoader]:
    """Get the universal config loader if available."""
    config_loader = get_agents_config()
    return config_loader.universal_config

def get_environment_config() -> Dict[str, Any]:
    """Get current environment configuration."""
    return get_agents_config().get_environment_config()

def get_available_operations() -> list:
    """Get available operations for current environment."""
    return get_agents_config().get_available_operations()

def get_diagnostic_context() -> Dict[str, Any]:
    """Get comprehensive diagnostic context for AI."""
    return get_agents_config().get_diagnostic_context() 