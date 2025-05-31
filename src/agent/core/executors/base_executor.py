"""
Base Executor
Abstract base class for environment-specific operation executors
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from ...config.simple_config import get_config

logger = logging.getLogger(__name__)

class BaseExecutor(ABC):
    """
    Abstract base class for environment-specific operation executors
    Defines the interface that all executors must implement
    """
    
    def __init__(self, config):
        """Initialize base executor with configuration"""
        self.config = config
        self.environment = "docker"  # Default environment
        self.environment_type = "docker"
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.logger.info(f"Initialized {self.__class__.__name__} for environment: {self.environment}")
    
    @abstractmethod
    async def execute_operation(self, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific operation with given parameters
        
        Args:
            operation_name: Name of the operation to execute
            parameters: Normalized parameters for the operation
        
        Returns:
            Dict containing:
                - output: Operation output (string or structured data)
                - metadata: Additional execution metadata
                - return_code: Exit code if applicable
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Get list of operations this executor can handle
        
        Returns:
            List of operation names this executor supports
        """
        pass
    
    @abstractmethod
    async def validate_environment(self) -> Dict[str, Any]:
        """
        Validate that the execution environment is properly configured
        
        Returns:
            Dict containing:
                - valid: Boolean indicating if environment is valid
                - checks: List of validation checks performed
                - errors: List of validation errors if any
        """
        pass
    
    def get_command_translation(self, operation_name: str) -> Dict[str, Any]:
        """Get command translation for operation in current environment"""
        # Simplified - return basic command mapping
        return {
            "command": operation_name,
            "timeout": 60
        }
    
    def get_environment_limits(self) -> Dict[str, Any]:
        """Get resource limits for current environment"""
        return {
            "operation_timeout": 60,
            "max_concurrent_operations": 5,
            "memory_limit": "1Gi",
            "cpu_limit": "1"
        }
    
    def get_operation_timeout(self, operation_name: str, default: int = 60) -> int:
        """Get timeout for specific operation"""
        # Simplified timeout logic
        timeout_map = {
            "restart_service": 120,
            "scale_service": 180,
            "get_logs": 30,
            "check_resources": 30,
            "health_check": 15
        }
        return timeout_map.get(operation_name, default)
    
    def build_error_result(self, error: Exception, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Build standardized error result"""
        return {
            "output": f"Operation '{operation_name}' failed: {error}",
            "metadata": {
                "error": str(error),
                "error_type": type(error).__name__,
                "operation": operation_name,
                "parameters": parameters,
                "executor": self.__class__.__name__
            },
            "return_code": -1
        }
    
    def build_success_result(self, output: str, metadata: Dict[str, Any] = None, return_code: int = 0) -> Dict[str, Any]:
        """Build standardized success result"""
        return {
            "output": output,
            "metadata": metadata or {},
            "return_code": return_code
        }
    
    async def check_safety_restrictions(self, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check safety restrictions for operation
        
        Returns:
            Dict containing:
                - allowed: Boolean indicating if operation is allowed
                - restrictions: List of restrictions that apply
                - warnings: List of safety warnings
        """
        safety_result = {
            "allowed": True,
            "restrictions": [],
            "warnings": []
        }
        
        try:
            # Simplified safety checks using config
            safety_mode = self.config.get('agent.safety_mode', True)
            
            if not safety_mode:
                return safety_result
            
            # Check restricted commands
            restricted_commands = ["rm -rf", "dd if=", "mkfs", "shutdown", "reboot"]
            if operation_name == "execute_command":
                command = parameters.get("command", "")
                for restricted in restricted_commands:
                    if restricted in command:
                        safety_result["allowed"] = False
                        safety_result["restrictions"].append(f"Command contains restricted pattern: {restricted}")
            
            # Check operations requiring confirmation
            require_confirmation = ["restart_service", "scale_service"]
            if operation_name in require_confirmation:
                safety_result["warnings"].append(f"Operation '{operation_name}' requires confirmation in production")
            
            # Check restart frequency limits
            if operation_name == "restart_service":
                safety_result["warnings"].append("Maximum restart frequency: 3 per hour")
            
        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            safety_result["warnings"].append(f"Safety check failed: {e}")
        
        return safety_result 