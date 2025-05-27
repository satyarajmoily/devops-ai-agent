# System Patterns - DevOps AI Agent

## System Architecture

### High-Level DevOps AI Agent Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Market Predictor│────│ DevOps Monitoring│───│  LangChain LLM  │
│ Infrastructure  │    │     System      │    │   (DevOps AI)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Docker API     │────│ Infrastructure  │
                       │ (Orchestration) │    │   Testing Env   │
                       └─────────────────┘    └─────────────────┘
```

### Agent Application Architecture
```
src/agent/
├── main.py                     # FastAPI application factory
├── core/                       # Core agent logic
│   ├── monitoring.py          # Monitoring orchestration
│   ├── analysis.py            # Issue analysis engine
│   ├── actions.py             # Action execution engine
│   └── learning.py            # Learning and adaptation
├── services/                   # External service integrations
│   ├── prometheus_client.py   # Prometheus integration
│   ├── loki_client.py         # Loki log client
│   ├── github_client.py       # GitHub API client
│   └── predictor_client.py    # Market predictor communication
├── agents/                     # LangChain agent components
│   ├── analyzer.py            # Analysis agent
│   ├── coder.py               # Code generation agent
│   └── tester.py              # Testing agent
├── models/                     # Data models
│   ├── alerts.py              # Alert and monitoring models
│   ├── analysis.py            # Analysis result models
│   └── actions.py             # Action and change models
└── config/                     # Configuration
    ├── settings.py            # Pydantic settings
    ├── prompts.py             # LLM prompts
    └── logging.py             # Logging configuration
```

## Key Technical Decisions

### 1. Autonomous Agent Framework: LangChain
**Decision**: Use LangChain as the core AI/LLM framework
**Reasoning**:
- **Agent Orchestration**: Built-in support for autonomous agent patterns
- **LLM Integration**: Seamless integration with multiple LLM providers
- **Memory Management**: Built-in memory patterns for learning and context
- **Tool Integration**: Easy integration with external tools and APIs
- **Extensibility**: Modular design allows for complex agent workflows

### 2. Service Architecture: FastAPI + Agent Core
**Decision**: Separate FastAPI web service from autonomous agent core
**Reasoning**:
- **Service Exposure**: REST API for health, status, and manual triggers
- **Separation of Concerns**: Web service logic separate from agent logic
- **Monitoring Integration**: Standard endpoints for external monitoring
- **Control Interface**: Human oversight and intervention capabilities

### 3. Monitoring Strategy: Multi-Source Integration
**Decision**: Integrate with Prometheus, Loki, and direct HTTP monitoring
**Reasoning**:
- **Comprehensive Coverage**: Multiple data sources provide complete picture
- **Redundancy**: Backup monitoring if one source fails
- **Rich Context**: Combine metrics, logs, and direct health checks
- **Pattern Detection**: Multiple data streams enable better anomaly detection

### 4. Safety-First Approach: Testing Before Deployment
**Decision**: All changes must pass local testing before PR creation
**Reasoning**:
- **Risk Mitigation**: Prevent deployment of broken or harmful changes
- **Quality Assurance**: Ensure all changes meet quality standards
- **Trust Building**: Build confidence in autonomous system
- **Learning Data**: Test results provide feedback for improvement

## Design Patterns

### 1. Agent Orchestration Pattern
```python
class AutonomousAgent:
    def __init__(self, monitors: List[Monitor], analyzers: List[Analyzer], 
                 actors: List[Actor]):
        self.monitors = monitors
        self.analyzers = analyzers
        self.actors = actors
    
    async def run_cycle(self):
        # Monitor -> Analyze -> Act cycle
        observations = await self.collect_observations()
        analysis = await self.analyze_observations(observations)
        actions = await self.plan_actions(analysis)
        await self.execute_actions(actions)
```

### 2. LangChain Agent Integration Pattern
```python
class AnalysisAgent:
    def __init__(self, llm: LLM, tools: List[Tool]):
        self.agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
        )
    
    async def analyze_issue(self, context: Dict) -> AnalysisResult:
        # Use LLM to analyze monitoring data and generate insights
        prompt = self.build_analysis_prompt(context)
        result = await self.agent.arun(prompt)
        return AnalysisResult.parse(result)
```

### 3. Service Client Pattern
```python
class PredictorClient:
    def __init__(self, base_url: str, timeout: int = 30):
        self.session = httpx.AsyncClient(timeout=timeout)
        self.base_url = base_url
    
    async def health_check(self) -> HealthStatus:
        response = await self.session.get(f"{self.base_url}/health")
        return HealthStatus.parse_obj(response.json())
    
    async def get_metrics(self) -> PrometheusMetrics:
        response = await self.session.get(f"{self.base_url}/metrics")
        return PrometheusMetrics.parse(response.text)
```

### 4. Action Validation Pattern
```python
class ActionValidator:
    def __init__(self, testing_env: TestingEnvironment):
        self.testing_env = testing_env
    
    async def validate_action(self, action: Action) -> ValidationResult:
        # Create isolated test environment
        test_env = await self.testing_env.create_isolated_env()
        
        try:
            # Apply action in test environment
            await test_env.apply_action(action)
            
            # Run validation tests
            results = await test_env.run_tests()
            
            return ValidationResult(
                success=results.all_passed(),
                test_results=results,
                safe_to_deploy=results.meets_safety_criteria()
            )
        finally:
            await test_env.cleanup()
```

## Component Relationships

### 1. Monitoring Flow
```
External Sources → Service Clients → Monitoring Core → Analysis Engine
     ↓                  ↓                 ↓                  ↓
Prometheus         HTTP Clients     Data Collection    LangChain Agents
Loki Logs          Status Checks    Anomaly Detection  Root Cause Analysis
Direct Health      Performance      Alert Generation   Solution Generation
```

### 2. Action Execution Flow
```
Analysis Results → Action Planning → Validation → GitHub Integration
       ↓               ↓               ↓              ↓
   Issue Insights   Action Generation  Local Testing  PR Creation
   Recommendations  Code Changes       Safety Checks  Deployment
   Priority Scores  Configuration      Quality Gates  Monitoring
```

### 3. Learning Loop
```
Action Outcomes → Feedback Analysis → Strategy Updates → Improved Decisions
       ↓                ↓                  ↓                   ↓
   Success/Failure   Pattern Recognition  Agent Training      Better Actions
   Performance Data  Correlation Analysis Model Updates       Higher Quality
   User Feedback     Learning Algorithms  Prompt Refinement   Safer Changes
```

## Error Handling Patterns

### 1. Graceful Degradation
```python
class MonitoringService:
    async def collect_metrics(self):
        try:
            # Try Prometheus first
            return await self.prometheus_client.get_metrics()
        except PrometheusError:
            try:
                # Fallback to direct health checks
                return await self.direct_health_check()
            except HealthCheckError:
                # Minimal monitoring mode
                return await self.basic_status_check()
```

### 2. Circuit Breaker Pattern
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError()
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
```

### 3. Retry with Exponential Backoff
```python
async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            return await func()
        except RetryableError as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
    
    raise MaxRetriesExceededError()
```

## Performance Patterns

### 1. Async Processing
```python
class AutonomousAgent:
    async def run_monitoring_loop(self):
        tasks = [
            self.monitor_health(),
            self.collect_metrics(),
            self.analyze_logs(),
            self.check_performance()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self.process_monitoring_results(results)
```

### 2. Caching Strategy
```python
class CachedAnalysisService:
    def __init__(self, cache_ttl: int = 300):
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
    
    async def analyze_metrics(self, metrics_hash: str) -> AnalysisResult:
        if metrics_hash in self.cache:
            return self.cache[metrics_hash]
        
        result = await self.perform_analysis(metrics_hash)
        self.cache[metrics_hash] = result
        return result
```

### 3. Background Task Management
```python
class BackgroundTaskManager:
    def __init__(self):
        self.tasks = set()
    
    def create_task(self, coro):
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task
    
    async def shutdown(self):
        await asyncio.gather(*self.tasks, return_exceptions=True)
```

## Security Patterns

### 1. LLM Input Sanitization
```python
class SecureLLMClient:
    def __init__(self, llm: LLM):
        self.llm = llm
        self.sanitizer = InputSanitizer()
    
    async def generate_response(self, prompt: str) -> str:
        # Sanitize input to prevent prompt injection
        safe_prompt = self.sanitizer.sanitize(prompt)
        
        # Add safety constraints to prompt
        constrained_prompt = self.add_safety_constraints(safe_prompt)
        
        response = await self.llm.agenerate([constrained_prompt])
        
        # Validate response before returning
        return self.validate_response(response)
```

### 2. GitHub API Security
```python
class SecureGitHubClient:
    def __init__(self, token: str):
        self.client = Github(token)
        self.allowed_repos = set(settings.ALLOWED_REPOSITORIES)
    
    async def create_pr(self, repo_name: str, pr_data: PRData) -> PullRequest:
        if repo_name not in self.allowed_repos:
            raise UnauthorizedRepositoryError(repo_name)
        
        # Validate PR content for safety
        self.validate_pr_content(pr_data)
        
        return await self.client.create_pull_request(repo_name, pr_data)
```

### 3. Sandbox Isolation
```python
class IsolatedTestEnvironment:
    def __init__(self):
        self.container_client = docker.from_env()
    
    async def create_test_environment(self) -> TestEnvironment:
        # Create isolated Docker container for testing
        container = self.container_client.containers.run(
            image="test-environment:latest",
            detach=True,
            network_mode="none",  # No network access
            mem_limit="512m",     # Memory limit
            cpu_period=100000,    # CPU limit
            cpu_quota=50000
        )
        
        return TestEnvironment(container)
``` 