"""Main FastAPI application for DevOps AI Agent."""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.config.settings import get_settings
from agent.core.monitoring import MonitoringOrchestrator
from agent.models.health import AgentDetailedStatus, AgentHealthStatus
from agent.models.webhook import AlertmanagerWebhook, WebhookResponse

# Global variables to track application state
app_start_time = time.time()
monitoring_orchestrator: MonitoringOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    global monitoring_orchestrator
    
    settings = get_settings()
    print(f"🤖 Starting {settings.service_name} v{settings.service_version}")
    print(f"🌍 Environment: {settings.environment}")
    print(f"📡 API will be available at http://{settings.api_host}:{settings.api_port}")
    
    # Initialize monitoring orchestrator
    monitoring_orchestrator = MonitoringOrchestrator()
    
    # Initialize agent in alert-driven mode (no continuous polling)
    print("🔒 Agent initialized in alert-driven mode")
    print("📡 Waiting for alerts from Prometheus/Alertmanager at /webhook/alerts")
    print("🛠️  Manual monitoring available via /monitoring/cycle")
    
    # Note: Continuous polling has been disabled in favor of event-driven alerts
    
    yield
    
    # Cleanup
    print(f"🛑 Shutting down {settings.service_name}")
    if monitoring_orchestrator:
        await monitoring_orchestrator.stop_monitoring()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="DevOps AI Agent",
        description="Intelligent Infrastructure Management and DevOps Automation System",
        version=settings.service_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health endpoints
    @app.get("/health", response_model=AgentHealthStatus, tags=["Health"])
    async def health_check():
        """Basic health check endpoint."""
        return AgentHealthStatus(
            status="healthy",
            service=settings.service_name,
            version=settings.service_version,
            agent_active=monitoring_orchestrator.is_running if monitoring_orchestrator else False
        )
    
    @app.get("/status", response_model=AgentDetailedStatus, tags=["Health"])
    async def detailed_status():
        """Detailed service status endpoint."""
        uptime = time.time() - app_start_time
        
        # Get monitoring status
        monitoring_status = monitoring_orchestrator.get_monitoring_status() if monitoring_orchestrator else {}
        
        # Check LLM availability
        llm_available = False
        if monitoring_orchestrator and monitoring_orchestrator.analysis_agent:
            llm_available = monitoring_orchestrator.analysis_agent.is_available()
        
        # Get target services status
        target_services = {}
        if monitoring_orchestrator:
            for name, target in monitoring_orchestrator.monitoring_targets.items():
                target_services[name] = target.status
        
        # Get recent actions
        recent_actions = []
        if monitoring_orchestrator:
            recent_actions = [action.description for action in monitoring_orchestrator.recent_actions[-5:]]
        
        return AgentDetailedStatus(
            status="healthy",
            service=settings.service_name,
            version=settings.service_version,
            uptime_seconds=uptime,
            agent_active=monitoring_orchestrator.is_running if monitoring_orchestrator else False,
            last_monitoring_cycle=monitoring_orchestrator.last_cycle_time if monitoring_orchestrator else None,
            monitoring_interval=settings.monitoring_interval,
            target_services=target_services,
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            llm_available=llm_available,
            recent_actions=recent_actions,
            pending_actions=0,  # Will be implemented in later phases
            safety_mode=settings.safety_mode,
            learning_enabled=settings.learning_enabled,
            fallback_enabled=settings.fallback_enabled
        )
    
    # Agent control endpoints
    @app.post("/control/start-monitoring", tags=["Agent Control"])
    async def start_monitoring():
        """Manually start the monitoring loop."""
        if not monitoring_orchestrator:
            raise HTTPException(status_code=500, detail="Monitoring orchestrator not initialized")
        
        if monitoring_orchestrator.is_running:
            return {"message": "Monitoring already running", "status": "running"}
        
        await monitoring_orchestrator.start_monitoring()
        return {"message": "Monitoring started", "status": "started"}
    
    @app.post("/control/stop-monitoring", tags=["Agent Control"])
    async def stop_monitoring():
        """Manually stop the monitoring loop."""
        if not monitoring_orchestrator:
            raise HTTPException(status_code=500, detail="Monitoring orchestrator not initialized")
        
        if not monitoring_orchestrator.is_running:
            return {"message": "Monitoring not running", "status": "stopped"}
        
        await monitoring_orchestrator.stop_monitoring()
        return {"message": "Monitoring stopped", "status": "stopped"}
    
    @app.get("/monitoring/status", tags=["Monitoring"])
    async def monitoring_status():
        """Get detailed monitoring status."""
        if not monitoring_orchestrator:
            raise HTTPException(status_code=500, detail="Monitoring orchestrator not initialized")
        
        return monitoring_orchestrator.get_monitoring_status()
    
    @app.post("/monitoring/cycle", tags=["Monitoring"])
    async def trigger_monitoring_cycle():
        """Manually trigger a single monitoring cycle."""
        if not monitoring_orchestrator:
            raise HTTPException(status_code=500, detail="Monitoring orchestrator not initialized")
        
        try:
            await monitoring_orchestrator._perform_monitoring_cycle()
            return {"message": "Monitoring cycle completed", "timestamp": datetime.utcnow().isoformat()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Monitoring cycle failed: {str(e)}")
    
    @app.get("/debug/docker", tags=["Debug"])
    async def debug_docker():
        """Debug Docker API connectivity and permissions."""
        from agent.services.docker_service import DockerServiceManager
        
        docker_service = DockerServiceManager()
        debug_info = await docker_service.debug_docker_connectivity()
        system_info = await docker_service.get_system_info()
        
        return {
            "debug_info": debug_info,
            "system_info": system_info
        }
    
    @app.get("/orchestrator/status", tags=["Debug"])
    async def orchestrator_status():
        """Get orchestrator status with recovery action history."""
        from agent.core.orchestrator import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        return orchestrator.get_status()
    
    # Webhook endpoints
    @app.post("/webhook/alerts", response_model=WebhookResponse, tags=["Webhooks"])
    async def receive_alertmanager_webhook(webhook: AlertmanagerWebhook):
        """Receive alerts from Alertmanager and trigger automated recovery."""
        if not monitoring_orchestrator:
            raise HTTPException(status_code=500, detail="Monitoring orchestrator not initialized")
        
        # Convert webhook to dictionary format for processing
        alert_data = {
            'alerts': [
                {
                    'labels': alert.labels,
                    'annotations': alert.annotations,
                    'status': alert.status,
                    'starts_at': alert.starts_at.isoformat() if alert.starts_at else None,
                    'ends_at': alert.ends_at.isoformat() if alert.ends_at else None
                }
                for alert in webhook.alerts
            ]
        }
        
        # Handle alerts with recovery integration
        result = await monitoring_orchestrator.handle_alert_webhook(alert_data)
        
        return WebhookResponse(
            status="processed",
            message=f"Processed {result['received_alerts']} alerts, executed {result['processed_alerts']} recoveries",
            alerts_processed=result['received_alerts'],
            actions_triggered=result['processed_alerts']
        )
    
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.service_name,
            "version": settings.service_version,
            "status": "running",
            "agent_type": "autonomous_programmer",
            "docs_url": "/docs",
            "health_url": "/health",
            "status_url": "/status",
            "monitoring_url": "/monitoring/status"
        }
    
    return app


# Create the FastAPI application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    from agent.config.settings import get_settings
    
    settings = get_settings()
    uvicorn.run(
        "agent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )