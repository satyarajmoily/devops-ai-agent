"""
Universal Configuration Loader
Centralized configuration management for all UICI components
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class UniversalConfigLoader:
    """
    Universal Configuration Loader
    Manages all configuration from infrastructure/config/ directory
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Universal Configuration Loader
        
        Args:
            config_path: Optional override for config directory path
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine config path
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Check for mounted config directory first (Docker environment)
            mounted_config = Path("/config")
            if mounted_config.exists():
                self.config_path = mounted_config
            else:
                # Fallback: infrastructure/config relative to workspace root
                current_dir = Path(__file__).parent
                # Navigate up to workspace root, then to infrastructure/config
                workspace_root = current_dir.parent.parent.parent.parent.parent  # From devops-ai-agent/src/agent/config/
                self.config_path = workspace_root / "infrastructure" / "config"
        
        self.logger.info(f"Universal config path: {self.config_path}")
        
        # Load all configuration files
        self._load_all_configs()
    
    def _load_all_configs(self):
        """Load all configuration files from infrastructure/config/"""
        try:
            # Load core configuration files
            self.platform_config = self._load_yaml_file("platform.yml")
            self.environments_config = self._load_yaml_file("environments.yml")
            self.operations_config = self._load_yaml_file("operations.yml")
            self.command_translations_config = self._load_yaml_file("command_translations.yml")
            self.agents_config = self._load_yaml_file("agents.yml")
            
            self.logger.info("All universal configurations loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load universal configurations: {e}")
            raise RuntimeError(f"Universal configuration loading failed: {e}")
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load a specific YAML configuration file"""
        file_path = self.config_path / filename
        
        if not file_path.exists():
            self.logger.warning(f"Configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            self.logger.debug(f"Loaded configuration from {filename}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load {filename}: {e}")
            return {}
    
    def get_current_environment(self) -> str:
        """Get current environment from platform configuration"""
        try:
            return self.platform_config["platform"]["environment"]
        except KeyError:
            self.logger.warning("Current environment not found in platform.yml, defaulting to 'local_docker'")
            return "local_docker"
    
    def get_environment_type(self) -> str:
        """Get current environment type"""
        current_env = self.get_current_environment()
        
        try:
            return self.environments_config["environments"][current_env]["type"]
        except KeyError:
            self.logger.warning(f"Environment type not found for {current_env}, defaulting to 'docker'")
            return "docker"
    
    def get_environment_capabilities(self, environment: Optional[str] = None) -> List[str]:
        """Get capabilities for specified environment"""
        env_name = environment or self.get_current_environment()
        
        try:
            return self.environments_config["environments"][env_name]["capabilities"]
        except KeyError:
            self.logger.warning(f"Capabilities not found for environment {env_name}")
            return []
    
    def get_operation_config(self, operation_name: str) -> Dict[str, Any]:
        """Get configuration for a specific operation"""
        try:
            return self.operations_config["operations"][operation_name]
        except KeyError:
            self.logger.warning(f"Operation {operation_name} not found in operations.yml")
            return {}
    
    def get_command_translation(self, environment: str, operation: str) -> Dict[str, Any]:
        """Get command translation for specific environment and operation"""
        try:
            return self.command_translations_config["translations"][environment][operation]
        except KeyError:
            self.logger.warning(f"Command translation not found for {operation} in {environment}")
            return {}
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration from platform.yml"""
        try:
            return self.platform_config["credentials"]["llm"]
        except KeyError:
            self.logger.error("LLM configuration not found in platform.yml")
            raise RuntimeError("LLM configuration missing from platform.yml")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for specific agent"""
        try:
            return self.agents_config["agents"][agent_name]
        except KeyError:
            self.logger.warning(f"Agent {agent_name} not found in agents.yml")
            return {}
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information"""
        try:
            return self.platform_config["platform"]
        except KeyError:
            self.logger.warning("Platform information not found")
            return {}
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration"""
        try:
            return self.platform_config.get("monitoring", {})
        except Exception:
            self.logger.warning("Monitoring configuration not found")
            return {}
    
    def get_resource_limits(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get resource limits for environment"""
        env_name = environment or self.get_current_environment()
        
        try:
            env_config = self.environments_config["environments"][env_name]
            return env_config.get("resource_limits", {})
        except KeyError:
            self.logger.warning(f"Resource limits not found for {env_name}")
            return {}
    
    def get_network_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get network configuration for environment"""
        env_name = environment or self.get_current_environment()
        
        try:
            env_config = self.environments_config["environments"][env_name]
            return env_config.get("network", {})
        except KeyError:
            self.logger.warning(f"Network configuration not found for {env_name}")
            return {}
    
    def get_service_architecture(self) -> Dict[str, Any]:
        """Get service architecture information"""
        try:
            return self.platform_config.get("architecture", {})
        except Exception:
            self.logger.warning("Service architecture not found")
            return {}
    
    def get_service_dependencies(self, service: Optional[str] = None) -> Dict[str, Any]:
        """Get service dependencies"""
        try:
            architecture = self.get_service_architecture()
            if service:
                return architecture.get("services", {}).get(service, {}).get("dependencies", {})
            else:
                return architecture.get("dependencies", {})
        except Exception:
            self.logger.warning(f"Dependencies not found for service {service}")
            return {}
    
    def get_health_endpoints(self, service: Optional[str] = None) -> List[str]:
        """Get health check endpoints for service"""
        try:
            architecture = self.get_service_architecture()
            if service:
                service_config = architecture.get("services", {}).get(service, {})
                return service_config.get("health_endpoints", ["/health"])
            else:
                return ["/health", "/ready", "/metrics"]
        except Exception:
            self.logger.warning(f"Health endpoints not found for service {service}")
            return ["/health"]
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate all loaded configurations"""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required configuration files
        required_configs = ["platform_config", "environments_config", "operations_config", "agents_config"]
        for config_name in required_configs:
            config = getattr(self, config_name, {})
            if not config:
                validation_results["valid"] = False
                validation_results["errors"].append(f"Missing or empty {config_name}")
        
        # Validate current environment exists
        current_env = self.get_current_environment()
        if current_env not in self.environments_config.get("environments", {}):
            validation_results["valid"] = False
            validation_results["errors"].append(f"Current environment '{current_env}' not defined in environments.yml")
        
        # Validate LLM configuration
        try:
            llm_config = self.get_llm_config()
            required_llm_keys = ["provider", "model", "openai_api_key"]
            for key in required_llm_keys:
                if key not in llm_config:
                    validation_results["warnings"].append(f"Missing LLM config key: {key}")
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"LLM configuration validation failed: {e}")
        
        # Log validation results
        if validation_results["valid"]:
            self.logger.info("✅ Configuration validation passed")
        else:
            self.logger.error(f"❌ Configuration validation failed: {validation_results['errors']}")
        
        if validation_results["warnings"]:
            self.logger.warning(f"⚠️ Configuration warnings: {validation_results['warnings']}")
        
        return validation_results
    
    def reload_configuration(self):
        """Reload all configuration files"""
        self.logger.info("Reloading universal configuration...")
        self._load_all_configs()
        
        # Validate after reload
        validation = self.validate_configuration()
        if not validation["valid"]:
            raise RuntimeError(f"Configuration reload failed validation: {validation['errors']}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get summary of loaded configuration"""
        return {
            "current_environment": self.get_current_environment(),
            "environment_type": self.get_environment_type(),
            "available_environments": list(self.environments_config.get("environments", {}).keys()),
            "available_operations": list(self.operations_config.get("operations", {}).keys()),
            "available_agents": list(self.agents_config.get("agents", {}).keys()),
            "llm_provider": self.get_llm_config().get("provider"),
            "llm_model": self.get_llm_config().get("model"),
            "config_path": str(self.config_path),
            "platform_name": self.get_platform_info().get("name", "Unknown")
        } 