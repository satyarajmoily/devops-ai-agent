# DevOps AI Agent - Technical Context

## Technology Stack

### Core Framework
- **Python 3.11+**: Modern Python with async/await support
- **FastAPI**: High-performance async web framework for API endpoints
- **Pydantic**: Data validation and settings management with BaseSettings
- **HTTPX**: Modern async HTTP client for AI Command Gateway communication

### AI & LLM Integration
- **OpenAI Python Client**: GPT-4 integration for intelligent analysis
- **LangChain Framework**: AI agent orchestration and reasoning chains
- **Custom AI Components**: Multi-phase diagnostic planning and pattern recognition

### Infrastructure Operations
- **AI Command Gateway Client**: Natural language Docker operations via HTTP API
- **Natural Language Processing**: Convert AI analysis to human-readable operation intents
- **Structured Response Processing**: Handle gateway execution results and errors

### Monitoring & Alerting
- **Prometheus Integration**: Metrics collection and monitoring
- **Alertmanager Webhooks**: Event-driven alert processing
- **Custom Alert Models**: Structured alert data processing

### Configuration & Environment
- **Environment Variables**: .env file configuration with strict validation
- **Pydantic Settings**: Type-safe configuration management with no defaults
- **Fail-Fast Validation**: Application startup failure for missing configuration

## Architecture Overview

### Clean Microservices Design
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

### Key Components

#### 1. AI Command Gateway Client
- **Technology**: HTTPX async HTTP client
- **Purpose**: Natural language infrastructure operations
- **API**: RESTful HTTP API with JSON payloads
- **Features**: Rich context sharing, structured error handling

#### 2. AI Analysis Engine
- **Technology**: OpenAI GPT-4 + LangChain
- **Purpose**: Intelligent monitoring and problem analysis
- **Features**: Multi-phase diagnostics, pattern recognition, recovery planning

#### 3. Alert Processing System
- **Technology**: FastAPI webhooks + Pydantic models
- **Purpose**: Event-driven infrastructure monitoring
- **Features**: Alertmanager integration, structured alert processing

## Development Environment

### Local Setup
```bash
# Virtual environment setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Dependencies installation
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with required settings (no defaults provided)

# AI Command Gateway dependency
# Ensure AI Command Gateway is running at http://localhost:8003
```

### Required Environment Variables
```env
# AI Command Gateway Integration (REQUIRED - no defaults)
AI_COMMAND_GATEWAY_URL=http://localhost:8003
AI_COMMAND_GATEWAY_TIMEOUT=30
AI_COMMAND_GATEWAY_SOURCE_ID=devops-ai-agent

# LLM Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-4-1106-preview
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000

# Application Settings (REQUIRED)
LOG_LEVEL=INFO
ENVIRONMENT=development
```

## Dependencies

### Core Dependencies
```python
# Web framework and async support
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# HTTP client for AI Command Gateway
httpx==0.25.2

# AI and LLM integration
openai==1.3.0
langchain==0.0.350
langchain-openai==0.0.2

# Monitoring and alerting
prometheus-client==0.19.0

# Configuration and utilities
python-dotenv==1.0.0
structlog==23.2.0
```

### Removed Dependencies (AI Command Gateway Integration)
```python
# No longer needed - replaced by HTTP client
# docker==6.1.3              # Docker SDK removed
# paramiko==3.4.0             # SSH support removed  
# oci==2.115.0                # OCI direct integration removed
# kubernetes==28.1.0          # Kubernetes direct support removed
```

### Development Dependencies
```python
# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx-mock==0.10.0          # For mocking gateway HTTP calls
pytest-mock==3.12.0

# Code quality
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.0
```

## Configuration Management

### Strict Configuration Pattern
```python
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Strict configuration with no defaults"""
    
    # AI Command Gateway (REQUIRED)
    ai_command_gateway_url: str = Field(..., description="Gateway URL")
    ai_command_gateway_timeout: int = Field(..., description="Request timeout")
    ai_command_gateway_source_id: str = Field(..., description="Source ID")
    
    # LLM Configuration (REQUIRED)
    openai_api_key: str = Field(..., description="OpenAI API key")
    llm_model: str = Field(..., description="LLM model name")
    llm_temperature: float = Field(..., description="LLM temperature")
    llm_max_tokens: int = Field(..., description="LLM max tokens")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def __post_init__(self):
        """Validate configuration at startup"""
        if not self.ai_command_gateway_url.startswith(('http://', 'https://')):
            raise ValueError("❌ Invalid gateway URL")
```

## API Integration

### AI Command Gateway API Schema
```python
# Request Schema
class GatewayRequest(BaseModel):
    source_id: str                    # "devops-ai-agent"
    target_resource: Dict[str, str]   # {"name": "market-predictor"}
    action_request: ActionRequest

class ActionRequest(BaseModel):
    intent: str                       # "restart the service"
    context: str                      # Rich monitoring context
    priority: str = "MEDIUM"          # "LOW", "MEDIUM", "HIGH"

# Response Schema  
class GatewayResponse(BaseModel):
    request_id: str
    timestamp_processed_utc: str
    overall_status: str               # "success", "error", "timeout"
    execution_details: ExecutionDetails

class ExecutionDetails(BaseModel):
    command: str                      # Generated Docker command
    execution_result: str             # Command output/result
    execution_time_ms: int            # Execution duration
```

### Example API Usage
```python
async def restart_service_via_gateway(service_name: str, context: str):
    """Restart service through AI Command Gateway"""
    
    request = {
        "source_id": "devops-ai-agent",
        "target_resource": {"name": service_name},
        "action_request": {
            "intent": "restart the service",
            "context": f"AI Analysis: {context}. Memory leak detected.",
            "priority": "HIGH"
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.ai_command_gateway_url}/execute-docker-command",
            json=request,
            timeout=settings.ai_command_gateway_timeout
        )
        
    return response.json()
```

## Testing Strategy

### HTTP Client Testing
```python
import httpx_mock
import pytest

@pytest.mark.asyncio
async def test_gateway_restart_service():
    """Test service restart through gateway"""
    
    with httpx_mock.mock(url="http://localhost:8003/execute-docker-command") as mock:
        # Mock gateway response
        mock.add_response(json={
            "request_id": "test-123",
            "overall_status": "success",
            "execution_details": {
                "command": "docker restart market-predictor",
                "execution_result": "Container restarted successfully",
                "execution_time_ms": 2500
            }
        })
        
        # Test gateway client
        client = AICommandGatewayClient(settings)
        result = await client.restart_service("market-predictor", "test context")
        
        assert result.success
        assert "restarted successfully" in result.output
```

### AI Component Testing
```python
@pytest.mark.asyncio
async def test_ai_analysis_with_mocked_llm():
    """Test AI analysis with mocked LLM responses"""
    
    with patch('openai.ChatCompletion.acreate') as mock_llm:
        mock_llm.return_value = {
            "choices": [{
                "message": {
                    "content": "Memory leak detected. Recommend service restart."
                }
            }]
        }
        
        analyzer = AIAnalyzer(settings)
        result = await analyzer.analyze_alert(test_alert)
        
        assert "memory leak" in result.analysis.lower()
        assert "restart" in result.recommendation.lower()
```

## Deployment Architecture

### Container Environment
```dockerfile
FROM python:3.11-slim

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ /app/src/
WORKDIR /app

# Configuration
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "src.agent.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Service Dependencies
```yaml
# docker-compose.yml
version: '3.8'
services:
  devops-ai-agent:
    build: .
    ports:
      - "8001:8001"
    environment:
      - AI_COMMAND_GATEWAY_URL=http://ai-command-gateway:8003
    depends_on:
      - ai-command-gateway
    networks:
      - ai-infrastructure
      
  ai-command-gateway:
    # AI Command Gateway service
    ports:
      - "8003:8003"
    networks:
      - ai-infrastructure
      
networks:
  ai-infrastructure:
    driver: bridge
```

## Performance Considerations

### Async Architecture
- **Non-blocking Operations**: All HTTP calls to gateway are async
- **Concurrent Processing**: Multiple alerts can be processed simultaneously
- **Timeout Management**: Configurable timeouts for all gateway operations

### Resource Usage
- **Memory**: Lightweight HTTP client vs heavy Docker SDK
- **CPU**: Reduced overhead from simplified architecture
- **Network**: Efficient HTTP/JSON communication with gateway

### Scalability
- **Horizontal Scaling**: Agent and gateway can be scaled independently
- **Load Distribution**: Multiple agent instances can share alert processing
- **Resource Isolation**: Clean separation between monitoring and execution

## Security Considerations

### API Security
- **Authentication**: Bearer tokens for gateway API access
- **Input Validation**: Strict request validation using Pydantic models
- **Error Handling**: No sensitive information leaked in error responses

### Configuration Security
- **Environment Variables**: Sensitive config in environment variables
- **No Hardcoding**: All credentials and URLs from configuration
- **Fail-Fast**: Missing security config prevents application startup

### Network Security
- **Internal Networks**: Agent communicates with gateway over internal networks
- **HTTPS Support**: Gateway communication can use HTTPS in production
- **Audit Logging**: All gateway operations logged for security audit

## Development Workflow

### Code Organization
```
devops-ai-agent/
├── src/
│   └── agent/
│       ├── main.py                    # FastAPI application
│       ├── core/
│       │   ├── monitoring.py          # Alert processing orchestration
│       │   └── ai_intelligence.py     # AI analysis and reasoning
│       ├── services/
│       │   ├── ai_command_gateway_client.py  # Gateway HTTP client
│       │   └── recovery_service.py     # Recovery orchestration
│       ├── models/
│       │   ├── alerts.py              # Alert data models
│       │   ├── gateway.py             # Gateway request/response models
│       │   └── operations.py          # Operation result models
│       └── config/
│           └── settings.py            # Configuration management
├── tests/
│   ├── unit/                          # Unit tests with mocking
│   └── integration/                   # Integration tests
├── requirements.txt                   # Python dependencies
├── .env.example                       # Configuration template
└── README.md                          # Setup and usage docs
```

### Development Best Practices
- **Type Hints**: Full type annotations for all functions and classes
- **Async/Await**: Consistent async patterns throughout codebase  
- **Error Handling**: Structured error handling with proper logging
- **Configuration**: Strict configuration validation with clear error messages
- **Testing**: Comprehensive test coverage with HTTP mocking
- **Documentation**: Clear docstrings and API documentation

This technical context reflects a modern, clean architecture focused on AI orchestration with centralized infrastructure operations through the AI Command Gateway service. 