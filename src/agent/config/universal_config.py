"""
Universal Configuration Loader
Handles all configuration files from infrastructure/config/ for environment-agnostic operations
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class UniversalConfigLoader:
    """
    Load all configurations from infrastructure/config/
    Single source of truth for all agent configurations
    """
    
    def __init__(self, config_base_path: Optional[str] = None):
        # Default to infrastructure/config mounted in container or local path
        if config_base_path:
            self.base_path = Path(config_base_path)
        elif os.path.exists("/config"):  # Container mount
            self.base_path = Path("/config")
        else:  # Local development
            self.base_path = Path(__file__).parent.parent.parent.parent.parent / "infrastructure" / "config"
        
        logger.info(f"Loading universal configuration from {self.base_path}")
        
        # Load all configuration files
        self.platform_config = self._load_yaml("platform.yml")
        self.agents_config = self._load_yaml("agents.yml")
        self.repositories_config = self._load_yaml("repositories.yml")
        self.environments_config = self._load_yaml("environments.yml")
        self.operations_config = self._load_yaml("operations.yml")
        self.command_translations_config = self._load_yaml("command_translations.yml")
        
        # Validate critical configurations
        self._validate_configurations()
        
        logger.info(f"Universal configuration loaded successfully - Environment: {self.get_current_environment()}, Operations: {len(self.get_all_operations())}, Environments: {len(self.get_all_environments())}")
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file with error handling"""
        config_path = self.base_path / filename
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            raise FileNotFoundError(f"Required configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded configuration file: {filename}")
                return config or {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML file: {filename}", error=str(e))
            raise ValueError(f"Invalid YAML in {filename}: {e}")
        except Exception as e:
            logger.error(f"Failed to load configuration file: {filename}", error=str(e))
            raise
    
    def _validate_configurations(self):
        """Validate that all required configurations are present"""
        required_sections = {
            "platform_config": ["platform", "credentials"],
            "environments_config": ["environments"],
            "operations_config": ["operations"],
            "command_translations_config": ["translations"]
        }
        
        for config_name, required_keys in required_sections.items():
            config = getattr(self, config_name)
            for key in required_keys:
                if key not in config:
                    raise ValueError(f"Missing required section '{key}' in {config_name}")
    
    # LLM Configuration
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration from platform.yml - NO HARDCODING!"""
        return self.platform_config["credentials"]["llm"]
    
    # Environment Configuration
    def get_current_environment(self) -> str:
        """Get current environment from platform configuration"""
        return self.platform_config["platform"]["environment"]
    
    def get_all_environments(self) -> List[str]:
        """Get list of all configured environments"""
        return list(self.environments_config["environments"].keys())
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get configuration for specific environment"""
        environments = self.environments_config["environments"]
        if environment not in environments:
            raise ValueError(f"Environment '{environment}' not configured")
        return environments[environment]
    
    def get_environment_capabilities(self, environment: str) -> List[str]:
        """Get what operations are available in this environment"""
        env_config = self.get_environment_config(environment)
        return env_config.get("capabilities", [])
    
    def get_environment_type(self, environment: Optional[str] = None) -> str:
        """Get environment type (docker_compose, oci, k8s)"""
        env = environment or self.get_current_environment()
        env_config = self.get_environment_config(env)
        return env_config.get("type", "unknown")
    
    def get_environment_limits(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get environment resource limits and constraints"""
        env = environment or self.get_current_environment()
        env_config = self.get_environment_config(env)
        return env_config.get("limits", {})
    
    def detect_environment(self) -> str:
        """Auto-detect current environment based on detection rules"""
        detection_rules = self.environments_config.get("detection", {})
        
        for env_name, rules in detection_rules.items():
            indicators = rules.get("indicators", [])
            if self._check_environment_indicators(indicators):
                logger.info(f"Auto-detected environment: {env_name}")
                return env_name
        
        # Fallback to default
        default_env = self.environments_config.get("default_environment", "local_docker")
        logger.warning(f"Could not detect environment, using default: {default_env}")
        return default_env
    
    def _check_environment_indicators(self, indicators: List[str]) -> bool:
        """Check if environment indicators are present"""
        for indicator in indicators:
            if "environment variable" in indicator:
                env_var = indicator.split()[0]
                if not os.getenv(env_var):
                    return False
            elif "exists" in indicator:
                file_path = indicator.split()[0]
                if not Path(file_path.replace("~", os.path.expanduser("~"))).exists():
                    return False
            elif "command available" in indicator:
                command = indicator.split()[0]
                if os.system(f"which {command} > /dev/null 2>&1") != 0:
                    return False
        return True
    
    # Operations Configuration
    def get_all_operations(self) -> List[str]:
        """Get list of all available operations"""
        return list(self.operations_config["operations"].keys())
    
    def get_operation_config(self, operation_name: str) -> Dict[str, Any]:
        """Get configuration for specific operation"""
        operations = self.operations_config["operations"]
        if operation_name not in operations:
            raise ValueError(f"Operation '{operation_name}' not configured")
        return operations[operation_name]
    
    def get_operation_schema(self, operation_name: str) -> Dict[str, Any]:
        """Get parameter schema for operation"""
        operation_config = self.get_operation_config(operation_name)
        return operation_config.get("parameters", {})
    
    def get_available_operations(self, environment: Optional[str] = None) -> List[str]:
        """Get operations available in specific environment"""
        env = environment or self.get_current_environment()
        env_capabilities = self.get_environment_capabilities(env)
        
        available_ops = []
        for op_name, op_config in self.operations_config["operations"].items():
            op_environments = op_config.get("environments", [])
            if env in op_environments or any(cap in env_capabilities for cap in [op_name]):
                available_ops.append(op_name)
        
        return available_ops
    
    def get_operation_categories(self) -> Dict[str, Any]:
        """Get operation categories and organization"""
        return self.operations_config.get("categories", {})
    
    def get_operation_settings(self) -> Dict[str, Any]:
        """Get global operation settings and safety rules"""
        return self.operations_config.get("settings", {})
    
    # Command Translation Configuration
    def get_command_translation(self, environment: str, operation: str) -> Dict[str, Any]:
        """Get command translation for operation in environment"""
        translations = self.command_translations_config["translations"]
        
        if environment not in translations:
            raise ValueError(f"No translations configured for environment: {environment}")
        
        env_translations = translations[environment]
        if operation not in env_translations:
            raise ValueError(f"No translation for operation '{operation}' in environment '{environment}'")
        
        return env_translations[operation]
    
    def get_command_builders(self, environment: str) -> Dict[str, Any]:
        """Get command builders and utilities for environment"""
        builders = self.command_translations_config.get("builders", {})
        return builders.get(environment, {})
    
    def get_translation_settings(self) -> Dict[str, Any]:
        """Get global translation settings and security rules"""
        return self.command_translations_config.get("settings", {})
    
    # Service and Repository Configuration  
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for specific service"""
        # Check platform agents first
        platform_agents = self.platform_config.get("agents", {})
        if service_name in platform_agents:
            return platform_agents[service_name]
        
        # Check repositories
        repositories = self.repositories_config.get("target_repositories", {})
        if service_name in repositories:
            return repositories[service_name]
        
        raise ValueError(f"Service '{service_name}' not found in configuration")
    
    def get_all_services(self) -> List[str]:
        """Get list of all configured services"""
        services = []
        
        # Add platform agents
        platform_agents = self.platform_config.get("agents", {})
        services.extend(platform_agents.keys())
        
        # Add repositories
        repositories = self.repositories_config.get("target_repositories", {})
        services.extend(repositories.keys())
        
        return list(set(services))  # Remove duplicates
    
    def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get service dependencies for analysis"""
        service_config = self.get_service_config(service_name)
        return service_config.get("dependencies", [])
    
    def get_health_endpoints(self, service_name: str) -> List[str]:
        """Get health check endpoints for service"""
        service_config = self.get_service_config(service_name)
        health_endpoint = service_config.get("health_endpoint", "/health")
        return [health_endpoint]
    
    # Platform Configuration
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        return self.platform_config["platform"]
    
    def get_monitoring_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get monitoring configuration for environment"""
        env = environment or self.get_current_environment()
        
        # Get monitoring URLs from platform config
        platform_monitoring = self.platform_config.get("services", {})
        
        # Get environment-specific monitoring from environments config
        env_monitoring = self.environments_config.get("configurations", {}).get("monitoring", {}).get(env, {})
        
        # Merge configurations
        monitoring_config = {**platform_monitoring, **env_monitoring}
        return monitoring_config
    
    def get_network_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get network configuration for environment"""
        env = environment or self.get_current_environment()
        
        # Get network info from platform config
        platform_network = self.platform_config.get("infrastructure", {})
        
        # Get environment-specific network config
        env_config = self.get_environment_config(env)
        env_network = env_config.get("connection", {})
        
        return {**platform_network, **env_network}
    
    def get_resource_limits(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get resource limits for environment"""
        env = environment or self.get_current_environment()
        return self.get_environment_limits(env)
    
    # Agent Configuration (backward compatibility)
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get agent configuration - maintains compatibility with existing code"""
        # First check agents.yml
        if agent_name in self.agents_config.get("platform_agents", {}):
            return self.agents_config["platform_agents"][agent_name]
        
        # Then check platform.yml agents section
        platform_agents = self.platform_config.get("agents", {})
        if agent_name in platform_agents:
            return platform_agents[agent_name]
        
        raise ValueError(f"Agent '{agent_name}' not found in configuration")
    
    # Configuration validation and diagnostics
    def validate_operation_request(self, operation: str, environment: Optional[str] = None) -> bool:
        """Validate if operation is supported in environment"""
        env = environment or self.get_current_environment()
        available_ops = self.get_available_operations(env)
        return operation in available_ops
    
    def get_diagnostic_context(self) -> Dict[str, Any]:
        """Get comprehensive context for AI diagnostic reasoning"""
        current_env = self.get_current_environment()
        
        return {
            "platform": self.get_platform_info(),
            "environment": {
                "current": current_env,
                "type": self.get_environment_type(current_env),
                "capabilities": self.get_environment_capabilities(current_env),
                "limits": self.get_environment_limits(current_env)
            },
            "operations": {
                "available": self.get_available_operations(current_env),
                "categories": self.get_operation_categories(),
                "settings": self.get_operation_settings()
            },
            "services": {
                "all": self.get_all_services(),
                "monitoring": self.get_monitoring_config(current_env)
            },
            "network": self.get_network_config(current_env)
        } 