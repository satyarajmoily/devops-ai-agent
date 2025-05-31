"""
Generic Executor
Fallback executor for environments without specific implementations
"""

import asyncio
from typing import Dict, Any, List
from .base_executor import BaseExecutor

class GenericExecutor(BaseExecutor):
    """
    Generic operation executor
    Provides basic implementations for environments without specific executors
    """
    
    def get_capabilities(self) -> List[str]:
        """Get operations this executor can handle"""
        return [
            "get_logs",
            "check_resources",
            "health_check"
        ]
    
    async def validate_environment(self) -> Dict[str, Any]:
        """Basic environment validation"""
        validation_result = {
            "valid": True,
            "checks": ["Generic executor available"],
            "errors": [],
            "warnings": ["Using generic executor - limited functionality available"]
        }
        
        return validation_result
    
    async def execute_operation(self, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute operation with generic implementation"""
        self.logger.info(f"Executing generic operation: {operation_name}")
        
        try:
            # Check safety restrictions
            safety_check = await self.check_safety_restrictions(operation_name, parameters)
            if not safety_check["allowed"]:
                raise ValueError(f"Operation blocked by safety restrictions: {safety_check['restrictions']}")
            
            # Route to specific operation handler
            if operation_name == "get_logs":
                return await self._get_logs(parameters)
            elif operation_name == "check_resources":
                return await self._check_resources(parameters)
            elif operation_name == "health_check":
                return await self._health_check(parameters)
            else:
                raise ValueError(f"Operation '{operation_name}' not implemented in GenericExecutor")
        
        except Exception as e:
            self.logger.error(f"Generic operation '{operation_name}' failed: {e}")
            return self.build_error_result(e, operation_name, parameters)
    
    async def _get_logs(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generic log retrieval - placeholder implementation"""
        target = parameters["target"]
        lines = parameters.get("lines", 100)
        
        # This is a placeholder - in a real implementation, this would
        # attempt to find and read log files or use system logging
        message = f"Generic log retrieval for '{target}' (last {lines} lines)"
        
        return self.build_success_result(
            f"Log retrieval not implemented for environment type: {self.environment_type}\n"
            f"Target: {target}, Lines: {lines}",
            {
                "target": target,
                "lines_requested": lines,
                "method": "generic_placeholder",
                "warning": "This is a placeholder implementation"
            }
        )
    
    async def _check_resources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generic resource checking - basic system commands"""
        target = parameters["target"]
        metrics = parameters.get("metrics", ["cpu", "memory"])
        
        try:
            # Try basic system commands
            commands = []
            if "cpu" in metrics:
                commands.append("top -bn1 | head -5")
            if "memory" in metrics:
                commands.append("free -h")
            if "disk" in metrics:
                commands.append("df -h")
            
            results = []
            for command in commands:
                result = await self._run_command(command, timeout=10)
                results.append(f"$ {command}\n{result['output']}")
            
            output = "\n\n".join(results)
            
            return self.build_success_result(
                output,
                {
                    "target": target,
                    "metrics": metrics,
                    "method": "generic_system_commands",
                    "commands_executed": commands
                }
            )
            
        except Exception as e:
            return self.build_success_result(
                f"Resource check partially failed: {e}\nTarget: {target}",
                {
                    "target": target,
                    "metrics": metrics,
                    "error": str(e),
                    "method": "generic_fallback"
                }
            )
    
    async def _health_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generic health check - basic connectivity"""
        target = parameters["target"]
        endpoints = parameters.get("endpoints", ["/health"])
        
        # For generic executor, we can only do basic checks
        health_results = []
        
        for endpoint in endpoints:
            # This is a placeholder - real implementation would
            # attempt HTTP requests or other connectivity checks
            health_results.append({
                "endpoint": endpoint,
                "status": "unknown",
                "method": "generic_placeholder"
            })
        
        return self.build_success_result(
            f"Generic health check for '{target}' completed",
            {
                "target": target,
                "overall_healthy": None,
                "endpoint_results": health_results,
                "warning": "Generic health check has limited functionality"
            }
        )
    
    async def _run_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Run basic shell command"""
        self.logger.debug(f"Executing generic command: {command}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            output = stdout.decode() + stderr.decode()
            return {
                "output": output.strip(),
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            return {
                "output": f"Command timed out after {timeout} seconds",
                "return_code": -1
            }
        except Exception as e:
            return {
                "output": f"Command execution failed: {e}",
                "return_code": -1
            } 