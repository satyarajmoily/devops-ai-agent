from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from agent.core.orchestrator import AgentOrchestrator
from agent.services.docker_service import DockerService

router = APIRouter()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get current status of the agent.
    
    Returns:
        Current status including actions taken
    """
    orchestrator = AgentOrchestrator()
    return orchestrator.get_status()


@router.get("/debug/docker")
async def debug_docker() -> Dict[str, Any]:
    """Debug Docker API connectivity and permissions.
    
    Returns:
        Detailed debug information about Docker connectivity
    """
    docker_service = DockerService()
    debug_info = await docker_service.debug_docker_connectivity()
    system_info = await docker_service.get_system_info()
    
    return {
        "debug_info": debug_info,
        "system_info": system_info
    } 