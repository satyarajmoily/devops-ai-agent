"""Health and status models for the Market Programmer Agent."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class AgentHealthStatus(BaseModel):
    """Basic agent health status response."""
    
    status: str = Field(..., description="Agent health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    agent_active: bool = Field(..., description="Whether agent monitoring is active")


class AgentDetailedStatus(BaseModel):
    """Detailed agent status with monitoring information."""
    
    status: str = Field(..., description="Overall agent status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status check timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Agent uptime in seconds")
    
    # Agent-specific status
    agent_active: bool = Field(..., description="Whether agent monitoring is active")
    last_monitoring_cycle: Optional[datetime] = Field(default=None, description="Last monitoring cycle timestamp")
    monitoring_interval: int = Field(..., description="Monitoring interval in seconds")
    
    # External service connectivity
    target_services: Dict[str, str] = Field(default_factory=dict, description="Target service health status")
    
    # AI/LLM status
    llm_provider: str = Field(..., description="Current LLM provider")
    llm_model: str = Field(..., description="Current LLM model")
    llm_available: bool = Field(..., description="Whether LLM is available")
    
    # Recent activity
    recent_actions: List[str] = Field(default_factory=list, description="Recent agent actions")
    pending_actions: int = Field(default=0, description="Number of pending actions")
    
    # Configuration
    safety_mode: bool = Field(..., description="Whether safety mode is enabled")
    learning_enabled: bool = Field(..., description="Whether learning is enabled")


class MonitoringTarget(BaseModel):
    """Information about a monitoring target."""
    
    name: str = Field(..., description="Target service name")
    url: str = Field(..., description="Target service URL")
    status: str = Field(..., description="Current status")
    last_check: datetime = Field(..., description="Last health check timestamp")
    response_time_ms: Optional[float] = Field(default=None, description="Last response time in milliseconds")
    error_message: Optional[str] = Field(default=None, description="Last error message if any")


class AgentAction(BaseModel):
    """Represents an action taken by the agent."""
    
    action_id: str = Field(..., description="Unique action identifier")
    action_type: str = Field(..., description="Type of action")
    target_service: str = Field(..., description="Target service name")
    description: str = Field(..., description="Action description")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")
    status: str = Field(..., description="Action status")
    result: Optional[str] = Field(default=None, description="Action result")


class ErrorResponse(BaseModel):
    """Error response model for agent operations."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    details: Optional[Dict] = Field(default=None, description="Additional error details")
    service: str = Field(default="market-programmer-agent", description="Service that generated the error")