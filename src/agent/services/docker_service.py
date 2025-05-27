"""Docker service management for container operations."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import docker
from docker.errors import DockerException, APIError, NotFound
from pydantic import BaseModel, Field
import time
import requests

from agent.config.settings import get_settings


class ContainerInfo(BaseModel):
    """Container information model."""
    
    id: str = Field(..., description="Container ID")
    name: str = Field(..., description="Container name")
    status: str = Field(..., description="Container status")
    image: str = Field(..., description="Container image")
    created: datetime = Field(..., description="Creation time")
    started: Optional[datetime] = Field(default=None, description="Start time")
    ports: Dict[str, Any] = Field(default_factory=dict, description="Port mappings")
    labels: Dict[str, str] = Field(default_factory=dict, description="Container labels")
    health: Optional[str] = Field(default=None, description="Health status")


class ServiceRestartResult(BaseModel):
    """Result of service restart operation."""
    
    success: bool = Field(..., description="Whether restart was successful")
    service_name: str = Field(..., description="Name of the service")
    container_id: Optional[str] = Field(default=None, description="Container ID")
    action_taken: str = Field(..., description="Action that was performed")
    duration_seconds: float = Field(..., description="Time taken for operation")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    validation_result: Optional[Dict] = Field(default=None, description="Post-restart validation")


class DockerServiceManager:
    """Manager for Docker container operations."""
    
    def __init__(self):
        """Initialize Docker service manager."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self._docker_client: Optional[docker.DockerClient] = None
        
        # Configure docker client
        self._initialize_docker_client()
    
    def _initialize_docker_client(self):
        """Initialize Docker client with error handling."""
        try:
            self._docker_client = docker.from_env()
            # Test connection
            self._docker_client.ping()
            self.logger.info("Docker client initialized successfully")
        except DockerException as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            self._docker_client = None
    
    def is_available(self) -> bool:
        """Check if Docker service is available.
        
        Returns:
            True if Docker is available and accessible
        """
        if not self._docker_client:
            return False
        
        try:
            self._docker_client.ping()
            return True
        except DockerException:
            return False
    
    async def get_container_info(self, container_name: str) -> Optional[ContainerInfo]:
        """Get information about a specific container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Container information or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            container = self._docker_client.containers.get(container_name)
            
            # Parse container information
            created_time = datetime.fromisoformat(container.attrs['Created'].replace('Z', '+00:00'))
            started_time = None
            
            if container.attrs['State']['StartedAt'] != '0001-01-01T00:00:00Z':
                started_time = datetime.fromisoformat(
                    container.attrs['State']['StartedAt'].replace('Z', '+00:00')
                )
            
            # Get health status if available
            health_status = None
            if 'Health' in container.attrs['State']:
                health_status = container.attrs['State']['Health']['Status']
            
            return ContainerInfo(
                id=container.id,
                name=container.name,
                status=container.status,
                image=container.image.tags[0] if container.image.tags else container.image.id,
                created=created_time,
                started=started_time,
                ports=container.attrs['NetworkSettings']['Ports'] or {},
                labels=container.labels or {},
                health=health_status
            )
            
        except NotFound:
            self.logger.warning(f"Container {container_name} not found")
            return None
        except DockerException as e:
            self.logger.error(f"Error getting container info for {container_name}: {e}")
            return None
    
    async def list_containers(self, service_filter: Optional[str] = None) -> List[ContainerInfo]:
        """List all containers, optionally filtered by service.
        
        Args:
            service_filter: Optional service name filter
            
        Returns:
            List of container information
        """
        if not self.is_available():
            return []
        
        try:
            containers = self._docker_client.containers.list(all=True)
            container_info = []
            
            for container in containers:
                # Apply service filter if specified
                if service_filter:
                    service_label = container.labels.get('com.docker.compose.service', '')
                    if service_filter not in service_label:
                        continue
                
                info = await self.get_container_info(container.name)
                if info:
                    container_info.append(info)
            
            return container_info
            
        except DockerException as e:
            self.logger.error(f"Error listing containers: {e}")
            return []
    
    async def restart_container(self, container_name: str) -> bool:
        """Restart a Docker container.
        
        Args:
            container_name: Name of the container to restart
            
        Returns:
            True if restart successful, False otherwise
        """
        if not self.is_available():
            self.logger.error("Docker client not available for restart operation")
            return False
        
        self.logger.info(f"Attempting to restart container: {container_name}")
        
        try:
            # First, try to find the container
            try:
                container = self._docker_client.containers.get(container_name)
                self.logger.info(f"Found container {container_name} with ID: {container.id[:12]}")
                self.logger.info(f"Current container status: {container.status}")
            except NotFound as e:
                self.logger.error(f"Container '{container_name}' not found: {str(e)}")
                return False
            except APIError as e:
                self.logger.error(f"Docker API error finding container '{container_name}': {str(e)}")
                return False
            
            # Attempt restart
            try:
                self.logger.info(f"Restarting container {container_name}...")
                container.restart(timeout=30)
                
                # Wait a moment and check status
                time.sleep(2)
                
                # Refresh container status
                container.reload()
                new_status = container.status
                self.logger.info(f"Container {container_name} restart completed. New status: {new_status}")
                
                if new_status == "running":
                    self.logger.info(f"Successfully restarted container: {container_name}")
                    return True
                else:
                    self.logger.warning(f"Container {container_name} restarted but status is: {new_status}")
                    return False
                    
            except APIError as e:
                self.logger.error(f"Docker API error restarting container '{container_name}': {str(e)}")
                return False
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error restarting container '{container_name}': {str(e)}")
                return False
            except Exception as e:
                self.logger.error(f"Unexpected error restarting container '{container_name}': {type(e).__name__}: {str(e)}")
                return False
                
        except DockerException as e:
            self.logger.error(f"General Docker error during restart of '{container_name}': {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in restart_container for '{container_name}': {type(e).__name__}: {str(e)}")
            return False
    
    async def _wait_for_container_running(self, container, timeout: int = 30):
        """Wait for container to reach running state.
        
        Args:
            container: Docker container object
            timeout: Maximum time to wait
        """
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            try:
                container.reload()
                if container.status == 'running':
                    self.logger.info(f"Container {container.name} is running")
                    return
                
                await asyncio.sleep(1)
                
            except DockerException as e:
                self.logger.warning(f"Error checking container status: {e}")
                await asyncio.sleep(1)
        
        raise TimeoutError(f"Container {container.name} did not start within {timeout} seconds")
    
    async def _validate_service_restart(self, service_name: str) -> Dict:
        """Validate that service restart was successful.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Validation result dictionary
        """
        validation = {
            "container_running": False,
            "health_check_passed": False,
            "response_time_ms": None,
            "error_message": None
        }
        
        try:
            # Check container status
            container_info = await self.get_container_info(service_name)
            if container_info and container_info.status == 'running':
                validation["container_running"] = True
            
            # Check health if service exposes health endpoint
            if service_name == "market-predictor":
                validation.update(await self._check_service_health("http://localhost:8000/health"))
            elif service_name == "devops-ai-agent":
                validation.update(await self._check_service_health("http://localhost:8001/health"))
            
        except Exception as e:
            validation["error_message"] = str(e)
        
        return validation
    
    async def _check_service_health(self, health_url: str) -> Dict:
        """Check service health endpoint.
        
        Args:
            health_url: URL of health endpoint
            
        Returns:
            Health check result
        """
        import aiohttp
        import time
        
        health_result = {
            "health_check_passed": False,
            "response_time_ms": None
        }
        
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = (time.time() - start_time) * 1000
                    health_result["response_time_ms"] = round(response_time, 2)
                    
                    if response.status == 200:
                        health_result["health_check_passed"] = True
                    
        except Exception as e:
            health_result["error_message"] = str(e)
        
        return health_result
    
    async def get_service_logs(self, service_name: str, lines: int = 100) -> Optional[str]:
        """Get recent logs from a service container.
        
        Args:
            service_name: Name of the service
            lines: Number of log lines to retrieve
            
        Returns:
            Log content or None if error
        """
        if not self.is_available():
            return None
        
        try:
            # Find container by service name
            container_names = [
                f"autonomous-trading-builder_{service_name}_1",
                service_name,
                f"autonomoustradingbuilder_{service_name}_1",
                f"{service_name}_1"
            ]
            
            for name in container_names:
                try:
                    container = self._docker_client.containers.get(name)
                    logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
                    return logs
                except NotFound:
                    continue
            
            self.logger.warning(f"No container found for service {service_name}")
            return None
            
        except DockerException as e:
            self.logger.error(f"Error getting logs for service {service_name}: {e}")
            return None
    
    async def get_system_info(self) -> Dict:
        """Get Docker system information.
        
        Returns:
            System information dictionary
        """
        if not self.is_available():
            return {"available": False, "error": "Docker client not available"}
        
        try:
            info = self._docker_client.info()
            version = self._docker_client.version()
            
            return {
                "available": True,
                "version": version.get("Version", "unknown"),
                "api_version": version.get("ApiVersion", "unknown"),
                "containers_running": info.get("ContainersRunning", 0),
                "containers_paused": info.get("ContainersPaused", 0),
                "containers_stopped": info.get("ContainersStopped", 0),
                "images": info.get("Images", 0),
                "server_version": info.get("ServerVersion", "unknown")
            }
            
        except DockerException as e:
            return {"available": False, "error": str(e)}

    async def debug_docker_connectivity(self) -> Dict:
        """Debug Docker API connectivity and permissions.
        
        Returns:
            Detailed debug information about Docker connectivity
        """
        debug_info = {
            "docker_client_available": False,
            "socket_accessible": False,
            "container_list_accessible": False,
            "ping_successful": False,
            "containers_found": 0,
            "container_names": [],
            "our_container_id": None,
            "errors": []
        }
        
        try:
            # Test basic client availability
            if self._docker_client:
                debug_info["docker_client_available"] = True
                self.logger.info("Docker client is available")
                
                # Test ping
                self._docker_client.ping()
                debug_info["ping_successful"] = True
                self.logger.info("Docker ping successful")
                
                # Test container listing
                containers = self._docker_client.containers.list(all=True)
                debug_info["container_list_accessible"] = True
                debug_info["containers_found"] = len(containers)
                debug_info["container_names"] = [c.name for c in containers]
                self.logger.info(f"Found {len(containers)} containers: {[c.name for c in containers]}")
                
                # Try to find our own container
                try:
                    our_container = self._docker_client.containers.get("devops-ai-agent")
                    debug_info["our_container_id"] = our_container.id
                    self.logger.info(f"Found our own container: {our_container.id}")
                except NotFound:
                    debug_info["errors"].append("Could not find our own container")
                
                # Test specific service containers
                service_tests = {}
                for service in ["market-predictor", "devops-ai-agent", "prometheus", "alertmanager"]:
                    try:
                        container = self._docker_client.containers.get(service)
                        service_tests[service] = {
                            "found": True,
                            "status": container.status,
                            "id": container.id
                        }
                    except NotFound:
                        service_tests[service] = {"found": False, "error": "Container not found"}
                
                debug_info["service_container_tests"] = service_tests
                
        except DockerException as e:
            error_msg = f"Docker API error: {str(e)}"
            debug_info["errors"].append(error_msg)
            self.logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during Docker debug: {str(e)}"
            debug_info["errors"].append(error_msg)
            self.logger.error(error_msg)
        
        return debug_info 

    async def restart_service(self, service_name: str, timeout_seconds: int = 60) -> ServiceRestartResult:
        """Restart a service container.
        
        Args:
            service_name: Name of the service to restart
            timeout_seconds: Maximum time to wait for restart
            
        Returns:
            ServiceRestartResult with restart outcome
        """
        start_time = time.time()
        
        if not self.is_available():
            return ServiceRestartResult(
                success=False,
                service_name=service_name,
                action_taken="check_docker_availability",
                duration_seconds=time.time() - start_time,
                error_message="Docker client not available"
            )
        
        self.logger.info(f"Attempting to restart service: {service_name}")
        
        try:
            # Try to restart using the container name directly
            restart_success = await self.restart_container(service_name)
            
            if restart_success:
                # Validate the restart
                validation_result = await self._validate_service_restart(service_name)
                
                return ServiceRestartResult(
                    success=True,
                    service_name=service_name,
                    action_taken="restart_container",
                    duration_seconds=time.time() - start_time,
                    validation_result=validation_result
                )
            else:
                return ServiceRestartResult(
                    success=False,
                    service_name=service_name,
                    action_taken="restart_container",
                    duration_seconds=time.time() - start_time,
                    error_message="Container restart failed"
                )
                
        except Exception as e:
            self.logger.error(f"Error restarting service {service_name}: {str(e)}")
            return ServiceRestartResult(
                success=False,
                service_name=service_name,
                action_taken="restart_service",
                duration_seconds=time.time() - start_time,
                error_message=str(e)
            ) 