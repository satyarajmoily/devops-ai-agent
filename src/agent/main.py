"""Main FastAPI application for DevOps AI Agent."""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agent.config.settings import get_settings
from agent.models.health import AgentHealthStatus
from agent.models.webhook import AlertmanagerWebhook, WebhookResponse
from agent.services.recovery_service import PureAIRecoveryService

# Global variables to track application state
app_start_time = time.time()
ai_recovery_service: PureAIRecoveryService = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    global ai_recovery_service
    
    settings = get_settings()
    print(f"🤖 Starting {settings.service_name} v{settings.service_version}")
    print(f"🌍 Environment: {settings.environment}")
    print(f"📡 API will be available at http://{settings.api_host}:{settings.api_port}")
    
    # Initialize AI recovery service for event-driven responses
    ai_recovery_service = PureAIRecoveryService()
    
    # Event-driven mode ONLY - no monitoring loops
    print("🎯 Agent initialized in PURE event-driven mode")
    print("📡 Waiting for alerts from Prometheus/Alertmanager at /webhook/alerts")
    print("🚫 NO background monitoring - responds only to alerts")
    
    yield
    
    # Cleanup
    print(f"🛑 Shutting down {settings.service_name}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="DevOps AI Agent",
        description="Event-Driven Infrastructure Recovery System",
        version=settings.service_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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
            agent_active=True  # Always active for event-driven responses
        )
    
    # Webhook endpoints - CORE FUNCTIONALITY
    @app.post("/webhook/alerts", response_model=WebhookResponse, tags=["Webhooks"])
    async def receive_alertmanager_webhook(webhook: AlertmanagerWebhook):
        """Receive alerts from Alertmanager and trigger automated recovery."""
        if not ai_recovery_service:
            raise HTTPException(status_code=500, detail="AI recovery service not initialized")
        
        # Log incoming alerts clearly
        alert_count = len(webhook.alerts)
        print(f"🚨 Received {alert_count} alerts from Alertmanager")
        
        # Log each alert with clear information
        for i, alert in enumerate(webhook.alerts):
            alert_name = alert.labels.get('alertname', 'Unknown')
            severity = alert.labels.get('severity', 'unknown')
            service = alert.labels.get('service', 'unknown')
            status = alert.status
            
            if status == 'firing':
                print(f"  🔥 FIRING: {alert_name} - {service} service issue (severity: {severity})")
            else:
                print(f"  ✅ RESOLVED: {alert_name} - {service} service recovered")
            
            if status == 'firing':
                print(f"     🤖 Triggering AI-driven recovery for alert: {alert_name}")
                print(f"     🧠 AI will analyze the situation and decide what actions to take...")
        
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
        
        # Handle alerts with AI recovery
        try:
            print(f"  🔄 Starting background AI recovery for {[alert.labels.get('alertname', 'Unknown') for alert in webhook.alerts if alert.status == 'firing']}...")
            result = await ai_recovery_service.execute_recovery(alert_data)
            
            success_msg = f"✅ AI Recovery completed: {result.ai_decision}"
            print(success_msg)
            
            return WebhookResponse(
                status="processed",
                message=f"Executed AI recovery: {result.ai_decision}",
                alerts_processed=len(webhook.alerts),
                actions_triggered=result.actions_executed
            )
        except Exception as e:
            error_msg = f"❌ AI Recovery failed: {str(e)}"
            print(error_msg)
            
            return WebhookResponse(
                status="error",
                message=f"Recovery failed: {str(e)}",
                alerts_processed=len(webhook.alerts),
                actions_triggered=0
            )
    
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.service_name,
            "version": settings.service_version,
            "status": "running",
            "mode": "event_driven_only",
            "docs_url": "/docs",
            "health_url": "/health",
            "webhook_url": "/webhook/alerts"
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