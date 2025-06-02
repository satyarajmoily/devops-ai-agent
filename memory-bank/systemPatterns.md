# DevOps AI Agent - System Patterns & Architecture

## Revolutionary Architecture: AI Command Gateway Integration

### Core Innovation
The DevOps AI Agent has evolved from complex Docker SDK integration to a clean AI Command Gateway client architecture. This enables intelligent monitoring and analysis with natural language infrastructure operations through a specialized command execution service.

### Architecture Evolution

#### ❌ OLD: Complex Docker SDK Integration
```python
# BAD: Complex Docker SDK handling
def restart_service(service_name):
    docker_client = docker.from_env()
    container = docker_client.containers.get(service_name)
    container.restart()

def get_logs(service_name):
    docker_client = docker.from_env()
    container = docker_client.containers.get(service_name)
    return container.logs()
```

#### ✅ NEW: Natural Language Gateway Operations
```python
# GOOD: Clean AI Command Gateway client
async def restart_service(service_name: str, context: str):
    gateway_request = {
        "source_id": "devops-ai-agent",
        "target_resource": {"name": service_name},
        "action_request": {
            "intent": "restart the service",
            "context": context
        }
    }
    return await gateway_client.execute_operation(gateway_request)
```

## AI Command Gateway Integration Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  DevOps AI      │───▶│ AI Command      │───▶│ Docker Engine   │
│  Agent          │    │ Gateway         │    │                 │
│  (Monitor &     │    │ (Command Gen &  │    │ (Containers)    │
│   Analyze)      │    │  Execution)     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│ GPT-4 Analysis  │    │ GPT-3.5 Command │
│ & Decision      │    │ Generation      │
└─────────────────┘    └─────────────────┘
```

## Core System Patterns

### 1. AI Command Gateway Client Pattern
**Principle**: All infrastructure operations delegated to AI Command Gateway service

```python
class AICommandGatewayClient:
    """Clean HTTP client for AI Command Gateway communication"""
    
    def __init__(self, config: Settings):
        # NO HARDCODING - Everything from config
        self.gateway_url = config.ai_command_gateway_url
        self.timeout = config.ai_command_gateway_timeout
        self.source_id = config.ai_command_gateway_source_id
        
    async def restart_service(self, service_name: str, context: str) -> GatewayResult:
        """Restart service with rich context"""
        request = {
            "source_id": self.source_id,
            "target_resource": {"name": service_name},
            "action_request": {
                "intent": "restart the service",
                "context": f"DevOps AI Analysis: {context}",
                "priority": "HIGH"
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gateway_url}/execute-docker-command",
                json=request,
                timeout=self.timeout
            )
            return self._parse_gateway_response(response)
```

### 2. Natural Language Operation Pattern
**Principle**: Express infrastructure operations as human-readable intents

```python
class NaturalLanguageOperations:
    """Convert AI analysis to natural language operations"""
    
    def __init__(self, gateway_client: AICommandGatewayClient):
        self.gateway = gateway_client
    
    async def execute_recovery_plan(self, alert_context: str, ai_analysis: str):
        """Execute recovery with rich context"""
        
        # Convert AI analysis to natural language intent
        operations = {
            "memory_leak_detected": {
                "intent": "restart the service",
                "context": f"Alert: {alert_context}. Analysis: {ai_analysis}. Memory leak pattern detected."
            },
            "logs_investigation": {
                "intent": "show recent error logs",
                "context": f"Investigating {alert_context}. Looking for error patterns: {ai_analysis}"
            },
            "health_validation": {
                "intent": "check if service is healthy", 
                "context": f"Post-recovery validation for {alert_context}"
            }
        }
        
        # AI determines which operation to execute
        operation_type = await self._determine_operation(ai_analysis)
        operation = operations[operation_type]
        
        return await self.gateway.execute_operation(
            service_name=self._extract_service_name(alert_context),
            intent=operation["intent"],
            context=operation["context"]
        )
```

### 3. Gateway Executor Pattern
**Principle**: Replace complex Docker executor with simple gateway client

```python
class GatewayExecutor:
    """Simplified executor using AI Command Gateway"""
    
    def __init__(self, gateway_client: AICommandGatewayClient):
        self.gateway = gateway_client
    
    async def execute_operation(self, operation: dict) -> OperationResult:
        """Execute any operation through gateway"""
        
        # Map internal operations to natural language
        intent_mapping = {
            "restart_service": "restart the service",
            "get_logs": "show recent error logs", 
            "check_health": "check if service is healthy",
            "get_status": "show service status and health"
        }
        
        # Convert to natural language intent
        intent = intent_mapping.get(
            operation["name"], 
            f"perform {operation['name']} operation"
        )
        
        # Include rich context from operation parameters
        context = self._build_operation_context(operation)
        
        return await self.gateway.execute_operation(
            service_name=operation["target"],
            intent=intent,
            context=context
        )
    
    def _build_operation_context(self, operation: dict) -> str:
        """Build rich context for gateway request"""
        context_parts = []
        
        if "alert_context" in operation:
            context_parts.append(f"Alert: {operation['alert_context']}")
            
        if "ai_analysis" in operation:
            context_parts.append(f"AI Analysis: {operation['ai_analysis']}")
            
        if "reasoning" in operation:
            context_parts.append(f"Reasoning: {operation['reasoning']}")
            
        return ". ".join(context_parts)
```

### 4. Configuration-Driven Gateway Pattern
**Principle**: All gateway settings from .env with strict validation

```python
class GatewaySettings(BaseSettings):
    """Strict gateway configuration with no defaults"""
    
    # REQUIRED - Application fails if missing
    ai_command_gateway_url: str = Field(..., description="Gateway URL - REQUIRED")
    ai_command_gateway_timeout: int = Field(..., description="Request timeout - REQUIRED") 
    ai_command_gateway_source_id: str = Field(..., description="Source identification - REQUIRED")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __post_init__(self):
        """Validate gateway configuration"""
        if not self.ai_command_gateway_url.startswith(('http://', 'https://')):
            raise ValueError("❌ Invalid gateway URL - application cannot start")
            
        if self.ai_command_gateway_timeout <= 0:
            raise ValueError("❌ Invalid timeout value - application cannot start")
            
        if not self.ai_command_gateway_source_id:
            raise ValueError("❌ Missing source ID - application cannot start")
```

### 5. Fail-Fast Gateway Connectivity Pattern
**Principle**: Validate gateway connectivity at startup

```python
class GatewayConnectivityChecker:
    """Ensure gateway is available before starting operations"""
    
    def __init__(self, gateway_client: AICommandGatewayClient):
        self.gateway = gateway_client
    
    async def validate_connectivity(self) -> bool:
        """Check gateway connectivity at startup"""
        try:
            # Test connectivity with simple health check
            response = await self.gateway.health_check()
            
            if response.status == "success":
                logger.info("✅ AI Command Gateway connectivity validated")
                return True
            else:
                raise RuntimeError(f"❌ Gateway health check failed: {response}")
                
        except Exception as e:
            # FAIL FAST - Don't start if gateway unavailable
            raise RuntimeError(
                f"❌ CRITICAL: Cannot connect to AI Command Gateway at startup: {e}. "
                f"Application cannot start without gateway connectivity."
            )
```

### 6. Rich Context Enhancement Pattern
**Principle**: Include comprehensive monitoring context in gateway requests

```python
class ContextEnhancer:
    """Enhance gateway requests with rich monitoring context"""
    
    def enhance_request_context(
        self, 
        alert: AlertModel, 
        ai_analysis: str,
        operation_type: str
    ) -> str:
        """Build comprehensive context for gateway request"""
        
        context_components = [
            f"Service: {alert.service_name}",
            f"Alert: {alert.alert_name} - {alert.description}",
            f"Severity: {alert.severity}",
            f"Duration: {alert.duration}",
            f"AI Analysis: {ai_analysis}",
            f"Operation: {operation_type}",
            f"Timestamp: {alert.timestamp}",
        ]
        
        # Add historical context if available
        if hasattr(alert, 'previous_incidents'):
            context_components.append(
                f"History: {alert.previous_incidents} similar incidents in last 24h"
            )
            
        # Add performance context
        if hasattr(alert, 'metrics'):
            context_components.append(
                f"Metrics: CPU {alert.metrics.cpu}%, Memory {alert.metrics.memory}%"
            )
            
        return ". ".join(context_components)
```

## Integration Benefits Patterns

### Architecture Simplification Pattern
```python
# BEFORE: Complex multi-service pattern
class OldDockerManager:
    def __init__(self):
        self.docker_client = docker.from_env()  # Docker SDK
        self.ssh_client = paramiko.SSHClient()  # SSH for remote
        self.subprocess_runner = subprocess     # Shell commands
        # 500+ lines of Docker SDK handling
        
# AFTER: Simple HTTP client pattern
class NewGatewayClient:
    def __init__(self):
        self.http_client = httpx.AsyncClient()  # Single HTTP client
        # ~50 lines of clean HTTP requests
```

### Testing Simplification Pattern
```python
# BEFORE: Complex Docker testing
async def test_docker_restart():
    # Requires Docker daemon, test containers, complex mocking
    mock_docker = MagicMock()
    mock_container = MagicMock()
    # Complex setup...

# AFTER: Simple HTTP testing  
async def test_gateway_restart():
    # Simple HTTP response mocking
    with httpx_mock.mock(url="http://localhost:8003/execute-docker-command") as mock:
        mock.add_response(json={"status": "success"})
        result = await gateway_client.restart_service("test-service", "test context")
        assert result.success
```

### Error Handling Pattern
```python
class GatewayErrorHandler:
    """Handle structured error responses from gateway"""
    
    async def handle_gateway_response(self, response: httpx.Response) -> OperationResult:
        """Process gateway response with proper error handling"""
        
        if response.status_code == 200:
            result = response.json()
            return OperationResult(
                success=True,
                command=result["execution_details"]["command"],
                output=result["execution_details"]["execution_result"],
                timestamp=result["timestamp_processed_utc"]
            )
        elif response.status_code == 400:
            error = response.json()
            logger.error(f"Gateway request error: {error['detail']}")
            return OperationResult(
                success=False,
                error=f"Invalid request: {error['detail']}"
            )
        elif response.status_code == 500:
            logger.error("Gateway internal error - escalating to human")
            # NO FALLBACK - Escalate to human as per project rules
            raise GatewayUnavailableError("Gateway service unavailable")
        else:
            raise UnexpectedResponseError(f"Unexpected response: {response.status_code}")
```

## Anti-Patterns to Avoid

### ❌ Docker SDK Fallback Pattern
```python
# NEVER DO THIS - No fallback mechanisms allowed
async def bad_execute_with_fallback(operation):
    try:
        return await gateway_client.execute(operation)
    except Exception:
        # BAD - No Docker SDK fallback
        return docker_client.execute(operation)  # FORBIDDEN
```

### ❌ Hardcoded Configuration Pattern  
```python
# NEVER DO THIS - No hardcoded values
class BadConfiguration:
    GATEWAY_URL = "http://localhost:8003"  # HARDCODED!
    TIMEOUT = 30                          # HARDCODED!
```

### ❌ Hidden Defaults Pattern
```python
# NEVER DO THIS - No hidden defaults
def bad_config_with_defaults():
    return {
        "gateway_url": os.getenv("GATEWAY_URL", "http://localhost:8003"),  # BAD!
        "timeout": int(os.getenv("TIMEOUT", "30"))                        # BAD!
    }
```

## Production-Ready Patterns

### Audit Trail Pattern
```python
class GatewayAuditLogger:
    """Log all gateway operations for audit trail"""
    
    async def log_operation(self, request: dict, response: dict):
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "devops-ai-agent",
            "operation": request["action_request"]["intent"],
            "target": request["target_resource"]["name"],
            "context": request["action_request"]["context"],
            "success": response.get("overall_status") == "success",
            "command_executed": response.get("execution_details", {}).get("command"),
            "execution_time": response.get("execution_time_ms")
        }
        
        logger.info(f"Gateway Operation: {json.dumps(audit_entry)}")
```

### Performance Monitoring Pattern
```python
class GatewayPerformanceMonitor:
    """Monitor gateway operation performance"""
    
    async def track_operation_performance(self, operation_start: datetime, response: dict):
        operation_time = (datetime.utcnow() - operation_start).total_seconds()
        
        # Track metrics
        metrics = {
            "gateway_operation_duration_seconds": operation_time,
            "gateway_success_rate": 1 if response.get("overall_status") == "success" else 0,
            "gateway_command_execution_time_ms": response.get("execution_time_ms", 0)
        }
        
        # Log performance metrics
        for metric, value in metrics.items():
            logger.info(f"METRIC: {metric}={value}")
```

This architecture represents a fundamental shift from complex, tightly-coupled Docker operations to clean, microservices-based AI orchestration with natural language infrastructure operations. 