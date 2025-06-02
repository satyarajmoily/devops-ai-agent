"""
AI Command Gateway Client Service

Provides clean interface for communicating with AI Command Gateway.
Replaces direct Docker operations with natural language API calls.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import httpx

from ..config.settings import get_settings


class GatewayOperationResult(BaseModel):
    """Result of an AI Command Gateway operation."""
    
    success: bool = Field(..., description="Whether operation succeeded")
    operation_type: str = Field(..., description="Type of operation performed")
    target_service: str = Field(..., description="Target service name")
    command_executed: Optional[str] = Field(default=None, description="Docker command that was executed")
    output: Optional[str] = Field(default=None, description="Command output")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    gateway_request_id: Optional[str] = Field(default=None, description="Gateway request ID for tracking")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AICommandGatewayClient:
    """Client for communicating with AI Command Gateway service."""
    
    def __init__(self):
        """Initialize AI Command Gateway client."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Validate gateway configuration at initialization
        if not self.settings.ai_command_gateway_url:
            raise ValueError("AI_COMMAND_GATEWAY_URL is required but not configured")
        
        if not self.settings.ai_command_gateway_source_id:
            raise ValueError("AI_COMMAND_GATEWAY_SOURCE_ID is required but not configured")
        
        self.base_url = self.settings.ai_command_gateway_url.rstrip('/')
        self.timeout = self.settings.ai_command_gateway_timeout
        self.source_id = self.settings.ai_command_gateway_source_id
        
        self.logger.info(
            f"AI Command Gateway client initialized",
            extra={
                "gateway_url": self.base_url,
                "source_id": self.source_id,
                "timeout": self.timeout
            }
        )
    
    async def restart_service(self, service_name: str, context: str = None, priority: str = None) -> GatewayOperationResult:
        """
        Restart a service via AI Command Gateway.
        
        Args:
            service_name: Name of the service to restart
            context: Additional context for the AI (e.g., "High memory usage detected")
            priority: Operation priority (uses config default if None)
            
        Returns:
            GatewayOperationResult with operation outcome
        """
        # Use config default if not specified
        if priority is None:
            priority = self.settings.gateway_default_priority
            
        # SIMPLIFIED: Basic natural language intent only
        intent = "restart the service"
        
        return await self._execute_gateway_operation(
            service_name=service_name,
            intent=intent,
            context=context,
            priority=priority,
            operation_type="restart_service"
        )
    
    async def get_service_logs(self, service_name: str, lines: int = None, level: str = "all", context: str = None) -> GatewayOperationResult:
        """
        Get service logs via AI Command Gateway.
        
        Args:
            service_name: Name of the service
            lines: Number of log lines to retrieve (uses config default if None)
            level: Log level filter (all, error, warn, info, debug)
            context: Additional context for the AI
            
        Returns:
            GatewayOperationResult with log content
        """
        # Use config default if not specified
        if lines is None:
            lines = self.settings.gateway_default_log_lines
            
        # SIMPLIFIED: Basic natural language intent only
        if level == "error":
            intent = "show recent error logs"
        else:
            intent = "show recent logs"
        
        # Build simple context with parameters
        simple_context = f"Requesting {lines} lines"
        if level != "all":
            simple_context += f", {level} level only"
        if context:
            simple_context += f". {context}"
        
        return await self._execute_gateway_operation(
            service_name=service_name,
            intent=intent,
            context=simple_context,
            priority="LOW",
            operation_type="get_logs"
        )
    
    async def check_service_health(self, service_name: str, context: str = None) -> GatewayOperationResult:
        """
        Check service health via AI Command Gateway.
        
        Args:
            service_name: Name of the service
            context: Additional context for the health check
            
        Returns:
            GatewayOperationResult with health status
        """
        # SIMPLIFIED: Basic natural language intent only
        intent = "check if service is healthy"
        
        return await self._execute_gateway_operation(
            service_name=service_name,
            intent=intent,
            context=context,
            priority=self.settings.gateway_default_priority,
            operation_type="health_check"
        )
    
    async def get_service_status(self, service_name: str, context: str = None) -> GatewayOperationResult:
        """
        Get service status via AI Command Gateway.
        
        Args:
            service_name: Name of the service
            context: Additional context for the status check
            
        Returns:
            GatewayOperationResult with service status
        """
        # SIMPLIFIED: Basic natural language intent only
        intent = "check container status"
        
        return await self._execute_gateway_operation(
            service_name=service_name,
            intent=intent,
            context=context,
            priority="LOW",
            operation_type="check_status"
        )
    
    async def get_resource_usage(self, service_name: str, context: str = None) -> GatewayOperationResult:
        """
        Get service resource usage via AI Command Gateway.
        
        Args:
            service_name: Name of the service
            context: Additional context for resource monitoring
            
        Returns:
            GatewayOperationResult with resource usage data
        """
        # SIMPLIFIED: Basic natural language intent only
        intent = "show memory and CPU usage"
        
        return await self._execute_gateway_operation(
            service_name=service_name,
            intent=intent,
            context=context,
            priority="LOW",
            operation_type="check_resources"
        )
    
    async def execute_diagnostic_command(self, service_name: str, intent: str, context: str = None, priority: str = "NORMAL") -> GatewayOperationResult:
        """
        Execute a diagnostic command via AI Command Gateway.
        
        Args:
            service_name: Name of the service
            intent: Natural language description of what to do
            context: Additional context for the operation
            priority: Operation priority
            
        Returns:
            GatewayOperationResult with command execution results
        """
        return await self._execute_gateway_operation(
            service_name=service_name,
            intent=intent,
            context=context,
            priority=priority,
            operation_type="execute_command"
        )
    
    async def _execute_gateway_operation(
        self, 
        service_name: str, 
        intent: str, 
        context: str = None, 
        priority: str = "NORMAL",
        operation_type: str = "unknown"
    ) -> GatewayOperationResult:
        """
        Execute operation via AI Command Gateway API.
        
        Args:
            service_name: Target service name
            intent: Natural language intent
            context: Additional context
            priority: Operation priority
            operation_type: Type of operation for result tracking
            
        Returns:
            GatewayOperationResult with execution outcome
        """
        start_time = datetime.utcnow()
        
        # Build gateway request
        gateway_request = {
            "source_id": self.source_id,
            "target_resource": {
                "name": service_name
            },
            "action_request": {
                "intent": intent,
                "priority": priority
            }
        }
        
        # Add context if provided
        if context:
            gateway_request["action_request"]["context"] = context
        
        self.logger.info(
            f"Executing gateway operation",
            extra={
                "operation_type": operation_type,
                "service_name": service_name,
                "intent": intent,
                "context": context,
                "priority": priority
            }
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/execute-docker-command",
                    json=gateway_request,
                    headers={"Content-Type": "application/json"}
                )
                
                # Handle HTTP errors
                if response.status_code != 200:
                    error_msg = f"Gateway HTTP error {response.status_code}: {response.text}"
                    self.logger.error(
                        f"Gateway operation failed",
                        extra={
                            "operation_type": operation_type,
                            "service_name": service_name,
                            "status_code": response.status_code,
                            "error": error_msg
                        }
                    )
                    
                    return GatewayOperationResult(
                        success=False,
                        operation_type=operation_type,
                        target_service=service_name,
                        error_message=error_msg,
                        execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
                    )
                
                # Parse response
                gateway_response = response.json()
                execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Convert gateway response to our result format
                result = self._convert_gateway_response(
                    gateway_response, 
                    operation_type, 
                    service_name, 
                    execution_time_ms
                )
                
                # Log operation result
                if result.success:
                    self.logger.info(
                        f"Gateway operation completed successfully",
                        extra={
                            "operation_type": operation_type,
                            "service_name": service_name,
                            "request_id": result.gateway_request_id,
                            "execution_time_ms": execution_time_ms
                        }
                    )
                else:
                    self.logger.warning(
                        f"Gateway operation failed",
                        extra={
                            "operation_type": operation_type,
                            "service_name": service_name,
                            "request_id": result.gateway_request_id,
                            "error": result.error_message,
                            "execution_time_ms": execution_time_ms
                        }
                    )
                
                return result
                
        except httpx.TimeoutException:
            error_msg = f"Gateway request timed out after {self.timeout} seconds"
            self.logger.error(
                f"Gateway operation timeout",
                extra={
                    "operation_type": operation_type,
                    "service_name": service_name,
                    "timeout": self.timeout
                }
            )
            
            return GatewayOperationResult(
                success=False,
                operation_type=operation_type,
                target_service=service_name,
                error_message=error_msg,
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
        except httpx.ConnectError:
            error_msg = f"Cannot connect to AI Command Gateway at {self.base_url}"
            self.logger.error(
                f"Gateway connection failed",
                extra={
                    "operation_type": operation_type,
                    "service_name": service_name,
                    "gateway_url": self.base_url,
                    "error": error_msg
                }
            )
            
            # Following project rule: no fallback, escalate to human
            raise RuntimeError(
                f"AI Command Gateway unavailable at {self.base_url} - human intervention required"
            )
            
        except Exception as e:
            error_msg = f"Gateway operation failed: {str(e)}"
            self.logger.error(
                f"Gateway operation error",
                extra={
                    "operation_type": operation_type,
                    "service_name": service_name,
                    "error": str(e)
                }
            )
            
            return GatewayOperationResult(
                success=False,
                operation_type=operation_type,
                target_service=service_name,
                error_message=error_msg,
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )
    
    def _convert_gateway_response(
        self, 
        gateway_response: Dict[str, Any], 
        operation_type: str, 
        service_name: str, 
        execution_time_ms: float
    ) -> GatewayOperationResult:
        """
        Convert AI Command Gateway response to our internal result format.
        
        Args:
            gateway_response: Raw response from gateway
            operation_type: Type of operation
            service_name: Target service name
            execution_time_ms: Total execution time
            
        Returns:
            GatewayOperationResult with converted data
        """
        overall_status = gateway_response.get("overall_status", "UNKNOWN")
        success = overall_status == "COMPLETED_SUCCESS"
        
        # Extract execution details
        execution_details = gateway_response.get("execution_details", {})
        command_executed = execution_details.get("command")
        
        # Extract output from execution result
        execution_result = execution_details.get("execution_result", {})
        output = execution_result.get("stdout", "")
        stderr = execution_result.get("stderr", "")
        
        # Combine stdout and stderr for output
        if output and stderr:
            combined_output = f"STDOUT:\n{output}\n\nSTDERR:\n{stderr}"
        elif output:
            combined_output = output
        elif stderr:
            combined_output = stderr
        else:
            combined_output = None
        
        # Extract error information
        error_message = None
        if not success:
            error_details = gateway_response.get("error_details", {})
            if error_details:
                error_message = error_details.get("error_message", "Unknown error")
            elif stderr:
                error_message = stderr
            else:
                error_message = f"Operation failed with status: {overall_status}"
        
        # Build metadata
        metadata = {
            "overall_status": overall_status,
            "gateway_timestamp": gateway_response.get("timestamp_processed_utc"),
            "execution_result_status": execution_result.get("status"),
            "exit_code": execution_result.get("exit_code")
        }
        
        return GatewayOperationResult(
            success=success,
            operation_type=operation_type,
            target_service=service_name,
            command_executed=command_executed,
            output=combined_output,
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            gateway_request_id=gateway_response.get("request_id"),
            metadata=metadata
        )
    
    async def health_check(self) -> bool:
        """
        Check if AI Command Gateway is available.
        
        Returns:
            True if gateway is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Gateway health check failed: {e}")
            return False


# Global instance for dependency injection
_gateway_client: Optional[AICommandGatewayClient] = None


def get_gateway_client() -> AICommandGatewayClient:
    """Get AI Command Gateway client instance (singleton pattern)."""
    global _gateway_client
    if _gateway_client is None:
        _gateway_client = AICommandGatewayClient()
    return _gateway_client 