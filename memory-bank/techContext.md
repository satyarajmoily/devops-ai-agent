# Technical Context - Market Programmer Agent

## Technology Stack

### Core Technologies
- **Language**: Python 3.9+
- **Web Framework**: FastAPI 0.104+
- **AI Framework**: LangChain 0.1.0+
- **LLM Integration**: OpenAI GPT-4 (primary), Anthropic Claude (backup)
- **HTTP Client**: httpx (for external API calls)
- **Async Framework**: asyncio with background task management

### AI/LLM Dependencies
- **LangChain**: Core agent framework and LLM orchestration
- **OpenAI**: GPT-4 for analysis and code generation
- **LangChain Tools**: Memory, agents, chains, and tool integration
- **Prompt Templates**: Structured prompt management and versioning
- **Vector Stores**: For future knowledge base implementation

### External Service Integration
- **Prometheus Client**: prometheus-client for metrics scraping
- **GitHub API**: PyGithub for repository and PR management
- **Docker API**: docker-py for testing environment management
- **HTTP Monitoring**: httpx for service health monitoring

### Development Dependencies
- **Testing**: pytest, pytest-asyncio, pytest-mock
- **Code Quality**: black, isort, flake8, mypy
- **Documentation**: FastAPI auto-docs (OpenAPI/Swagger)
- **Development Server**: uvicorn with reload

### Deployment Technologies
- **Containerization**: Docker
- **Base Image**: python:3.9-slim
- **Process Manager**: Uvicorn + background async tasks
- **Port**: 8001 (configurable, different from market-predictor)

## Development Setup

### Prerequisites
- Python 3.9 or higher
- Docker (for containerized deployment and testing environments)
- Git (for version control and GitHub integration)
- OpenAI API key (for LLM integration)
- GitHub personal access token (for repository access)

### Local Development Environment
```bash
# Clone repository
git clone <repository-url>
cd market-programmer-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Run development server
uvicorn src.agent.main:app --reload --host 0.0.0.0 --port 8001
```

### Environment Configuration
```bash
# .env file for local development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8001

# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1

# External Service Configuration
MARKET_PREDICTOR_URL=http://localhost:8000
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100

# GitHub Integration
GITHUB_TOKEN=ghp_...
GITHUB_REPOSITORY=owner/repo-name
ALLOWED_REPOSITORIES=owner/market-predictor,owner/market-programmer-agent

# Monitoring Configuration
MONITORING_INTERVAL=30
HEALTH_CHECK_TIMEOUT=10
METRICS_CACHE_TTL=60
```

### Docker Development
```bash
# Build development image
docker build -f docker/Dockerfile.dev -t market-programmer-agent:dev .

# Run development container
docker run -p 8001:8001 --env-file .env market-programmer-agent:dev

# Run with docker-compose (includes testing environment)
docker-compose -f docker/docker-compose.dev.yml up
```

## Dependencies

### Core Production Dependencies
```
# Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# AI/LLM Framework
langchain>=0.1.0
openai>=1.0.0
anthropic>=0.7.0

# External Service Integration
httpx>=0.25.0
prometheus-client>=0.17.0
PyGithub>=1.59.0
docker>=6.1.0

# Utilities
python-multipart>=0.0.6
python-dotenv>=1.0.0
asyncio>=3.4.3
```

### Development Dependencies
```
# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
httpx>=0.25.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.4.0

# Development Tools
jupyter>=1.0.0  # For LLM experimentation
langchain-experimental>=0.0.40  # For advanced agent features
```

### Optional Dependencies
```
# Advanced Monitoring
grafana-api>=1.0.3
elasticsearch>=8.0.0

# Database (for future knowledge persistence)
sqlalchemy>=2.0.0
alembic>=1.12.0

# Vector Database (for knowledge base)
chromadb>=0.4.0
faiss-cpu>=1.7.4
```

## Technical Constraints

### Performance Requirements
- **Monitoring Loop**: Complete cycle every 30 seconds (configurable)
- **LLM Response Time**: < 30 seconds for analysis (with timeout)
- **API Response Time**: < 5 seconds for health/status endpoints
- **Memory Usage**: < 1GB under normal operation (excluding LLM context)

### AI/LLM Constraints
- **Token Limits**: Respect OpenAI/Anthropic token limits per request
- **Rate Limiting**: Handle API rate limits gracefully with backoff
- **Context Management**: Maintain conversation context within token limits
- **Cost Management**: Monitor and limit LLM usage costs

### Security Requirements
- **API Key Management**: Secure storage and rotation of API keys
- **Repository Access**: Limited to explicitly allowed repositories
- **Sandbox Isolation**: All testing in isolated environments
- **Input Sanitization**: Validate all LLM inputs and outputs

### Integration Constraints
- **Service Dependencies**: Graceful handling of external service failures
- **Network Timeouts**: Appropriate timeouts for all external calls
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breakers**: Prevent cascade failures

## Development Workflow

### Code Quality Standards
```bash
# Pre-commit hooks (includes LLM prompt validation)
pre-commit install

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking (with LangChain compatibility)
mypy src/ --ignore-missing-imports

# Linting
flake8 src/ tests/

# Testing (with LLM mocking)
pytest tests/ -v --cov=src --cov-report=html
```

### AI Development Workflow
```bash
# Test LLM prompts in Jupyter notebook
jupyter notebook notebooks/

# Validate prompt templates
python scripts/validate_prompts.py

# Test agent workflows with mock LLM
pytest tests/agents/ -k "test_agent_workflow"

# Integration test with real LLM (expensive)
pytest tests/integration/ -m "llm_integration" --slow
```

### Testing Strategy
```
tests/
├── unit/              # Unit tests for individual components
│   ├── services/      # Service layer tests
│   ├── agents/        # Agent tests with mocked LLM
│   └── models/        # Data model tests
├── integration/       # Integration tests
│   ├── api/           # FastAPI endpoint tests
│   ├── external/      # External service integration
│   └── llm/           # LLM integration tests (marked as slow)
├── fixtures/          # Test data and fixtures
└── mocks/             # LLM and external service mocks
```

## Configuration Management

### Environment Variables
```python
class Settings(BaseSettings):
    # Application settings
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    
    # LLM settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # External service settings
    market_predictor_url: str = "http://localhost:8000"
    prometheus_url: Optional[str] = None
    loki_url: Optional[str] = None
    
    # GitHub settings
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    allowed_repositories: List[str] = []
    
    # Monitoring settings
    monitoring_interval: int = 30
    health_check_timeout: int = 10
    metrics_cache_ttl: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### LLM Prompt Management
```python
class PromptTemplates:
    ANALYSIS_PROMPT = """
    You are an expert system administrator analyzing a service issue.
    
    Service: Market Predictor
    Issue Type: {issue_type}
    
    Monitoring Data:
    {monitoring_data}
    
    Please analyze this issue and provide:
    1. Root cause analysis
    2. Severity assessment
    3. Recommended actions
    4. Risk assessment for proposed changes
    
    Format your response as JSON with these fields:
    {{
        "root_cause": "...",
        "severity": "low|medium|high|critical",
        "recommended_actions": [...],
        "risk_assessment": "..."
    }}
    """
    
    CODE_GENERATION_PROMPT = """
    You are an expert software engineer creating a fix for an issue.
    
    Issue: {issue_description}
    Root Cause: {root_cause}
    Target: {target_file}
    
    Generate Python code to fix this issue following these constraints:
    - Use FastAPI patterns
    - Include proper error handling
    - Add appropriate logging
    - Follow existing code style
    
    Provide the complete code changes needed.
    """
```

## Integration Points

### External API Integrations
- **Market Predictor**: HTTP client for health, status, metrics
- **Prometheus**: PromQL queries for metrics analysis
- **Loki**: LogQL queries for log analysis
- **GitHub API**: Repository operations, PR management
- **OpenAI/Anthropic**: LLM analysis and code generation

### Service Discovery
- **Health Endpoints**: For monitoring agent health
- **Status Endpoints**: For detailed agent status and activity
- **Webhook Endpoints**: For external alerts and triggers
- **Manual Control**: Endpoints for human oversight and intervention

### Monitoring Integration
- **Self-Monitoring**: Agent monitors its own performance
- **Target Monitoring**: Monitors market-predictor service
- **Metrics Exposure**: Exposes metrics about agent operations
- **Log Integration**: Structured logging for analysis

## Future Technical Considerations

### Scalability Improvements
- **Multi-Target Monitoring**: Support multiple services beyond market-predictor
- **Distributed Agents**: Multiple agent instances with coordination
- **Knowledge Persistence**: Database for learning and historical data
- **Advanced Analytics**: More sophisticated pattern detection

### AI/LLM Enhancements
- **Multi-Model Support**: Use different LLMs for different tasks
- **Fine-Tuned Models**: Custom models trained on specific use cases
- **Vector Knowledge Base**: Semantic search for historical solutions
- **Reinforcement Learning**: Learn from action outcomes

### Advanced Features
- **Predictive Analysis**: Predict issues before they occur
- **Automated Testing**: Generate and run tests for changes
- **Code Review**: Automated code review before PR creation
- **Performance Optimization**: Continuous performance improvement

### Security Enhancements
- **Zero-Trust Architecture**: Verify all external interactions
- **Encrypted Communication**: Secure all external API calls
- **Audit Logging**: Complete audit trail of all agent actions
- **Access Control**: Fine-grained permissions for agent operations 