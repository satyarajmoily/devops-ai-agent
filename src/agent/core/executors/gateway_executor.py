"""
Gateway Executor
Implements infrastructure operations by delegating to AI Command Gateway
Replaces complex Docker SDK operations with natural language API calls
"""

import asyncio
import logging
from typing import Dict, Any, List
from .base_executor import BaseExecutor
from ...services.ai_command_gateway_client import get_gateway_client, GatewayOperationResult


class GatewayExecutor(BaseExecutor):
    """
    Gateway-based operation executor using AI Command Gateway
    Delegates all infrastructure operations to specialized AI Command Gateway service
    """
    
    def __init__(self, config):
        """Initialize Gateway executor with AI Command Gateway client"""
        super().__init__(config)
        self.environment = "gateway"
        self.environment_type = "ai_command_gateway"
        
        try:
            self.gateway_client = get_gateway_client()
            self.logger.info("Gateway executor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI Command Gateway client: {e}")
            raise RuntimeError(f"AI Command Gateway not available: {e}")
    
    def get_capabilities(self) -> List[str]:
        """Get operations this executor can handle via AI Command Gateway"""
        return [
            "get_logs",
            "check_resources", 
            "restart_service",
            "execute_command",
            "scale_service",  # Limited support via restart/stop
            "health_check"
        ]
    
    async def validate_environment(self) -> Dict[str, Any]:
        """Validate AI Command Gateway is accessible and operational"""
        validation_result = {
            "valid": True,
            "checks": [],
            "errors": []
        }
        
        try:
            # Check gateway health
            is_healthy = await self.gateway_client.health_check()
            if is_healthy:
                validation_result["checks"].append("AI Command Gateway accessible and healthy")
            else:
                validation_result["valid"] = False
                validation_result["errors"].append("AI Command Gateway health check failed")
            
            # Verify gateway configuration
            if hasattr(self.gateway_client, 'base_url'):
                validation_result["checks"].append(f"Gateway URL: {self.gateway_client.base_url}")
                validation_result["checks"].append(f"Source ID: {self.gateway_client.source_id}")
                validation_result["checks"].append(f"Timeout: {self.gateway_client.timeout}s")
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Gateway validation failed: {e}")
        
        return validation_result
    
    async def execute_operation(self, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation via AI Command Gateway using natural language intents"""
        self.logger.info(f"Executing gateway operation: {operation_name}")
        
        try:
            # Check safety restrictions
            safety_check = await self.check_safety_restrictions(operation_name, parameters)
            if not safety_check["allowed"]:
                raise ValueError(f"Operation blocked by safety restrictions: {safety_check['restrictions']}")
            
            # Log safety warnings
            for warning in safety_check["warnings"]:
                self.logger.warning(warning)
            
            # Route to specific operation handler
            if operation_name == "get_logs":
                return await self._get_logs_via_gateway(parameters)
            elif operation_name == "check_resources":
                return await self._check_resources_via_gateway(parameters)
            elif operation_name == "restart_service":
                return await self._restart_service_via_gateway(parameters)
            elif operation_name == "execute_command":
                return await self._execute_command_via_gateway(parameters)
            elif operation_name == "scale_service":
                return await self._scale_service_via_gateway(parameters)
            elif operation_name == "health_check":
                return await self._health_check_via_gateway(parameters)
            else:
                raise ValueError(f"Operation '{operation_name}' not implemented in GatewayExecutor")
        
        except Exception as e:
            self.logger.error(f"Gateway operation '{operation_name}' failed: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception details: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return self.build_error_result(e, operation_name, parameters)
    
    async def _get_logs_via_gateway(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get service logs via AI Command Gateway"""
        target = parameters["target"]
        gateway_config = self.config.get_gateway_config()
        lines = parameters.get("lines", gateway_config['default_log_lines'])
        level = parameters.get("level", "all")
        
        # SIMPLIFIED: Build simple context instead of complex intent
        context_parts = []
        if lines != gateway_config['default_log_lines']:
            context_parts.append(f"requesting {lines} lines")
        if level != "all":
            context_parts.append(f"filtering for {level} level")
        if parameters.get("since"):
            context_parts.append(f"since {parameters['since']}")
        
        context = ", ".join(context_parts) if context_parts else None
        
        try:
            result = await self.gateway_client.get_service_logs(
                service_name=target,
                lines=lines,
                level=level,
                context=context
            )
            
            return self._convert_gateway_result_to_executor_format(
                result, 
                operation_type="get_logs",
                original_parameters=parameters
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to get logs via gateway: {e}")
    
    async def _check_resources_via_gateway(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check service resources via AI Command Gateway"""
        target = parameters["target"]
        gateway_config = self.config.get_gateway_config()
        default_metrics = [metric.strip() for metric in gateway_config['default_metrics'].split(',')]
        metrics = parameters.get("metrics", default_metrics)
        format_type = parameters.get("format", "summary")
        
        # SIMPLIFIED: Build simple context
        context_parts = []
        if metrics != default_metrics:
            context_parts.append(f"metrics: {', '.join(metrics)}")
        if format_type != "summary":
            context_parts.append(f"format: {format_type}")
        
        context = ", ".join(context_parts) if context_parts else None
        
        try:
            result = await self.gateway_client.get_resource_usage(
                service_name=target,
                context=context
            )
            
            return self._convert_gateway_result_to_executor_format(
                result,
                operation_type="check_resources",
                original_parameters=parameters
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to check resources via gateway: {e}")
    
    async def _restart_service_via_gateway(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restart service via AI Command Gateway"""
        target = parameters["target"]
        gateway_config = self.config.get_gateway_config()
        strategy = parameters.get("strategy", gateway_config['default_restart_strategy'])
        backup = parameters.get("backup", True)
        health_check = parameters.get("health_check", True)
        timeout = parameters.get("timeout", gateway_config['default_timeout_seconds'])
        
        # SIMPLIFIED: Build simple context instead of complex intent
        context_parts = []
        if strategy != gateway_config['default_restart_strategy']:
            context_parts.append(f"using {strategy} strategy")
        if backup:
            context_parts.append("create backup before restart")
        if health_check:
            context_parts.append("verify health after restart")
        if timeout != gateway_config['default_timeout_seconds']:
            context_parts.append(f"timeout: {timeout}s")
        
        # Add operational context
        if parameters.get("reason"):
            context_parts.append(f"reason: {parameters['reason']}")
        
        context = ", ".join(context_parts) if context_parts else None
        
        # Use config for priority mapping
        priority = gateway_config['default_priority'] if strategy == gateway_config['default_restart_strategy'] else "HIGH"
        
        try:
            result = await self.gateway_client.restart_service(
                service_name=target,
                context=context,
                priority=priority
            )
            
            return self._convert_gateway_result_to_executor_format(
                result,
                operation_type="restart_service",
                original_parameters=parameters
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to restart service via gateway: {e}")
    
    async def _execute_command_via_gateway(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command via AI Command Gateway"""
        target = parameters["target"]
        command = parameters["command"]
        user = parameters.get("user", "root")
        working_dir = parameters.get("working_dir", "/")
        environment = parameters.get("environment", {})
        gateway_config = self.config.get_gateway_config()
        timeout_param = parameters.get("timeout", gateway_config['default_timeout_seconds'])
        
        # SIMPLIFIED: Simple intent for command execution
        intent = f"execute command: {command}"
        
        # Build simple context with execution parameters
        context_parts = []
        if user != "root":
            context_parts.append(f"as user {user}")
        if working_dir != "/":
            context_parts.append(f"in directory {working_dir}")
        if environment:
            env_str = ", ".join([f"{k}={v}" for k, v in environment.items()])
            context_parts.append(f"with environment: {env_str}")
        if timeout_param != gateway_config['default_timeout_seconds']:
            context_parts.append(f"timeout: {timeout_param}s")
        
        context = ", ".join(context_parts) if context_parts else None
        
        try:
            result = await self.gateway_client.execute_diagnostic_command(
                service_name=target,
                intent=intent,
                context=context,
                priority=gateway_config['default_priority']
            )
            
            return self._convert_gateway_result_to_executor_format(
                result,
                operation_type="execute_command",
                original_parameters=parameters
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to execute command via gateway: {e}")
    
    async def _scale_service_via_gateway(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scale service via AI Command Gateway (limited support)"""
        target = parameters["target"]
        replicas = parameters["replicas"]
        strategy = parameters.get("strategy", "gradual")
        
        # For scaling via gateway, we translate to restart/stop operations
        if replicas == 0:
            intent = "stop the service - scaling to 0 replicas"
            context = f"Service scaling operation: stop {target} (scale to 0)"
        elif replicas == 1:
            intent = "start or restart the service - scaling to 1 replica"
            context = f"Service scaling operation: ensure {target} is running (scale to 1)"
        else:
            # Gateway can't handle multi-replica scaling, but we can provide guidance
            intent = f"restart the service - note: scaling to {replicas} replicas requires orchestration platform"
            context = f"Service scaling limitation: single container cannot scale to {replicas} replicas"
        
        try:
            if replicas == 0:
                # Use diagnostic command to stop
                result = await self.gateway_client.execute_diagnostic_command(
                    service_name=target,
                    intent=intent,
                    context=context,
                    priority="NORMAL"
                )
            else:
                # Use restart for replicas >= 1
                result = await self.gateway_client.restart_service(
                    service_name=target,
                    context=context,
                    priority="NORMAL"
                )
            
            return self._convert_gateway_result_to_executor_format(
                result,
                operation_type="scale_service",
                original_parameters=parameters
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to scale service via gateway: {e}")
    
    async def _health_check_via_gateway(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Health check service via AI Command Gateway"""
        target = parameters["target"]
        gateway_config = self.config.get_gateway_config()
        retries = parameters.get("retries", gateway_config['default_health_retries'])
        default_endpoints = [endpoint.strip() for endpoint in gateway_config['default_health_endpoints'].split(',')]
        endpoints = parameters.get("endpoints", default_endpoints)
        
        # SIMPLIFIED: Build simple context
        context_parts = []
        if retries != gateway_config['default_health_retries']:
            context_parts.append(f"retries: {retries}")
        if endpoints != default_endpoints:
            context_parts.append(f"checking endpoints: {', '.join(endpoints)}")
        
        context = ", ".join(context_parts) if context_parts else None
        
        try:
            # FIX: Use check_service_health instead of health_check
            result = await self.gateway_client.check_service_health(
                service_name=target,
                context=context
            )
            
            return self._convert_gateway_result_to_executor_format(
                result,
                operation_type="health_check",
                original_parameters=parameters
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to health check via gateway: {e}")
    
    def _convert_gateway_result_to_executor_format(
        self, 
        gateway_result: GatewayOperationResult, 
        operation_type: str,
        original_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert AI Command Gateway result to executor result format
        
        Args:
            gateway_result: Result from AI Command Gateway
            operation_type: Type of operation performed
            original_parameters: Original operation parameters
            
        Returns:
            Dict in executor result format
        """
        if gateway_result.success:
            # Build success metadata
            metadata = {
                "target": gateway_result.target_service,
                "operation_type": operation_type,
                "gateway_request_id": gateway_result.gateway_request_id,
                "execution_time_ms": gateway_result.execution_time_ms,
                "command_executed": gateway_result.command_executed,
                "executor": "GatewayExecutor",
                "gateway_metadata": gateway_result.metadata,
                "original_parameters": original_parameters
            }
            
            # Use gateway output or generate success message
            output = gateway_result.output if gateway_result.output else f"Operation '{operation_type}' completed successfully via AI Command Gateway"
            
            return self.build_success_result(output, metadata, 0)
        else:
            # Build error result
            error_msg = gateway_result.error_message or f"Gateway operation failed: {operation_type}"
            
            # Create a structured error with gateway details
            metadata = {
                "target": gateway_result.target_service,
                "operation_type": operation_type,
                "gateway_request_id": gateway_result.gateway_request_id,
                "execution_time_ms": gateway_result.execution_time_ms,
                "command_executed": gateway_result.command_executed,
                "gateway_error": gateway_result.error_message,
                "gateway_metadata": gateway_result.metadata,
                "executor": "GatewayExecutor",
                "original_parameters": original_parameters
            }
            
            return {
                "output": f"Operation '{operation_type}' failed: {error_msg}",
                "metadata": metadata,
                "return_code": -1
            }
    
    def get_operation_timeout(self, operation_name: str, default: int = 60) -> int:
        """Get timeout for specific operation (adjusted for gateway operations)"""
        # Gateway operations may take longer due to AI processing
        timeout_map = {
            "restart_service": 180,  # AI analysis + restart + health check
            "scale_service": 240,    # AI analysis + scaling operations
            "get_logs": 60,          # AI analysis + log retrieval
            "check_resources": 45,   # AI analysis + resource monitoring
            "health_check": 30,      # AI analysis + health verification
            "execute_command": 120   # AI analysis + command execution
        }
        return timeout_map.get(operation_name, default)
    
    def get_environment_limits(self) -> Dict[str, Any]:
        """Get resource limits for gateway environment"""
        return {
            "operation_timeout": self.gateway_client.timeout,
            "max_concurrent_operations": 10,  # Gateway can handle more concurrent operations
            "gateway_url": self.gateway_client.base_url,
            "source_id": self.gateway_client.source_id,
            "ai_powered": True,
            "natural_language_operations": True
        } 