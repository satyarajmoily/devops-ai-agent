"""
Enhanced Docker Executor
Implements Docker-specific infrastructure operations using Python Docker SDK
Eliminates subprocess calls and Docker CLI dependency
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import docker
from docker.errors import DockerException, NotFound, APIError
from .base_executor import BaseExecutor

class DockerExecutor(BaseExecutor):
    """
    Enhanced Docker-specific operation executor using Python Docker SDK
    Implements operations for Docker Compose environments without CLI dependency
    """
    
    def __init__(self, config):
        """Initialize Docker executor with Docker client"""
        super().__init__(config)
        try:
            # Initialize Docker client - will use Docker socket
            self.docker_client = docker.from_env()
            # Test connection
            self.docker_client.ping()
            self.logger.info("Docker client initialized successfully")
        except DockerException as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError(f"Docker daemon not accessible: {e}")
    
    def get_capabilities(self) -> List[str]:
        """Get operations this executor can handle"""
        return [
            "get_logs",
            "check_resources", 
            "restart_service",
            "execute_command",
            "scale_service",
            "health_check"
        ]
    
    async def validate_environment(self) -> Dict[str, Any]:
        """Validate Docker environment is accessible"""
        validation_result = {
            "valid": True,
            "checks": [],
            "errors": []
        }
        
        try:
            # Check Docker daemon accessibility
            self.docker_client.ping()
            validation_result["checks"].append("Docker daemon accessible via SDK")
            
            # Check Docker version
            version_info = self.docker_client.version()
            validation_result["checks"].append(f"Docker version: {version_info.get('Version', 'unknown')}")
            
            # Check if we can list containers (permissions test)
            containers = self.docker_client.containers.list(all=True, limit=1)
            validation_result["checks"].append("Container listing permissions verified")
            
        except DockerException as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Docker validation failed: {e}")
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Environment validation failed: {e}")
        
        return validation_result
    
    async def execute_operation(self, operation_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Docker-specific operation using Docker SDK"""
        self.logger.info(f"Executing Docker operation: {operation_name}")
        
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
                return await self._get_logs(parameters)
            elif operation_name == "check_resources":
                return await self._check_resources(parameters)
            elif operation_name == "restart_service":
                return await self._restart_service(parameters)
            elif operation_name == "execute_command":
                return await self._execute_command(parameters)
            elif operation_name == "scale_service":
                return await self._scale_service(parameters)
            elif operation_name == "health_check":
                return await self._health_check(parameters)
            else:
                raise ValueError(f"Operation '{operation_name}' not implemented in DockerExecutor")
        
        except Exception as e:
            self.logger.error(f"Docker operation '{operation_name}' failed: {e}")
            return self.build_error_result(e, operation_name, parameters)
    
    def _get_container(self, target: str):
        """Get container by name or ID with error handling"""
        try:
            return self.docker_client.containers.get(target)
        except NotFound:
            raise ValueError(f"Container '{target}' not found")
        except DockerException as e:
            raise RuntimeError(f"Failed to access container '{target}': {e}")
    
    async def _get_logs(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get service logs using Docker SDK"""
        target = parameters["target"]
        lines = parameters.get("lines", 100)
        since = parameters.get("since")
        follow = parameters.get("follow", False)
        level = parameters.get("level", "all")
        filter_pattern = parameters.get("filter")
        timestamps = parameters.get("timestamps", True)
        
        container = self._get_container(target)
        
        # Convert since parameter to datetime if provided
        since_dt = None
        if since:
            try:
                if since.endswith(('s', 'm', 'h', 'd')):
                    # Parse relative time (e.g., "1h", "30m")
                    unit = since[-1]
                    value = int(since[:-1])
                    if unit == 's':
                        since_dt = datetime.now() - timedelta(seconds=value)
                    elif unit == 'm':
                        since_dt = datetime.now() - timedelta(minutes=value)
                    elif unit == 'h':
                        since_dt = datetime.now() - timedelta(hours=value)
                    elif unit == 'd':
                        since_dt = datetime.now() - timedelta(days=value)
                else:
                    # Assume ISO format
                    since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            except (ValueError, IndexError):
                self.logger.warning(f"Invalid since parameter: {since}, ignoring")
        
        # Get logs from container
        log_kwargs = {
            'stdout': True,
            'stderr': True,
            'timestamps': timestamps,
            'tail': lines
        }
        
        if since_dt:
            log_kwargs['since'] = since_dt
        if follow:
            log_kwargs['follow'] = True
            log_kwargs['stream'] = True
        
        try:
            if follow:
                # For streaming logs, collect for a short time
                logs = []
                log_stream = container.logs(**log_kwargs)
                for log_line in log_stream:
                    logs.append(log_line.decode('utf-8', errors='ignore'))
                    if len(logs) >= lines:
                        break
                output = '\n'.join(logs)
            else:
                logs = container.logs(**log_kwargs)
                output = logs.decode('utf-8', errors='ignore')
            
            # Apply level filtering if specified
            if level != "all":
                lines_filtered = []
                level_patterns = {
                    "error": ["ERROR", "FATAL", "error", "fatal"],
                    "warn": ["WARN", "WARNING", "warn", "warning"],
                    "info": ["INFO", "info"],
                    "debug": ["DEBUG", "debug"]
                }
                patterns = level_patterns.get(level, [])
                for line in output.split('\n'):
                    if any(pattern in line for pattern in patterns):
                        lines_filtered.append(line)
                output = '\n'.join(lines_filtered)
            
            # Apply custom filter if specified
            if filter_pattern:
                import re
                lines_filtered = []
                for line in output.split('\n'):
                    if re.search(filter_pattern, line):
                        lines_filtered.append(line)
                output = '\n'.join(lines_filtered)
            
            return self.build_success_result(
                output,
                {
                    "target": target,
                    "lines_requested": lines,
                    "level_filter": level,
                    "filter_pattern": filter_pattern,
                    "container_id": container.id[:12],
                    "method": "docker_sdk"
                }
            )
            
        except DockerException as e:
            raise RuntimeError(f"Failed to retrieve logs: {e}")
    
    async def _check_resources(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check Docker container/system resources using Docker SDK"""
        target = parameters["target"]
        metrics = parameters.get("metrics", ["cpu", "memory"])
        format_type = parameters.get("format", "summary")
        
        if target == "system":
            # System-wide Docker resources
            try:
                info = self.docker_client.info()
                df_result = self.docker_client.df()
                
                output = {
                    "system_info": {
                        "containers": info.get("Containers", 0),
                        "containers_running": info.get("ContainersRunning", 0),
                        "containers_stopped": info.get("ContainersStopped", 0),
                        "images": info.get("Images", 0),
                        "server_version": info.get("ServerVersion", "unknown")
                    },
                    "disk_usage": df_result
                }
                
                if format_type == "json":
                    output_str = json.dumps(output, indent=2)
                else:
                    output_str = f"""Docker System Resources:
Containers: {output['system_info']['containers']} (Running: {output['system_info']['containers_running']})
Images: {output['system_info']['images']}
Server Version: {output['system_info']['server_version']}"""
                
            except DockerException as e:
                raise RuntimeError(f"Failed to get system resources: {e}")
        else:
            # Container-specific resources
            container = self._get_container(target)
            
            try:
                # Get container stats (equivalent to docker stats)
                stats = container.stats(stream=False)
                
                # Calculate CPU percentage
                cpu_percent = 0.0
                if 'cpu_stats' in stats and 'precpu_stats' in stats:
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                               stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                  stats['precpu_stats']['system_cpu_usage']
                    if system_delta > 0 and cpu_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * 100.0
                
                # Calculate memory usage
                memory_usage = stats.get('memory_stats', {}).get('usage', 0)
                memory_limit = stats.get('memory_stats', {}).get('limit', 0)
                memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
                
                if format_type == "detailed":
                    # Get additional container info
                    container.reload()
                    output = {
                        "container_info": {
                            "name": container.name,
                            "id": container.id[:12],
                            "status": container.status,
                            "image": container.image.tags[0] if container.image.tags else "unknown"
                        },
                        "resources": {
                            "cpu_percent": round(cpu_percent, 2),
                            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
                            "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
                            "memory_percent": round(memory_percent, 2)
                        },
                        "raw_stats": stats
                    }
                    output_str = json.dumps(output, indent=2)
                else:
                    output_str = f"""Container: {container.name} ({container.id[:12]})
Status: {container.status}
CPU Usage: {cpu_percent:.2f}%
Memory: {memory_usage/1024/1024:.1f}MB / {memory_limit/1024/1024:.1f}MB ({memory_percent:.1f}%)"""
                
            except DockerException as e:
                raise RuntimeError(f"Failed to get container stats: {e}")
        
        return self.build_success_result(
            output_str,
            {
                "target": target,
                "metrics": metrics,
                "format": format_type,
                "method": "docker_sdk"
            }
        )
    
    async def _restart_service(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Restart Docker service using Docker SDK"""
        target = parameters["target"]
        strategy = parameters.get("strategy", "graceful")
        backup = parameters.get("backup", True)
        health_check = parameters.get("health_check", True)
        timeout = parameters.get("timeout", 30)
        
        container = self._get_container(target)
        actions_performed = []
        
        try:
            # Create backup if requested
            if backup:
                backup_tag = f"{target}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                try:
                    backup_image = container.commit(repository=backup_tag)
                    actions_performed.append(f"Created backup: {backup_tag}")
                    self.logger.info(f"Created backup image: {backup_tag}")
                except DockerException as e:
                    self.logger.warning(f"Backup failed: {e}")
                    actions_performed.append(f"Backup failed: {e}")
            
            # Execute restart based on strategy
            if strategy == "graceful":
                container.restart(timeout=timeout)
                actions_performed.append(f"Graceful restart with {timeout}s timeout")
            elif strategy == "force":
                container.kill()
                container.start()
                actions_performed.append("Force restart (kill + start)")
            elif strategy == "rolling":
                # For rolling restart, we'd need docker-compose integration
                # For now, perform graceful restart with longer timeout
                container.restart(timeout=timeout * 2)
                actions_performed.append(f"Rolling restart (graceful with {timeout*2}s timeout)")
            else:
                raise ValueError(f"Unknown restart strategy: {strategy}")
            
            # Wait for container to be running
            await asyncio.sleep(2)
            container.reload()
            
            # Perform health check if requested
            health_status = None
            if health_check:
                await asyncio.sleep(3)  # Additional wait for service startup
                try:
                    container.reload()
                    if container.status == "running":
                        # Check if container has health check configured
                        health_status = container.attrs.get('State', {}).get('Health', {}).get('Status', 'unknown')
                        if health_status == 'unknown':
                            health_status = "running" if container.status == "running" else "unhealthy"
                    else:
                        health_status = "unhealthy"
                    actions_performed.append(f"Health check: {health_status}")
                except DockerException as e:
                    health_status = f"health_check_failed: {e}"
                    actions_performed.append(f"Health check failed: {e}")
            
            success_message = f"Service '{target}' restarted successfully using {strategy} strategy"
            if container.status != "running":
                raise RuntimeError(f"Container not running after restart. Status: {container.status}")
            
            return self.build_success_result(
                success_message,
                {
                    "target": target,
                    "strategy": strategy,
                    "container_id": container.id[:12],
                    "final_status": container.status,
                    "health_status": health_status,
                    "actions_performed": actions_performed,
                    "method": "docker_sdk"
                }
            )
            
        except DockerException as e:
            raise RuntimeError(f"Service restart failed: {e}")
    
    async def _execute_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command in Docker container using Docker SDK"""
        target = parameters["target"]
        command = parameters["command"]
        user = parameters.get("user", "root")
        working_dir = parameters.get("working_dir", "/")
        environment = parameters.get("environment", {})
        timeout_param = parameters.get("timeout", 30)
        
        container = self._get_container(target)
        
        # Prepare execution parameters
        exec_kwargs = {
            'cmd': command,
            'user': user,
            'workdir': working_dir,
            'environment': environment
        }
        
        try:
            # Create and start exec instance
            exec_instance = container.exec_run(**exec_kwargs)
            
            # Get output and return code
            output = exec_instance.output.decode('utf-8', errors='ignore')
            return_code = exec_instance.exit_code
            
            if return_code == 0:
                return self.build_success_result(
                    output,
                    {
                        "target": target,
                        "command": command,
                        "user": user,
                        "working_dir": working_dir,
                        "environment": environment,
                        "container_id": container.id[:12],
                        "method": "docker_sdk"
                    },
                    return_code
                )
            else:
                raise RuntimeError(f"Command failed with exit code {return_code}: {output}")
                
        except DockerException as e:
            raise RuntimeError(f"Command execution failed: {e}")
    
    async def _scale_service(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Scale Docker service (limited implementation for single containers)"""
        target = parameters["target"]
        replicas = parameters["replicas"]
        strategy = parameters.get("strategy", "gradual")
        
        # For single container scaling, we can only start/stop
        # True scaling requires Docker Compose or Swarm
        container = self._get_container(target)
        
        try:
            if replicas == 0:
                # Stop container
                container.stop()
                result_msg = f"Scaled '{target}' to 0 replicas (stopped container)"
            elif replicas == 1:
                # Ensure container is running
                if container.status != "running":
                    container.start()
                result_msg = f"Scaled '{target}' to 1 replica (started container)"
            else:
                # Cannot scale single container beyond 1 replica
                raise ValueError(f"Cannot scale single container '{target}' to {replicas} replicas. Use Docker Compose or Swarm for multi-replica scaling.")
            
            container.reload()
            
            return self.build_success_result(
                result_msg,
                {
                    "target": target,
                    "requested_replicas": replicas,
                    "actual_replicas": 1 if container.status == "running" else 0,
                    "strategy": strategy,
                    "container_status": container.status,
                    "limitation": "Single container scaling only",
                    "method": "docker_sdk"
                }
            )
            
        except DockerException as e:
            raise RuntimeError(f"Service scaling failed: {e}")
    
    async def _health_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Perform health check on Docker service using Docker SDK"""
        target = parameters["target"]
        endpoints = parameters.get("endpoints", ["/health"])
        timeout_param = parameters.get("timeout", 10)
        retries = parameters.get("retries", 3)
        
        container = self._get_container(target)
        health_results = []
        
        try:
            # Get container health from Docker
            container.reload()
            docker_health = container.attrs.get('State', {}).get('Health', {})
            
            if docker_health:
                # Container has built-in health check
                health_results.append({
                    "type": "docker_health_check",
                    "status": docker_health.get('Status', 'unknown'),
                    "failing_streak": docker_health.get('FailingStreak', 0),
                    "log": docker_health.get('Log', [])[-1] if docker_health.get('Log') else None
                })
            
            # Check container status
            health_results.append({
                "type": "container_status",
                "status": "healthy" if container.status == "running" else "unhealthy",
                "container_status": container.status,
                "container_id": container.id[:12]
            })
            
            # Try endpoint checks if container is running and we can get port info
            if container.status == "running":
                ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                
                for endpoint in endpoints:
                    endpoint_result = {
                        "endpoint": endpoint,
                        "type": "endpoint_check",
                        "status": "unknown",
                        "attempts": []
                    }
                    
                    # If we have port mappings, try to check endpoints
                    if ports:
                        for attempt in range(retries):
                            try:
                                # Simple check - try to execute curl inside container
                                exec_result = container.exec_run(
                                    f"curl -f -m {timeout_param} http://localhost{endpoint}",
                                    user="root"
                                )
                                
                                if exec_result.exit_code == 0:
                                    endpoint_result["status"] = "healthy"
                                    endpoint_result["attempts"].append({
                                        "attempt": attempt + 1,
                                        "result": "success",
                                        "response": exec_result.output.decode('utf-8', errors='ignore')[:200]
                                    })
                                    break
                                else:
                                    endpoint_result["attempts"].append({
                                        "attempt": attempt + 1,
                                        "result": "failed",
                                        "error": exec_result.output.decode('utf-8', errors='ignore')[:200]
                                    })
                                    
                            except DockerException as e:
                                endpoint_result["attempts"].append({
                                    "attempt": attempt + 1,
                                    "result": "error",
                                    "error": str(e)[:200]
                                })
                            
                            if attempt < retries - 1:
                                await asyncio.sleep(1)
                    else:
                        endpoint_result["status"] = "skipped"
                        endpoint_result["reason"] = "No port mappings found"
                    
                    health_results.append(endpoint_result)
            
            # Determine overall health
            overall_healthy = all(
                result.get("status") in ["healthy", "running"] 
                for result in health_results 
                if result.get("type") != "endpoint_check" or result.get("status") != "skipped"
            )
            
            return self.build_success_result(
                f"Health check completed for '{target}'. Overall status: {'healthy' if overall_healthy else 'unhealthy'}",
                {
                    "target": target,
                    "container_id": container.id[:12],
                    "overall_healthy": overall_healthy,
                    "health_results": health_results,
                    "endpoints_checked": endpoints,
                    "method": "docker_sdk"
                }
            )
            
        except DockerException as e:
            raise RuntimeError(f"Health check failed: {e}") 