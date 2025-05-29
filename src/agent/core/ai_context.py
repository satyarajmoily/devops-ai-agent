"""AI-driven context gathering for comprehensive system analysis."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import aiohttp
import docker
from docker.errors import DockerException

from agent.config.settings import get_settings


class AIContextGatherer:
    """Gathers comprehensive context for AI analysis without hardcoded patterns."""
    
    def __init__(self):
        """Initialize context gatherer."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.docker_client = None
        self._initialize_docker()
    
    def _initialize_docker(self):
        """Initialize Docker client."""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
        except DockerException:
            self.docker_client = None
    
    async def gather_complete_context(self, alert_data: Dict) -> Dict:
        """Gather comprehensive context for AI analysis.
        
        Args:
            alert_data: Original alert data from webhook
            
        Returns:
            Complete context dictionary for AI analysis
        """
        self.logger.info("Gathering comprehensive context for AI analysis...")
        
        context = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_details": alert_data,
            "system_state": await self._get_system_state(),
            "docker_environment": await self._get_docker_environment(),
            "service_status": await self._get_service_status(),
            "infrastructure_topology": await self._get_infrastructure_topology(),
            "recent_events": await self._get_recent_events(),
            "resource_utilization": await self._get_resource_utilization(),
            "network_connectivity": await self._get_network_connectivity(),
            "logs_analysis": await self._get_logs_analysis(),
            "compose_configuration": await self._get_compose_configuration(),
            "monitoring_metrics": await self._get_monitoring_metrics()
        }
        
        self.logger.info(f"Context gathering complete. Collected {len(context)} categories of information.")
        return context
    
    async def _get_system_state(self) -> Dict:
        """Get overall system state."""
        try:
            system_info = {
                "docker_available": False,
                "docker_version": None,
                "host_info": {},
                "agent_status": "running"
            }
            
            if self.docker_client:
                try:
                    version_info = self.docker_client.version()
                    system_info.update({
                        "docker_available": True,
                        "docker_version": version_info.get("Version"),
                        "docker_api_version": version_info.get("ApiVersion"),
                        "host_info": self.docker_client.info()
                    })
                except DockerException as e:
                    system_info["docker_error"] = str(e)
            
            return system_info
            
        except Exception as e:
            self.logger.error(f"Error getting system state: {e}")
            return {"error": str(e)}
    
    async def _get_docker_environment(self) -> Dict:
        """Get comprehensive Docker environment information."""
        try:
            if not self.docker_client:
                return {"available": False, "error": "Docker client not available"}
            
            containers = self.docker_client.containers.list(all=True)
            images = self.docker_client.images.list()
            networks = self.docker_client.networks.list()
            volumes = self.docker_client.volumes.list()
            
            environment = {
                "available": True,
                "containers": {
                    "total": len(containers),
                    "running": len([c for c in containers if c.status == "running"]),
                    "stopped": len([c for c in containers if c.status in ["stopped", "exited"]]),
                    "details": []
                },
                "images": {
                    "total": len(images),
                    "details": [{"id": img.id[:12], "tags": img.tags} for img in images]
                },
                "networks": {
                    "total": len(networks),
                    "details": [{"id": net.id[:12], "name": net.name} for net in networks]
                },
                "volumes": {
                    "total": len(volumes),
                    "details": [{"name": vol.name} for vol in volumes]
                }
            }
            
            # Detailed container information
            for container in containers:
                try:
                    container_detail = {
                        "id": container.id[:12],
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                        "status": container.status,
                        "created": container.attrs.get("Created"),
                        "started_at": container.attrs.get("State", {}).get("StartedAt"),
                        "ports": container.attrs.get("NetworkSettings", {}).get("Ports", {}),
                        "labels": container.labels,
                        "compose_service": container.labels.get("com.docker.compose.service"),
                        "health_status": container.attrs.get("State", {}).get("Health", {}).get("Status"),
                        "restart_count": container.attrs.get("RestartCount", 0)
                    }
                    environment["containers"]["details"].append(container_detail)
                except Exception as e:
                    self.logger.warning(f"Error getting details for container {container.name}: {e}")
            
            return environment
            
        except Exception as e:
            self.logger.error(f"Error getting Docker environment: {e}")
            return {"available": False, "error": str(e)}
    
    async def _get_service_status(self) -> Dict:
        """Check status of known services."""
        services = {
            "market-predictor": {"url": "http://localhost:8000", "health_path": "/health"},
            "devops-ai-agent": {"url": "http://localhost:8001", "health_path": "/health"},
            "prometheus": {"url": "http://localhost:9090", "health_path": "/-/healthy"},
            "alertmanager": {"url": "http://localhost:9093", "health_path": "/-/healthy"}
        }
        
        service_status = {}
        
        for service_name, config in services.items():
            try:
                status = await self._check_service_health(config["url"], config["health_path"])
                service_status[service_name] = status
            except Exception as e:
                service_status[service_name] = {
                    "available": False,
                    "error": str(e),
                    "response_time_ms": None
                }
        
        return service_status
    
    async def _check_service_health(self, base_url: str, health_path: str) -> Dict:
        """Check health of a specific service."""
        import time
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}{health_path}", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    result = {
                        "available": response.status == 200,
                        "status_code": response.status,
                        "response_time_ms": round(response_time, 2)
                    }
                    
                    if response.status == 200:
                        try:
                            result["response_data"] = await response.json()
                        except:
                            result["response_data"] = await response.text()
                    
                    return result
                    
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000
            }
    
    async def _get_infrastructure_topology(self) -> Dict:
        """Get infrastructure topology and relationships."""
        topology = {
            "compose_project": "autonomous-trading-builder",
            "expected_services": [
                "market-predictor",
                "devops-ai-agent", 
                "prometheus",
                "alertmanager",
                "grafana"
            ],
            "service_dependencies": {
                "market-predictor": {"dependencies": [], "dependents": ["devops-ai-agent", "prometheus"]},
                "devops-ai-agent": {"dependencies": ["market-predictor"], "dependents": []},
                "prometheus": {"dependencies": ["market-predictor", "devops-ai-agent"], "dependents": ["alertmanager"]},
                "alertmanager": {"dependencies": ["prometheus"], "dependents": ["devops-ai-agent"]}
            },
            "network_topology": await self._get_network_topology(),
            "volume_mappings": await self._get_volume_mappings()
        }
        
        return topology
    
    async def _get_network_topology(self) -> Dict:
        """Get Docker network topology."""
        try:
            if not self.docker_client:
                return {"error": "Docker not available"}
            
            networks = self.docker_client.networks.list()
            network_info = {}
            
            for network in networks:
                containers_in_network = []
                for container_id, container_info in network.attrs.get("Containers", {}).items():
                    containers_in_network.append({
                        "id": container_id[:12],
                        "name": container_info.get("Name"),
                        "ipv4_address": container_info.get("IPv4Address")
                    })
                
                network_info[network.name] = {
                    "id": network.id[:12],
                    "driver": network.attrs.get("Driver"),
                    "scope": network.attrs.get("Scope"),
                    "containers": containers_in_network
                }
            
            return network_info
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_volume_mappings(self) -> Dict:
        """Get Docker volume mappings."""
        try:
            if not self.docker_client:
                return {"error": "Docker not available"}
            
            volumes = self.docker_client.volumes.list()
            volume_info = {}
            
            for volume in volumes:
                volume_info[volume.name] = {
                    "driver": volume.attrs.get("Driver"),
                    "mountpoint": volume.attrs.get("Mountpoint"),
                    "created": volume.attrs.get("CreatedAt"),
                    "labels": volume.attrs.get("Labels", {})
                }
            
            return volume_info
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_recent_events(self) -> Dict:
        """Get recent Docker events."""
        try:
            if not self.docker_client:
                return {"error": "Docker not available"}
            
            # Get events from last 10 minutes with timeout
            since = datetime.utcnow() - timedelta(minutes=10)
            
            # Use asyncio to prevent blocking on Docker API calls
            loop = asyncio.get_event_loop()
            events = await loop.run_in_executor(
                None, 
                lambda: list(self.docker_client.events(since=since, decode=True, until=datetime.utcnow()))
            )
            
            return {
                "total_events": len(events),
                "events": events[-20:] if len(events) > 20 else events  # Last 20 events
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_resource_utilization(self) -> Dict:
        """Get resource utilization information."""
        try:
            if not self.docker_client:
                return {"error": "Docker not available"}
            
            # Use executor to prevent blocking
            loop = asyncio.get_event_loop()
            system_info = await loop.run_in_executor(None, self.docker_client.info)
            
            resource_info = {
                "memory": {
                    "total": system_info.get("MemTotal"),
                    "available": system_info.get("MemTotal") - system_info.get("MemTotal", 0)  # Simplified
                },
                "containers_resource_usage": {}
            }
            
            # Get container resource usage with timeout
            containers = await loop.run_in_executor(None, self.docker_client.containers.list)
            for container in containers:
                try:
                    # Skip stats collection to prevent hanging - too expensive
                    resource_info["containers_resource_usage"][container.name] = {
                        "status": container.status,
                        "stats_skipped": "Performance optimization"
                    }
                except Exception:
                    # Skip if stats not available
                    pass
            
            return resource_info
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_network_connectivity(self) -> Dict:
        """Test network connectivity between services."""
        connectivity = {}
        
        # Test basic connectivity
        services_to_test = [
            ("market-predictor", "http://localhost:8000/health"),
            ("devops-ai-agent", "http://localhost:8001/health"),
            ("prometheus", "http://localhost:9090/-/healthy"),
            ("alertmanager", "http://localhost:9093/-/healthy")
        ]
        
        for service_name, url in services_to_test:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=2)) as response:
                        connectivity[service_name] = {
                            "reachable": True,
                            "status_code": response.status,
                            "response_time_ms": 0  # Will be calculated properly
                        }
            except Exception as e:
                connectivity[service_name] = {
                    "reachable": False,
                    "error": str(e)
                }
        
        return connectivity
    
    async def _get_logs_analysis(self) -> Dict:
        """Get recent logs from services for analysis."""
        logs = {}
        
        if not self.docker_client:
            return {"error": "Docker not available"}
        
        try:
            containers = self.docker_client.containers.list(all=True)
            
            for container in containers:
                service_name = container.labels.get("com.docker.compose.service", container.name)
                try:
                    # Get last 50 lines of logs
                    log_lines = container.logs(tail=50, timestamps=True).decode('utf-8')
                    logs[service_name] = {
                        "container_name": container.name,
                        "status": container.status,
                        "log_lines": log_lines.split('\n')[-50:] if log_lines else [],
                        "log_length": len(log_lines.split('\n')) if log_lines else 0
                    }
                except Exception as e:
                    logs[service_name] = {"error": str(e)}
            
            return logs
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_compose_configuration(self) -> Dict:
        """Get Docker Compose configuration information."""
        try:
            # Check if compose files exist
            compose_files = [
                "/Users/satyarajmoily/AutonomousTradingBuilder/docker-compose.yml",
                "/Users/satyarajmoily/AutonomousTradingBuilder/infrastructure/docker-compose.yml"
            ]
            
            compose_info = {
                "files_found": [],
                "services_defined": [],
                "networks_defined": [],
                "volumes_defined": []
            }
            
            import os
            for file_path in compose_files:
                if os.path.exists(file_path):
                    compose_info["files_found"].append(file_path)
                    
                    # Try to read and parse basic info
                    try:
                        # Try to import yaml, fall back gracefully if not available
                        try:
                            import yaml
                        except ImportError:
                            self.logger.warning("PyYAML not available, skipping compose file parsing")
                            compose_info[f"parse_error_{file_path}"] = "PyYAML not available"
                            continue
                            
                        with open(file_path, 'r') as f:
                            compose_data = yaml.safe_load(f)
                            
                        if 'services' in compose_data:
                            compose_info["services_defined"].extend(list(compose_data['services'].keys()))
                        if 'networks' in compose_data:
                            compose_info["networks_defined"].extend(list(compose_data['networks'].keys()))
                        if 'volumes' in compose_data:
                            compose_info["volumes_defined"].extend(list(compose_data['volumes'].keys()))
                            
                    except Exception as e:
                        compose_info[f"parse_error_{file_path}"] = str(e)
            
            return compose_info
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _get_monitoring_metrics(self) -> Dict:
        """Get current monitoring metrics if available."""
        try:
            metrics = {}
            
            # Try to get Prometheus metrics
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:9090/api/v1/query?query=up", 
                                         timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            metrics["prometheus_up_metrics"] = data.get("data", {}).get("result", [])
            except Exception as e:
                metrics["prometheus_error"] = str(e)
            
            # Try to get Alertmanager status
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://localhost:9093/api/v1/status", 
                                         timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            data = await response.json()
                            metrics["alertmanager_status"] = data.get("data", {})
            except Exception as e:
                metrics["alertmanager_error"] = str(e)
            
            return metrics
            
        except Exception as e:
            return {"error": str(e)} 