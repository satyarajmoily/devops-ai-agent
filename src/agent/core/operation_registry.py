"""
Operation Registry
Dynamic registry of available operations loaded from configuration
"""

import logging
from typing import Dict, Any, List, Optional
from ..config.simple_config import get_config

logger = logging.getLogger(__name__)

class OperationRegistry:
    """
    Dynamic registry of available operations
    Loads operation definitions from configuration and provides validation
    """
    
    def __init__(self, config_loader=None):
        """Initialize operation registry with configuration loader"""
        self.config_loader = config_loader or get_config()
        self.operations = self._load_operations_from_config()
        self.current_environment = "gateway"  # AI Command Gateway environment
        
        logger.info(
            f"Operation registry initialized with {len(self.operations)} operations "
            f"for environment: {self.current_environment}"
        )
    
    def _load_operations_from_config(self) -> Dict[str, Any]:
        """Load operation definitions from configuration"""
        # AI Command Gateway operation definitions
        operations = {
            "check_resources": {
                "description": "Check system resource usage via AI Command Gateway",
                "category": "monitoring",
                "environments": ["gateway"],
                "parameters": {
                    "target": {"type": "string", "required": True},
                    "metrics": {"type": "array", "default": ["cpu", "memory"]},
                    "format": {"type": "string", "default": "summary"}
                }
            },
            "get_logs": {
                "description": "Retrieve service logs via AI Command Gateway",
                "category": "diagnostic",
                "environments": ["gateway"],
                "parameters": {
                    "target": {"type": "string", "required": True},
                    "lines": {"type": "integer", "default": 50},
                    "level": {"type": "string", "default": "all"}
                }
            },
            "health_check": {
                "description": "Check service health via AI Command Gateway",
                "category": "monitoring",
                "environments": ["gateway"],
                "parameters": {
                    "target": {"type": "string", "required": True},
                    "endpoints": {"type": "array", "default": ["/health"]},
                    "timeout": {"type": "integer", "default": 10}
                }
            },
            "restart_service": {
                "description": "Restart a service via AI Command Gateway",
                "category": "management",
                "environments": ["gateway"],
                "parameters": {
                    "target": {"type": "string", "required": True},
                    "strategy": {"type": "string", "default": "graceful"},
                    "timeout": {"type": "integer", "default": 60}
                }
            },
            "scale_service": {
                "description": "Scale a service via AI Command Gateway",
                "category": "management",
                "environments": ["gateway"],
                "parameters": {
                    "target": {"type": "string", "required": True},
                    "replicas": {"type": "integer", "required": True},
                    "strategy": {"type": "string", "default": "gradual"}
                }
            },
            "execute_command": {
                "description": "Execute a custom command via AI Command Gateway",
                "category": "diagnostic",
                "environments": ["gateway"],
                "parameters": {
                    "command": {"type": "string", "required": True},
                    "timeout": {"type": "integer", "default": 30}
                }
            }
        }
        logger.debug(f"Loaded {len(operations)} operation definitions")
        return operations
    
    def get_all_operations(self) -> List[str]:
        """Get list of all operation names"""
        return list(self.operations.keys())
    
    def get_available_operations(self, environment: Optional[str] = None) -> List[str]:
        """Get operations available in specific environment"""
        env = environment or self.current_environment
        
        available_ops = []
        
        for op_name, op_config in self.operations.items():
            # Check if operation is supported in this environment
            op_environments = op_config.get("environments", [])
            if env in op_environments:
                available_ops.append(op_name)
        
        logger.debug(f"Environment '{env}' supports {len(available_ops)} operations")
        return available_ops
    
    def get_operation_config(self, operation_name: str) -> Dict[str, Any]:
        """Get full configuration for specific operation"""
        if operation_name not in self.operations:
            raise ValueError(f"Operation '{operation_name}' not found in registry")
        return self.operations[operation_name]
    
    def get_operation_schema(self, operation_name: str) -> Dict[str, Any]:
        """Get parameter schema for operation"""
        operation_config = self.get_operation_config(operation_name)
        return operation_config.get("parameters", {})
    
    def get_operation_description(self, operation_name: str) -> str:
        """Get human-readable description of operation"""
        operation_config = self.get_operation_config(operation_name)
        return operation_config.get("description", f"Operation: {operation_name}")
    
    def get_operation_category(self, operation_name: str) -> str:
        """Get category of operation (monitoring, management, diagnostic)"""
        operation_config = self.get_operation_config(operation_name)
        return operation_config.get("category", "unknown")
    
    def get_operations_by_category(self, category: str) -> List[str]:
        """Get all operations in specific category"""
        ops_in_category = []
        for op_name, op_config in self.operations.items():
            if op_config.get("category") == category:
                ops_in_category.append(op_name)
        return ops_in_category
    
    def get_all_categories(self) -> List[str]:
        """Get list of all operation categories"""
        categories = set()
        for op_config in self.operations.values():
            category = op_config.get("category", "unknown")
            categories.add(category)
        return list(categories)
    
    def validate_operation_exists(self, operation_name: str) -> bool:
        """Check if operation exists in registry"""
        return operation_name in self.operations
    
    def validate_operation_supported(self, operation_name: str, environment: Optional[str] = None) -> bool:
        """Check if operation is supported in environment"""
        if not self.validate_operation_exists(operation_name):
            return False
        
        available_ops = self.get_available_operations(environment)
        return operation_name in available_ops
    
    def validate_operation_parameters(self, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate operation parameters against schema
        Returns dict with validation results
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "normalized_params": {}
        }
        
        try:
            schema = self.get_operation_schema(operation_name)
            normalized_params = {}
            
            # Check required parameters
            for param_name, param_config in schema.items():
                is_required = param_config.get("required", False)
                param_value = parameters.get(param_name)
                
                if is_required and param_value is None:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Required parameter '{param_name}' is missing")
                    continue
                
                # Use default value if parameter not provided
                if param_value is None:
                    default_value = param_config.get("default")
                    if default_value is not None:
                        normalized_params[param_name] = default_value
                    continue
                
                # Type validation
                expected_type = param_config.get("type", "string")
                if not self._validate_parameter_type(param_value, expected_type):
                    validation_result["valid"] = False
                    validation_result["errors"].append(
                        f"Parameter '{param_name}' has invalid type. Expected: {expected_type}"
                    )
                    continue
                
                # Range validation for integers
                if expected_type == "integer" and "range" in param_config:
                    min_val, max_val = param_config["range"]
                    if not (min_val <= param_value <= max_val):
                        validation_result["valid"] = False
                        validation_result["errors"].append(
                            f"Parameter '{param_name}' value {param_value} outside range [{min_val}, {max_val}]"
                        )
                        continue
                
                # Options validation - handle arrays differently
                if "options" in param_config:
                    valid_options = param_config["options"]
                    
                    if expected_type == "array":
                        # For arrays, validate each element is in valid options
                        invalid_elements = [elem for elem in param_value if elem not in valid_options]
                        if invalid_elements:
                            validation_result["valid"] = False
                            validation_result["errors"].append(
                                f"Parameter '{param_name}' contains invalid elements: {invalid_elements}. Valid options: {valid_options}"
                            )
                            continue
                    else:
                        # For non-arrays, validate the value is in options
                        if param_value not in valid_options:
                            validation_result["valid"] = False
                            validation_result["errors"].append(
                                f"Parameter '{param_name}' value '{param_value}' not in valid options: {valid_options}"
                            )
                            continue
                
                normalized_params[param_name] = param_value
            
            # Check for unknown parameters
            for param_name in parameters:
                if param_name not in schema:
                    validation_result["warnings"].append(f"Unknown parameter '{param_name}' will be ignored")
            
            validation_result["normalized_params"] = normalized_params
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Parameter validation failed: {e}")
        
        return validation_result
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type"""
        type_validators = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict)
        }
        
        validator = type_validators.get(expected_type)
        if validator:
            return validator(value)
        
        # Default to string validation
        return isinstance(value, str)
    
    def get_operation_context_for_ai(self, operation_name: str) -> Dict[str, Any]:
        """Get comprehensive operation context for AI reasoning"""
        if not self.validate_operation_exists(operation_name):
            return {}
        
        operation_config = self.get_operation_config(operation_name)
        schema = self.get_operation_schema(operation_name)
        
        # Build parameter documentation for AI
        param_docs = {}
        for param_name, param_config in schema.items():
            param_docs[param_name] = {
                "type": param_config.get("type", "string"),
                "required": param_config.get("required", False),
                "default": param_config.get("default"),
                "description": param_config.get("description", ""),
                "examples": param_config.get("examples", []),
                "options": param_config.get("options", []),
                "range": param_config.get("range")
            }
        
        return {
            "name": operation_name,
            "description": operation_config.get("description", ""),
            "category": operation_config.get("category", "unknown"),
            "environments": operation_config.get("environments", []),
            "parameters": param_docs,
            "supported_in_current_env": self.validate_operation_supported(operation_name)
        }
    
    def get_all_operations_context_for_ai(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive context of all available operations for AI"""
        env = environment or self.current_environment
        available_ops = self.get_available_operations(env)
        
        operations_context = {}
        for op_name in available_ops:
            operations_context[op_name] = self.get_operation_context_for_ai(op_name)
        
        # Add category information
        categories_info = self.config_loader.get_operation_categories()
        
        return {
            "environment": env,
            "total_operations": len(available_ops),
            "operations": operations_context,
            "categories": categories_info,
            "operation_settings": self.config_loader.get_operation_settings()
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the operation registry"""
        stats = {
            "total_operations": len(self.operations),
            "current_environment": self.current_environment,
            "available_operations": len(self.get_available_operations()),
            "categories": {},
            "environments_supported": set()
        }
        
        # Count operations by category
        for op_name, op_config in self.operations.items():
            category = op_config.get("category", "unknown")
            if category not in stats["categories"]:
                stats["categories"][category] = 0
            stats["categories"][category] += 1
            
            # Collect supported environments
            environments = op_config.get("environments", [])
            stats["environments_supported"].update(environments)
        
        stats["environments_supported"] = list(stats["environments_supported"])
        return stats 