# DevOps AI Agent - System Patterns & Architecture

## Revolutionary Architecture: Universal Infrastructure Command Interface (UICI)

### Core Innovation
The DevOps AI Agent has evolved from traditional hardcoded operations to a revolutionary Universal Infrastructure Command Interface that enables intelligent, environment-agnostic infrastructure management across any platform.

### Architecture Evolution

#### ❌ OLD: Hardcoded, Environment-Specific
```python
# BAD: Environment lock-in
def restart_service(service_name):
    subprocess.run(f"docker restart {service_name}")

def get_logs(service_name):
    subprocess.run(f"docker logs {service_name}")
```

#### ✅ NEW: Universal, AI-Driven
```python
# GOOD: Environment-agnostic
async def execute_operation(operation):
    return await universal_interface.execute(operation)

# AI generates operations dynamically
operation = {
    "name": "restart_service",
    "parameters": {"target": "market-predictor", "strategy": "graceful"}
}
```

## UICI Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AI Reasoning  │───▶│  Universal UICI  │───▶│   Environment   │
│    Engine       │    │   Interface      │    │   Executors     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  Configuration   │    │ Docker/OCI/K8s  │
                       │   Management     │    │   Commands      │
                       └──────────────────┘    └─────────────────┘
```

## Core System Patterns

### 1. Configuration-Driven Everything Pattern
**Principle**: All behavior is driven by configuration files, no hardcoded values anywhere

```python
class ConfigurationPattern:
    """Everything comes from infrastructure/config/ directory"""
    
    def __init__(self):
        # NO HARDCODING - Everything from config
        self.config = UniversalConfigLoader()
        self.llm_config = self.config.get_llm_config()
        self.environment = self.config.get_current_environment()
        self.operations = self.config.get_available_operations()
    
    # ❌ NEVER DO THIS
    def bad_pattern(self):
        model = "gpt-4"  # HARDCODED!
        timeout = 30     # HARDCODED!
    
    # ✅ ALWAYS DO THIS
    def good_pattern(self):
        model = self.llm_config["model"]        # FROM CONFIG!
        timeout = self.llm_config["timeout"]   # FROM CONFIG!
```

### 2. Universal Operation Pattern
**Principle**: Same operation works across any environment through intelligent translation

```python
class UniversalOperationPattern:
    """Environment-agnostic operation execution"""
    
    async def execute_anywhere(self, operation):
        """Same operation works in Docker, Oracle Cloud, Kubernetes"""
        
        # Universal operation definition
        universal_op = {
            "name": "get_logs",
            "parameters": {
                "target": "market-predictor",
                "lines": 100,
                "level": "error",
                "since": "10m"
            }
        }
        
        # Translates to environment-specific commands:
        # Docker: docker logs market-predictor --tail 100 --since 10m | grep ERROR
        # Oracle Cloud: oci logging search-logs --query "ERROR" --limit 100
        # Kubernetes: kubectl logs deployment/market-predictor --tail=100 | grep ERROR
        
        return await self.universal_interface.execute(universal_op)
```

### 3. AI-Driven Dynamic Operation Generation Pattern
**Principle**: AI generates operations based on context, not limited to predefined actions

```python
class DynamicOperationPattern:
    """AI generates operations based on problem context"""
    
    async def ai_diagnostic_reasoning(self, alert_context):
        """AI creates custom diagnostic sequence"""
        
        # AI generates context-aware operations
        ai_operations = [
            {
                "phase": "immediate_triage",
                "operation": "check_resources",
                "parameters": {
                    "target": "market-predictor",
                    "metrics": ["cpu", "memory"],
                    "format": "summary"
                },
                "reasoning": "Quick resource check to rule out resource exhaustion"
            },
            {
                "phase": "problem_isolation",
                "operation": "get_logs",
                "parameters": {
                    "target": "market-predictor",
                    "lines": 50,
                    "level": "error",
                    "since": "10m",
                    "filter": "OutOfMemory|Exception"
                },
                "reasoning": "Check for recent error patterns indicating memory issues"
            },
            {
                "phase": "resolution",
                "operation": "restart_service",
                "parameters": {
                    "target": "market-predictor",
                    "strategy": "graceful",
                    "health_check": True,
                    "backup": True
                },
                "reasoning": "Restart service based on memory leak detection"
            }
        ]
        
        return ai_operations
```

### 4. Environment Abstraction Pattern
**Principle**: Same AI logic works across any deployment environment

```python
class EnvironmentAbstractionPattern:
    """Environment detection and adaptation"""
    
    def __init__(self):
        self.environment = self.detect_environment()
        self.executor = self.create_executor()
    
    def detect_environment(self):
        """Auto-detect current deployment environment"""
        if os.path.exists("/var/run/docker.sock"):
            return "local_docker"
        elif os.environ.get("OCI_CONFIG_FILE"):
            return "oracle_cloud"
        elif os.environ.get("KUBECONFIG"):
            return "kubernetes"
        return "unknown"
    
    def create_executor(self):
        """Factory pattern for environment-specific executors"""
        executors = {
            "local_docker": DockerExecutor,
            "oracle_cloud": OCIExecutor,
            "kubernetes": KubernetesExecutor
        }
        return executors[self.environment](self.config)
```

### 5. Fail-Fast Configuration Pattern
**Principle**: Application fails immediately if configuration is incomplete

```python
class FailFastPattern:
    """Immediate failure for missing configuration"""
    
    def __init__(self):
        try:
            self.config = self.load_configuration()
            self.validate_required_settings()
        except Exception as e:
            # FAIL FAST - Don't start with incomplete config
            raise RuntimeError(f"❌ CRITICAL: Cannot start without proper configuration: {e}")
    
    def validate_required_settings(self):
        """Validate all required settings are present"""
        required = ["llm_provider", "llm_model", "environment", "operations"]
        missing = [key for key in required if not self.config.get(key)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {missing}")
```

## Component Architecture Patterns

### 1. Configuration Management System

```python
class ConfigurationArchitecture:
    """Centralized configuration management"""
    
    # File Structure Pattern
    CONFIG_STRUCTURE = {
        "infrastructure/config/": {
            "platform.yml": "Global platform settings, LLM config, credentials",
            "agents.yml": "Agent-specific configurations",
            "environments.yml": "Environment definitions and capabilities", 
            "operations.yml": "Operation schemas and parameters",
            "command_translations.yml": "Environment-specific command mappings"
        }
    }
    
    # Configuration Loader Pattern
    class UniversalConfigLoader:
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

### 2. Operation Registry System

```python
class OperationRegistryArchitecture:
    """Dynamic operation discovery and validation"""
    
    class OperationRegistry:
        def __init__(self):
            self.operations = self._load_operations_from_config()
        
        def get_available_operations(self, environment):
            """Get operations available in specific environment"""
            env_capabilities = self.config.get_environment_capabilities(environment)
            return [op for op in self.operations if op in env_capabilities]
        
        def get_operation_schema(self, operation_name):
            """Get parameter schema for operation"""
            return self.operations[operation_name]
        
        def validate_operation(self, operation):
            """Validate operation against schema"""
            schema = self.get_operation_schema(operation["name"])
            return self._validate_parameters(operation["parameters"], schema)
```

### 3. AI Intelligence Engine

```python
class AIIntelligenceArchitecture:
    """Sophisticated AI reasoning for infrastructure problems"""
    
    class AIdiagnosticPlanner:
        def __init__(self, config):
            self.config = config
            self.llm_config = config.get_llm_config()  # NO HARDCODING!
            self.llm_client = self._create_llm_client()
        
        async def create_diagnostic_plan(self, context):
            """Generate intelligent multi-phase diagnostic plan"""
            
            prompt = self._build_comprehensive_prompt(context)
            
            response = await self.llm_client.chat.completions.create(
                model=self.llm_config["model"],      # FROM CONFIG!
                temperature=self.llm_config["temperature"],  # FROM CONFIG!
                max_tokens=self.llm_config["max_tokens"],    # FROM CONFIG!
                messages=[{"role": "system", "content": prompt}]
            )
            
            return self._parse_diagnostic_plan(response)
        
        def _build_comprehensive_prompt(self, context):
            """Build detailed prompt with full environment context"""
            return f"""
            You are a Senior Site Reliability Engineer with expertise in {context['environment']['platform']}.
            
            ## INCIDENT ANALYSIS
            Service: {context['incident']['service']}
            Symptoms: {context['incident']['symptoms']}
            Environment: {context['environment']['platform']}
            
            ## AVAILABLE OPERATIONS
            {self._format_operations_for_ai(context['available_operations'])}
            
            Generate a systematic diagnostic plan with phases:
            1. IMMEDIATE TRIAGE (0-2 min)
            2. PROBLEM ISOLATION (2-5 min)  
            3. ROOT CAUSE ANALYSIS (5-10 min)
            4. RESOLUTION & VALIDATION (10+ min)
            """
```

### 4. Environment Executor System

```python
class EnvironmentExecutorArchitecture:
    """Environment-specific command execution"""
    
    class ExecutorFactory:
        @staticmethod
        def create_executor(environment, config):
            executors = {
                "local_docker": DockerExecutor,
                "oracle_cloud": OCIExecutor,
                "kubernetes": KubernetesExecutor
            }
            return executors[environment](config)
    
    class DockerExecutor:
        async def execute(self, operation):
            op_name = operation["name"]
            params = operation["parameters"]
            
            if op_name == "restart_service":
                return await self._restart_docker_service(params)
            elif op_name == "get_logs":
                return await self._get_docker_logs(params)
    
    class OCIExecutor:
        async def execute(self, operation):
            # Translate operations to OCI API calls
            return await self._execute_oci_operation(operation)
```

## Data Flow Patterns

### 1. Alert Processing Flow
```
Alert Reception → Context Gathering → AI Analysis → Operation Generation → Environment Execution → Result Validation
```

### 2. Configuration Loading Flow
```
Application Start → Universal Config Loader → Environment Detection → Operation Registry → Executor Factory
```

### 3. Operation Execution Flow
```
AI Operation → Universal Interface → Environment Translator → Specific Executor → Command Execution → Result Return
```

## Security Patterns

### 1. Command Validation Pattern
```python
class SecurityPattern:
    DANGEROUS_COMMANDS = [
        "rm -rf", "dd if=", "mkfs", "fdisk",
        "shutdown", "reboot", "kill -9 1"
    ]
    
    def validate_command(self, command, service_config):
        # Validate against blacklist
        # Check service capabilities
        # Verify user permissions
        # Add audit logging
        pass
```

### 2. Parameter Sanitization Pattern
```python
class ParameterSanitizationPattern:
    def sanitize_parameters(self, operation):
        # SQL injection prevention
        # Command injection prevention
        # Path traversal prevention
        # Input validation
        pass
```

## Monitoring & Observability Patterns

### 1. Operation Execution Metrics
```python
class MetricsPattern:
    def record_operation_metrics(self, operation, result, duration):
        metrics = {
            "operation_name": operation["name"],
            "environment": self.environment,
            "success": result["success"],
            "duration_seconds": duration,
            "timestamp": datetime.now()
        }
        self.metrics_collector.record(metrics)
```

### 2. AI Decision Logging
```python
class AIDecisionLoggingPattern:
    def log_ai_decision(self, context, decision, reasoning):
        log_entry = {
            "incident_context": context,
            "ai_decision": decision,
            "reasoning": reasoning,
            "confidence": decision.get("confidence"),
            "timestamp": datetime.now()
        }
        self.decision_logger.log(log_entry)
```

## Error Handling Patterns

### 1. Graceful Degradation Pattern
```python
class GracefulDegradationPattern:
    async def execute_with_fallback(self, operation):
        try:
            return await self.primary_executor.execute(operation)
        except Exception as e:
            # Log the error
            self.logger.error(f"Primary execution failed: {e}")
            
            # Try fallback approaches
            return await self.fallback_executor.execute(operation)
```

### 2. Circuit Breaker Pattern
```python
class CircuitBreakerPattern:
    def __init__(self):
        self.failure_count = 0
        self.circuit_open = False
        self.last_failure_time = None
    
    async def execute_with_circuit_breaker(self, operation):
        if self.circuit_open:
            if self._should_attempt_reset():
                self.circuit_open = False
            else:
                raise CircuitBreakerOpenException()
        
        try:
            result = await self.executor.execute(operation)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.threshold:
                self.circuit_open = True
            raise
```

## Testing Patterns

### 1. Environment Testing Pattern
```python
class EnvironmentTestingPattern:
    async def test_operation_across_environments(self, operation):
        environments = ["local_docker", "oracle_cloud", "kubernetes"]
        
        for env in environments:
            interface = UniversalInfrastructureInterface()
            interface.environment = env
            
            result = await interface.execute_operation(operation)
            assert result["success"] is True
```

### 2. AI Reasoning Testing Pattern
```python
class AIReasoningTestingPattern:
    async def test_ai_diagnostic_quality(self, alert_scenario):
        planner = AIdiagnosticPlanner(config)
        context = await self._generate_test_context(alert_scenario)
        
        diagnostic_plan = await planner.create_diagnostic_plan(context)
        
        # Validate plan structure
        assert len(diagnostic_plan) >= 3
        assert all("reasoning" in op for op in diagnostic_plan)
        assert all("phase" in op for op in diagnostic_plan)
```

## Key Design Principles

### 1. Zero Hardcoding
- All values come from configuration files
- No default values in code
- Fail-fast if configuration is incomplete

### 2. Environment Agnostic
- Same operations work across any platform
- Universal operation interface
- Environment-specific translation layer

### 3. AI-Driven Intelligence
- Dynamic operation generation
- Context-aware decision making
- Creative problem-solving capability

### 4. Configuration-Driven
- Single source of truth in infrastructure/config/
- Centralized configuration management
- Environment detection and adaptation

### 5. Fail-Fast & Observable
- Immediate failure for invalid configuration
- Comprehensive logging and metrics
- Clear error messages with context

This architecture represents a paradigm shift from traditional hardcoded DevOps automation to intelligent, adaptive, multi-environment infrastructure management through the Universal Infrastructure Command Interface. 