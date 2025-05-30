# DevOps AI Agent - Technical Context

## Technology Stack: Universal Infrastructure Command Interface (UICI)

### Core Innovation Stack
The DevOps AI Agent leverages a revolutionary technology stack designed for intelligent, environment-agnostic infrastructure management.

## Primary Technologies

### 1. AI & LLM Integration
**LLM Provider**: Configurable (OpenAI, Anthropic, etc.)
- **Model**: `gpt-4.1-nano-2025-04-14` (from infrastructure/config/platform.yml)
- **Temperature**: `0.1` (precise, consistent responses)
- **Max Tokens**: `4000` (detailed diagnostic plans)
- **Timeout**: `60s` (reliable response timing)
- **Integration**: Direct OpenAI API integration (no LangChain dependency)

**Configuration Principle**: NO HARDCODING! All LLM settings from configuration files.

```python
# ❌ NEVER DO THIS
llm_model = "gpt-4"

# ✅ ALWAYS DO THIS  
config = UniversalConfigLoader()
llm_model = config.get_llm_config()["model"]
```

### 2. Web Framework & API
**FastAPI** - Modern async web framework
- **Async Support**: Full async/await patterns for concurrent operations
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Type Safety**: Pydantic models for request/response validation
- **Health Endpoints**: `/health`, `/metrics` for monitoring integration
- **WebSocket Support**: Real-time monitoring and status updates

### 3. Universal Infrastructure Interface
**Core Components**:
- **UniversalConfigLoader**: Centralized configuration management
- **OperationRegistry**: Dynamic operation discovery and validation
- **EnvironmentExecutor**: Environment-specific command execution
- **CommandTranslator**: Universal → environment-specific translation

**Environment Support**:
- **Local Docker**: Docker Python SDK integration
- **Oracle Cloud Infrastructure (OCI)**: OCI Python SDK
- **Kubernetes**: kubectl and Python kubernetes client
- **Future**: AWS ECS, Azure Container Instances, Google Cloud Run

### 4. Configuration Management
**Configuration File Structure**:
```
infrastructure/config/
├── platform.yml              # Global platform settings, LLM config
├── agents.yml                # Agent-specific configurations
├── environments.yml          # Environment definitions & capabilities
├── operations.yml            # Operation schemas & parameters  
└── command_translations.yml  # Environment-specific mappings
```

**Configuration Loader Architecture**:
```python
class UniversalConfigLoader:
    """Load all configurations from infrastructure/config/"""
    
    def __init__(self):
        self.base_path = Path("/config")
        self.platform_config = self._load_yaml("platform.yml")
        self.environment_config = self._load_yaml("environments.yml")
        self.operations_config = self._load_yaml("operations.yml")
    
    def get_llm_config(self):
        return self.platform_config["credentials"]["llm"]
    
    def get_current_environment(self):
        return self.platform_config["platform"]["environment"]
```

### 5. Monitoring & Observability
**Prometheus Integration**:
- **Metrics Collection**: Custom metrics for operation execution
- **Alert Rules**: Infrastructure health monitoring
- **Grafana Dashboards**: Visual monitoring and alerting

**Loki Integration**:
- **Log Aggregation**: Centralized log collection and analysis
- **Structured Logging**: JSON-formatted logs for analysis
- **Log Analysis**: AI-powered log pattern recognition

**Alertmanager Integration**:
- **Webhook Reception**: Receives alerts from Alertmanager
- **Alert Processing**: AI analysis of alert context and severity
- **Recovery Orchestration**: Automated response to infrastructure alerts

### 6. Containerization & Deployment
**Docker**:
- **Multi-stage Build**: Optimized container images
- **Health Checks**: Container health monitoring
- **Security**: Non-root user, minimal attack surface
- **Configuration Mounting**: External config files mounted at runtime

**Docker Compose**:
- **Service Orchestration**: Multi-service deployment
- **Environment Variables**: Minimal environment configuration
- **Volume Management**: Configuration and data persistence
- **Network Configuration**: Service communication setup

## Architecture Patterns

### 1. Configuration-Driven Everything
**Principle**: All behavior driven by configuration files, zero hardcoding

```python
class ConfigurationDrivenPattern:
    def __init__(self):
        # Load ALL configuration from files
        self.config = UniversalConfigLoader()
        self.llm_config = self.config.get_llm_config()
        self.environment = self.config.get_current_environment()
        self.operations = self.config.get_available_operations()
    
    # All values come from configuration
    def create_llm_client(self):
        return openai.AsyncOpenAI(
            api_key=self.llm_config["api_key"],
            timeout=self.llm_config["timeout"]
        )
```

### 2. Environment Abstraction Layer
**Principle**: Same operations work across any environment through intelligent translation

```python
class EnvironmentAbstractionPattern:
    """Universal operation execution across environments"""
    
    async def execute_operation(self, operation):
        """Same operation works in Docker, Oracle Cloud, Kubernetes"""
        
        # Universal operation definition
        universal_op = {
            "name": "get_logs",
            "parameters": {
                "target": "market-predictor",
                "lines": 100,
                "level": "error"
            }
        }
        
        # Environment-specific translation
        executor = self.get_environment_executor()
        return await executor.execute(universal_op)
```

### 3. AI-Driven Dynamic Operations
**Principle**: AI generates operations based on context, not limited to predefined actions

```python
class DynamicOperationPattern:
    """AI generates operations based on problem context"""
    
    async def create_diagnostic_plan(self, context):
        """AI creates context-aware diagnostic sequence"""
        
        prompt = f"""
        You are a Senior Site Reliability Engineer.
        
        ## INCIDENT CONTEXT
        Service: {context['service']}
        Environment: {context['environment']}
        Alert: {context['alert']}
        
        ## AVAILABLE OPERATIONS
        {self._format_operations(context['available_operations'])}
        
        Generate a systematic diagnostic plan with phases:
        1. IMMEDIATE TRIAGE (0-2 min)
        2. PROBLEM ISOLATION (2-5 min)
        3. ROOT CAUSE ANALYSIS (5-10 min)
        4. RESOLUTION & VALIDATION (10+ min)
        """
        
        response = await self.llm_client.chat.completions.create(
            model=self.llm_config["model"],
            messages=[{"role": "system", "content": prompt}]
        )
        
        return self._parse_operations(response.choices[0].message.content)
```

### 4. Fail-Fast Configuration
**Principle**: Application fails immediately if configuration is incomplete

```python
class FailFastPattern:
    def __init__(self):
        try:
            self.config = UniversalConfigLoader()
            self._validate_configuration()
        except Exception as e:
            raise RuntimeError(f"❌ CRITICAL: Cannot start without configuration: {e}")
    
    def _validate_configuration(self):
        required = ["llm_provider", "llm_model", "environment"]
        missing = [key for key in required if not self.config.get(key)]
        if missing:
            raise ValueError(f"Missing required configuration: {missing}")
```

## Environment-Specific Integration

### 1. Local Docker Environment
**Technologies**:
- **Docker Python SDK**: Native Python integration with Docker Engine
- **Docker Compose**: Multi-service orchestration
- **Docker Socket**: Container management via `/var/run/docker.sock`

**Operation Translation**:
```python
class DockerExecutor:
    async def execute(self, operation):
        if operation["name"] == "get_logs":
            return await self._docker_logs(operation["parameters"])
        elif operation["name"] == "restart_service":
            return await self._docker_restart(operation["parameters"])
    
    async def _docker_logs(self, params):
        container = self.docker_client.containers.get(params["target"])
        logs = container.logs(
            tail=params.get("lines", 100),
            since=params.get("since"),
            timestamps=params.get("timestamps", True)
        )
        return {"output": logs.decode(), "success": True}
```

### 2. Oracle Cloud Infrastructure (OCI)
**Technologies**:
- **OCI Python SDK**: Official Oracle Cloud SDK
- **OCI CLI**: Command-line interface for complex operations
- **Container Instances**: OCI container services
- **Logging Service**: Centralized log management

**Operation Translation**:
```python
class OCIExecutor:
    async def execute(self, operation):
        if operation["name"] == "get_logs":
            return await self._oci_logs(operation["parameters"])
        elif operation["name"] == "restart_service":
            return await self._oci_restart(operation["parameters"])
    
    async def _oci_logs(self, params):
        logs_client = oci.logging.LoggingManagementClient(self.config)
        response = logs_client.search_logs(
            search_logs_details=oci.logging.models.SearchLogsDetails(
                time_start=params.get("since"),
                time_end=datetime.now(),
                search_query=f"logContent='{params.get('filter', '')}'"
            )
        )
        return {"output": response.data, "success": True}
```

### 3. Kubernetes
**Technologies**:
- **kubectl**: Command-line tool for Kubernetes
- **Python Kubernetes Client**: Official Kubernetes Python library
- **Helm**: Package management for Kubernetes
- **Custom Resource Definitions**: Extended Kubernetes functionality

**Operation Translation**:
```python
class KubernetesExecutor:
    async def execute(self, operation):
        if operation["name"] == "get_logs":
            return await self._k8s_logs(operation["parameters"])
        elif operation["name"] == "restart_service":
            return await self._k8s_restart(operation["parameters"])
    
    async def _k8s_logs(self, params):
        v1 = kubernetes.client.CoreV1Api()
        pod_list = v1.list_namespaced_pod(
            namespace="default",
            label_selector=f"app={params['target']}"
        )
        
        logs = []
        for pod in pod_list.items:
            pod_logs = v1.read_namespaced_pod_log(
                name=pod.metadata.name,
                namespace="default",
                tail_lines=params.get("lines", 100)
            )
            logs.append(pod_logs)
        
        return {"output": "\n".join(logs), "success": True}
```

## Development Environment

### 1. Local Development Setup
**Requirements**:
- Python 3.9+
- Docker Desktop
- Virtual Environment (venv)
- Infrastructure configuration files

**Development Workflow**:
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
export AGENTS_CONFIG="/path/to/infrastructure/config/agents.yml"

# Run development server
uvicorn src.agent.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. Testing Environment
**Testing Stack**:
- **pytest**: Test framework with async support
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for testing
- **Docker SDK**: Container management for integration tests

**Test Categories**:
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service integration testing
- **Environment Tests**: Cross-environment operation testing
- **AI Reasoning Tests**: LLM response validation

### 3. Production Deployment
**Container Orchestration**:
- **Docker Compose**: Multi-service deployment
- **Health Checks**: Container and application health monitoring
- **Volume Management**: Configuration and data persistence
- **Network Security**: Service isolation and communication

**Configuration Management**:
- **External Configs**: Configuration files mounted from host
- **Environment Detection**: Auto-detect deployment environment
- **Secret Management**: Secure handling of API keys and credentials

## Performance & Scalability

### 1. Async Architecture
**FastAPI + asyncio**:
- **Non-blocking I/O**: Concurrent request handling
- **Connection Pooling**: Efficient resource utilization
- **Background Tasks**: Async background processing
- **WebSocket Support**: Real-time communication

### 2. Caching Strategy
**Configuration Caching**:
- **In-Memory Cache**: Fast configuration access
- **TTL-based Refresh**: Automatic cache invalidation
- **Fallback Mechanism**: Graceful degradation on cache miss

**AI Response Caching**:
- **Operation Result Cache**: Cache common operation results
- **Context-based Cache**: Cache based on problem context
- **Cache Invalidation**: Smart cache invalidation strategies

### 3. Resource Management
**Memory Management**:
- **Connection Pooling**: Efficient connection reuse
- **Garbage Collection**: Proper resource cleanup
- **Memory Limits**: Container memory constraints

**CPU Optimization**:
- **Async Processing**: Non-blocking operation execution
- **Background Workers**: CPU-intensive tasks in background
- **Process Optimization**: Efficient algorithm implementation

## Security Considerations

### 1. Container Security
**Security Practices**:
- **Non-root User**: Run container as non-privileged user
- **Minimal Base Image**: Reduce attack surface
- **Security Scanning**: Regular vulnerability assessment
- **Network Isolation**: Service communication security

### 2. API Security
**Authentication & Authorization**:
- **API Key Management**: Secure API key handling
- **Rate Limiting**: Request rate limiting
- **Input Validation**: Comprehensive input sanitization
- **Audit Logging**: Complete operation audit trail

### 3. Configuration Security
**Secret Management**:
- **Environment Variables**: Secure secret injection
- **File Permissions**: Restrictive configuration file permissions
- **Encryption**: Sensitive data encryption at rest
- **Access Control**: Limited configuration access

## Integration Technologies

### 1. Monitoring Integration
**Prometheus**:
- **Custom Metrics**: Operation execution metrics
- **Health Metrics**: Application health indicators
- **Performance Metrics**: Response time and throughput

**Grafana**:
- **Dashboards**: Visual monitoring interfaces
- **Alerting**: Visual alert management
- **Data Visualization**: Performance and health visualization

### 2. Logging Integration
**Structured Logging**:
- **JSON Format**: Machine-readable log format
- **Correlation IDs**: Request tracing across services
- **Log Levels**: Appropriate log level usage
- **Performance Logging**: Operation performance tracking

**Loki Integration**:
- **Log Aggregation**: Centralized log collection
- **Log Analysis**: Pattern recognition and analysis
- **Alert Generation**: Log-based alerting

## Future Technology Roadmap

### Phase 1: Foundation (Current)
- **Configuration Management**: Universal configuration loading
- **Environment Abstraction**: Docker, OCI, Kubernetes support
- **AI Integration**: GPT-4 powered diagnostic reasoning
- **Basic Operations**: Restart, logs, resource monitoring

### Phase 2: Intelligence Enhancement (Next 3 months)
- **Machine Learning**: Pattern recognition and learning
- **Predictive Analytics**: Problem prediction capabilities
- **Advanced Operations**: Complex multi-service operations
- **Performance Optimization**: Intelligent resource management

### Phase 3: Platform Expansion (Next 6 months)
- **Cloud Provider Integration**: AWS, Azure, GCP support
- **Kubernetes Operators**: Custom Kubernetes controllers
- **Service Mesh Integration**: Istio, Linkerd support
- **Advanced Security**: Security scanning and compliance

### Phase 4: Ecosystem Integration (Next 12 months)
- **CI/CD Integration**: Jenkins, GitLab CI, GitHub Actions
- **Database Management**: Database operation automation
- **Cost Optimization**: Intelligent resource cost management
- **Compliance Automation**: Automated compliance checking

This technical architecture enables the Universal Infrastructure Command Interface to provide intelligent, environment-agnostic infrastructure management while maintaining security, performance, and scalability across any deployment environment. 