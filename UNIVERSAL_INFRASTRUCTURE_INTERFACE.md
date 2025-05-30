# Universal Infrastructure Command Interface (UICI)

> **A Revolutionary Approach to Environment-Agnostic Infrastructure Management**

## 🎯 Executive Summary

The Universal Infrastructure Command Interface (UICI) eliminates hardcoded infrastructure operations and enables AI agents to work seamlessly across any environment (local Docker, Oracle Cloud, Kubernetes, etc.) through intelligent operation abstraction and dynamic command generation.

## ❌ Current Problems

### 1. **Hardcoded Operations**
```python
# BAD: Hardcoded methods limit AI creativity
async def restart(self, service: str):     # Only restart
async def logs(self, service: str):        # Only logs  
async def scale(self, service: str):       # Only scale
```

### 2. **Environment Lock-in**
```bash
# BAD: Docker-specific commands
docker restart market-predictor
docker logs market-predictor --tail 100
```

### 3. **Configuration Hardcoding**
```python
# BAD: Hardcoded values scattered everywhere
llm_model = "gpt-4"  # Should come from config
provider = "openai"  # Should come from config
```

### 4. **Limited AI Intelligence**
- AI can only perform predefined operations
- No creative problem-solving capability
- Environment-specific knowledge required

## ✅ Solution: Universal Infrastructure Command Interface

### **Core Principles**

1. **No Hardcoded Operations** - AI generates any operation dynamically
2. **Environment Abstraction** - Same operations work everywhere
3. **Configuration-Driven** - All settings from `infrastructure/config/`
4. **AI Intelligence** - Smart diagnostic reasoning and creative problem-solving
5. **Extensible** - Easy to add new environments and operations

## 🏗️ Architecture Overview

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

## 📋 Implementation Phases

## **Phase 1: Configuration Centralization** (Week 1)
**Goal**: Eliminate all hardcoded configurations

### **1.1 Configuration Structure**
```yaml
# infrastructure/config/platform.yml - SINGLE SOURCE OF TRUTH
platform:
  name: "Autonomous Trading Builder"
  version: "1.0.0"
  environment: "development"

credentials:
  llm:
    openai_api_key: "${OPENAI_API_KEY}"
    provider: "openai"
    model: "gpt-4.1-nano-2025-04-14"  # NO HARDCODING IN CODE!
    temperature: 0.1
    max_tokens: 4000
    timeout: 60

# infrastructure/config/environments.yml
environments:
  local_docker:
    type: "docker_compose"
    capabilities: ["restart_service", "get_logs", "execute_command"]
    
  oracle_cloud:
    type: "oci"
    capabilities: ["restart_service", "get_logs", "scale_service", "get_metrics"]
    
  kubernetes:
    type: "k8s" 
    capabilities: ["restart_service", "get_logs", "scale_service", "rolling_update"]
```

### **1.2 Configuration Loader Enhancement**
```python
class UniversalConfigLoader:
    """Load all configurations from infrastructure/config/"""
    
    def __init__(self):
        self.base_path = Path("/config")  # infrastructure/config mounted here
        self.platform_config = self._load_yaml("platform.yml")
        self.environment_config = self._load_yaml("environments.yml")
        self.agents_config = self._load_yaml("agents.yml")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM config from platform.yml - NO HARDCODING!"""
        return self.platform_config["credentials"]["llm"]
    
    def get_current_environment(self) -> str:
        """Get current environment from config"""
        return self.platform_config["platform"]["environment"]
    
    def get_environment_capabilities(self, env_name: str) -> List[str]:
        """Get what operations are available in this environment"""
        return self.environment_config["environments"][env_name]["capabilities"]
```

### **1.3 Critical Rule: NO HARDCODING**
```python
# ❌ NEVER DO THIS - NO HARDCODED VALUES!
llm_model = "gpt-4"
provider = "openai"
default_timeout = 30

# ✅ ALWAYS DO THIS - GET FROM CONFIG!
config = UniversalConfigLoader()
llm_model = config.get_llm_config()["model"] 
provider = config.get_llm_config()["provider"]
default_timeout = config.get_operation_config("timeout")
```

---

## **Phase 2: Universal Operation Interface** (Week 2)
**Goal**: Replace hardcoded methods with dynamic operations

### **2.1 Operation Registry**
```python
class OperationRegistry:
    """Dynamic registry of available operations"""
    
    def __init__(self):
        self.operations = self._load_operations_from_config()
    
    def _load_operations_from_config(self) -> Dict[str, Any]:
        """Load operation definitions from config"""
        config_path = Path("/config/operations.yml")
        with open(config_path) as f:
            return yaml.safe_load(f)
    
    def get_available_operations(self, environment: str) -> List[str]:
        """Get operations available in specific environment"""
        env_config = self.config_loader.get_environment_capabilities(environment)
        return [op for op in self.operations.keys() if op in env_config]
    
    def get_operation_schema(self, operation_name: str) -> Dict[str, Any]:
        """Get parameter schema for operation"""
        return self.operations[operation_name]
```

### **2.2 Universal Interface**
```python
class UniversalInfrastructureInterface:
    """Environment-agnostic infrastructure operations"""
    
    def __init__(self):
        self.config = UniversalConfigLoader()
        self.environment = self.config.get_current_environment()
        self.executor = self._get_executor_for_environment()
        self.registry = OperationRegistry()
    
    async def execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute any infrastructure operation"""
        
        # Validate operation exists
        if operation["name"] not in self.registry.get_available_operations(self.environment):
            raise ValueError(f"Operation {operation['name']} not available in {self.environment}")
        
        # Route to environment-specific executor
        return await self.executor.execute(operation)
    
    def get_ai_context(self) -> Dict[str, Any]:
        """Provide full context to AI for intelligent decision making"""
        return {
            "environment": self.environment,
            "available_operations": self.registry.get_available_operations(self.environment),
            "operation_schemas": {op: self.registry.get_operation_schema(op) 
                                for op in self.registry.get_available_operations(self.environment)},
            "platform_info": self.config.platform_config,
            "resource_limits": self.config.get_resource_limits(),
            "network_topology": self.config.get_network_info()
        }
```

---

## **Phase 3: Environment Executors** (Week 3)
**Goal**: Implement environment-specific command execution

### **3.1 Executor Factory**
```python
class ExecutorFactory:
    """Create appropriate executor based on environment"""
    
    @staticmethod
    def create_executor(environment: str, config: UniversalConfigLoader):
        """Factory method to create environment-specific executor"""
        
        if environment == "local_docker":
            return DockerExecutor(config)
        elif environment == "oracle_cloud":
            return OCIExecutor(config)
        elif environment == "kubernetes":
            return KubernetesExecutor(config)
        else:
            raise ValueError(f"Unsupported environment: {environment}")

class DockerExecutor:
    """Execute operations in Docker environment"""
    
    async def execute(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        op_name = operation["name"]
        params = operation["parameters"]
        
        if op_name == "restart_service":
            return await self._restart_docker_service(params)
        elif op_name == "get_logs":
            return await self._get_docker_logs(params)
        elif op_name == "execute_command":
            return await self._execute_docker_command(params)
        # ... dynamic operation handling

class OCIExecutor:
    """Execute operations in Oracle Cloud"""
    
    async def execute(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        # Translate operations to OCI API calls
        pass
```

### **3.2 Command Translation Engine**
```python
class CommandTranslator:
    """Translate universal operations to environment-specific commands"""
    
    def __init__(self, environment: str, config: UniversalConfigLoader):
        self.environment = environment
        self.config = config
        self.translation_rules = self._load_translation_rules()
    
    def translate_operation(self, operation: Dict[str, Any]) -> str:
        """Convert universal operation to environment command"""
        
        rule = self.translation_rules[self.environment][operation["name"]]
        return rule.format(**operation["parameters"])
    
    def _load_translation_rules(self) -> Dict[str, Any]:
        """Load command translation rules from config"""
        config_path = Path("/config/command_translations.yml")
        with open(config_path) as f:
            return yaml.safe_load(f)
```

---

## **Phase 4: AI Intelligence Engine** (Week 4)
**Goal**: Implement sophisticated AI reasoning for infrastructure problems

### **4.1 Enhanced AI Context**
```python
async def generate_ai_context(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive context for AI reasoning"""
    
    return {
        # Incident Context
        "incident": {
            "alert_name": alert_data.get("alertname"),
            "service": alert_data.get("service"),
            "severity": alert_data.get("severity"),
            "duration": alert_data.get("duration"),
            "symptoms": self._extract_symptoms(alert_data),
            "recent_changes": await self._get_recent_changes()
        },
        
        # Environment Context - FROM CONFIG, NOT HARDCODED!
        "environment": {
            "platform": self.config.get_current_environment(),
            "type": self.config.get_environment_type(),
            "capabilities": self.config.get_environment_capabilities(),
            "resource_limits": self.config.get_resource_limits(),
            "network_setup": self.config.get_network_config(),
            "monitoring_setup": self.config.get_monitoring_config()
        },
        
        # Available Operations - DYNAMIC!
        "available_operations": self.interface.registry.get_available_operations(
            self.config.get_current_environment()
        ),
        
        # Operation Schemas - COMPREHENSIVE!
        "operation_schemas": self._get_detailed_operation_schemas(),
        
        # Historical Context
        "similar_incidents": await self._find_similar_incidents(alert_data),
        "success_patterns": await self._get_success_patterns(),
        
        # Service Context
        "service_architecture": self.config.get_service_architecture(),
        "dependencies": self.config.get_service_dependencies(),
        "health_endpoints": self.config.get_health_endpoints()
    }
```

### **4.2 Intelligent Diagnostic Planner**
```python
class AIdiagnosticPlanner:
    """Advanced AI reasoning for infrastructure problems"""
    
    def __init__(self, config: UniversalConfigLoader):
        self.config = config
        self.llm_config = config.get_llm_config()  # NO HARDCODING!
        self.llm_client = self._create_llm_client()
    
    async def create_diagnostic_plan(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligent diagnostic plan"""
        
        prompt = self._build_comprehensive_prompt(context)
        
        llm_response = await self.llm_client.chat.completions.create(
            model=self.llm_config["model"],  # FROM CONFIG!
            temperature=self.llm_config["temperature"],  # FROM CONFIG!
            max_tokens=self.llm_config["max_tokens"],  # FROM CONFIG!
            messages=[{"role": "system", "content": prompt}]
        )
        
        return self._parse_diagnostic_plan(llm_response.choices[0].message.content)
    
    def _build_comprehensive_prompt(self, context: Dict[str, Any]) -> str:
        """Build detailed prompt with full context"""
        
        return f"""
        You are a Senior Site Reliability Engineer with deep expertise in {context['environment']['platform']} infrastructure.
        
        ## INCIDENT ANALYSIS
        Service: {context['incident']['service']}
        Alert: {context['incident']['alert_name']}
        Severity: {context['incident']['severity']}
        Duration: {context['incident']['duration']}
        Symptoms: {context['incident']['symptoms']}
        
        ## ENVIRONMENT CONTEXT
        Platform: {context['environment']['platform']}
        Type: {context['environment']['type']}
        Capabilities: {context['environment']['capabilities']}
        Resource Limits: {context['environment']['resource_limits']}
        
        ## AVAILABLE OPERATIONS
        {self._format_operations_for_ai(context['available_operations'], context['operation_schemas'])}
        
        ## DIAGNOSTIC STRATEGY
        Create a systematic plan following these phases:
        
        1. **IMMEDIATE TRIAGE** (0-2 minutes)
           - Quick health and resource checks
           - Rule out obvious issues
           
        2. **PROBLEM ISOLATION** (2-5 minutes)
           - Targeted log analysis
           - Resource pattern investigation
           - Network and dependency checks
           
        3. **ROOT CAUSE ANALYSIS** (5-10 minutes)
           - Deep diagnostic investigation
           - Historical comparison
           - Performance profiling
           
        4. **RESOLUTION & VALIDATION** (10+ minutes)
           - Apply targeted fixes
           - Verify resolution
           - Monitor for regression
        
        ## DECISION FRAMEWORK
        **When to use get_logs:**
        - Service errors: filter by level="error", since="15m"
        - Performance issues: filter="slow|timeout", lines=200
        - Post-deployment: since="1h", timestamps=true
        
        **When to use check_resources:**
        - High latency: metrics=["cpu","memory","io"], duration="5m"
        - Service crashes: metrics=["memory"], historical=true
        - Before restart: metrics=["all"], format="detailed"
        
        **When to use execute_command:**
        - Network issues: "netstat -tlnp", "ss -tuln"
        - Database problems: "mysql -e 'SHOW PROCESSLIST'"
        - Custom diagnostics: environment-specific tools
        
        **When to use restart_service:**
        - Memory leaks detected: strategy="graceful", backup=true
        - Config changes: strategy="rolling", health_check=true
        - Critical failures: strategy="force", notify=true
        
        ## OUTPUT FORMAT
        Return JSON array of operations with detailed reasoning:
        [
          {{
            "phase": "immediate_triage",
            "operation": "check_resources",
            "parameters": {{
              "target": "{context['incident']['service']}",
              "metrics": ["cpu", "memory"],
              "format": "summary",
              "threshold_alerts": true
            }},
            "reasoning": "Quick resource check to identify obvious bottlenecks",
            "expected_duration": "15s",
            "success_criteria": "CPU < 80%, Memory < 90%",
            "next_actions": ["If high resource usage → detailed analysis", "If normal → check logs"]
          }}
        ]
        
        Generate 4-8 operations covering all diagnostic phases.
        Adapt strategy to {context['environment']['platform']} environment specifics.
        Consider {context['incident']['severity']} severity for operation priority.
        """
```

---

## **Phase 5: Operation Configuration** (Week 5)
**Goal**: Externalize all operation definitions to config files

### **5.1 Operations Configuration**
```yaml
# infrastructure/config/operations.yml
operations:
  get_logs:
    description: "Retrieve and analyze service logs"
    parameters:
      target:
        type: "string"
        required: true
        description: "Service name or container identifier"
      lines:
        type: "integer" 
        default: 100
        range: [1, 10000]
        description: "Number of log lines to retrieve"
      since:
        type: "string"
        default: null
        examples: ["1h", "30m", "2d", "2023-01-01T00:00:00Z"]
        description: "Time period or timestamp for log start"
      level:
        type: "string"
        default: "all"
        options: ["error", "warn", "info", "debug", "all"]
        description: "Log level filter"
      filter:
        type: "string"
        default: null
        description: "Regex pattern to filter log content"
      follow:
        type: "boolean"
        default: false
        description: "Stream logs in real-time"
      timestamps:
        type: "boolean"
        default: true
        description: "Include timestamps in output"
      source:
        type: "string"
        default: "all"
        options: ["stdout", "stderr", "all"]
        description: "Log source streams"
    
    # Environment-specific implementations
    environments:
      local_docker:
        command_template: "docker logs {target} --tail {lines} {since_flag} {follow_flag}"
        supports: ["lines", "since", "follow", "timestamps"]
      
      oracle_cloud:
        api_method: "oci.logging.search_logs"
        supports: ["lines", "since", "filter", "level"]
        
      kubernetes:
        command_template: "kubectl logs {deployment_type}/{target} --tail={lines} {since_flag}"
        supports: ["lines", "since", "follow"]

  check_resources:
    description: "Monitor system and service resource usage"
    parameters:
      target:
        type: "string"
        required: true
        description: "Service name or 'system' for host resources"
      metrics:
        type: "array"
        default: ["cpu", "memory", "disk", "network"]
        options: ["cpu", "memory", "disk", "network", "io", "connections", "threads"]
        description: "Resource metrics to collect"
      duration:
        type: "string"
        default: "current" 
        examples: ["current", "5m", "1h", "1d"]
        description: "Time range for metrics"
      format:
        type: "string"
        default: "summary"
        options: ["summary", "detailed", "json", "prometheus"]
        description: "Output format"
      threshold_alerts:
        type: "boolean"
        default: true
        description: "Generate alerts for high usage"
      historical:
        type: "boolean"
        default: false
        description: "Include historical trend data"
      per_process:
        type: "boolean"
        default: false
        description: "Break down metrics by process"
    
    environments:
      local_docker:
        commands:
          summary: "docker stats --no-stream {target}"
          detailed: "docker exec {target} ps aux && docker exec {target} free -h"
      
      oracle_cloud:
        api_method: "oci.monitoring.get_metrics"
        metric_namespace: "oci_containerinstances"
        
      kubernetes:
        commands:
          summary: "kubectl top pods {target}"
          detailed: "kubectl describe pod {target}"

  restart_service:
    description: "Restart a service with configurable strategy"
    parameters:
      target:
        type: "string"
        required: true
        description: "Service name to restart"
      strategy:
        type: "string"
        default: "graceful"
        options: ["graceful", "force", "rolling", "blue-green"]
        description: "Restart strategy"
      timeout:
        type: "integer"
        default: 30
        range: [5, 300]
        description: "Maximum wait time for restart (seconds)"
      backup:
        type: "boolean"
        default: true
        description: "Backup current state before restart"
      health_check:
        type: "boolean"
        default: true
        description: "Verify health after restart"
      wait_for_ready:
        type: "boolean"
        default: true
        description: "Wait until service is fully ready"
      rollback_on_failure:
        type: "boolean"
        default: true
        description: "Automatically rollback if restart fails"
      notify:
        type: "boolean"
        default: true
        description: "Send notifications about restart"
    
    environments:
      local_docker:
        graceful: "docker restart {target}"
        force: "docker kill {target} && docker start {target}"
        
      oracle_cloud:
        graceful: "oci container-instances restart --instance-id {instance_id}"
        force: "oci container-instances stop --instance-id {instance_id} && oci container-instances start --instance-id {instance_id}"
        
      kubernetes:
        graceful: "kubectl rollout restart deployment/{target}"
        rolling: "kubectl rollout restart deployment/{target} --timeout={timeout}s"

  execute_command:
    description: "Execute custom commands for advanced diagnostics"
    parameters:
      target:
        type: "string"
        required: true
        description: "Service, container, or host to execute on"
      command:
        type: "string"
        required: true
        description: "Command to execute"
      timeout:
        type: "integer"
        default: 30
        range: [1, 300]
        description: "Command timeout (seconds)"
      working_dir:
        type: "string"
        default: "/"
        description: "Working directory for command"
      user:
        type: "string"
        default: "root"
        description: "User to run command as"
      environment:
        type: "object"
        default: {}
        description: "Environment variables for command"
      capture_output:
        type: "boolean"
        default: true
        description: "Capture and return command output"
      background:
        type: "boolean"
        default: false
        description: "Run command in background"
    
    environments:
      local_docker:
        command_template: "docker exec {user_flag} {env_flags} {target} {command}"
        
      oracle_cloud:
        api_method: "oci.compute.run_command"
        
      kubernetes:
        command_template: "kubectl exec {target} -- {command}"
```

### **5.2 Environment-Specific Translations**
```yaml
# infrastructure/config/command_translations.yml
translations:
  local_docker:
    get_logs:
      template: "docker logs {target}"
      parameter_mappings:
        lines: "--tail {lines}"
        since: "--since {since}"
        follow: "--follow"
        timestamps: "--timestamps"
    
    check_resources:
      summary: "docker stats --no-stream {target}"
      detailed: "docker exec {target} top -bn1 && docker exec {target} free -h"
      
    restart_service:
      graceful: "docker restart {target}"
      force: "docker kill {target} && docker start {target}"

  oracle_cloud:
    get_logs:
      api_call: "oci.logging.search_logs"
      parameters:
        log_group_id: "{target}_log_group"
        time_start: "{since}"
        limit: "{lines}"
        
    check_resources:
      api_call: "oci.monitoring.list_metrics"
      namespace: "oci_containerinstances"
      resource_group: "{target}"
      
    restart_service:
      api_call: "oci.container_instances.restart_container_instance"
      instance_id: "{target}_instance_id"

  kubernetes:
    get_logs:
      template: "kubectl logs deployment/{target}"
      parameter_mappings:
        lines: "--tail={lines}"
        since: "--since={since}"
        follow: "--follow"
        
    check_resources:
      summary: "kubectl top pods -l app={target}"
      detailed: "kubectl describe pod -l app={target}"
      
    restart_service:
      graceful: "kubectl rollout restart deployment/{target}"
      rolling: "kubectl rollout restart deployment/{target} --timeout={timeout}s"
```

---

## **Phase 6: Testing & Validation** (Week 6)
**Goal**: Comprehensive testing across all environments

### **6.1 Test Framework**
```python
class UICITestFramework:
    """Comprehensive testing for Universal Infrastructure Interface"""
    
    async def test_operation_execution(self, environment: str, operation: Dict[str, Any]):
        """Test operation execution in specific environment"""
        
        interface = UniversalInfrastructureInterface()
        
        # Test operation validation
        assert operation["name"] in interface.registry.get_available_operations(environment)
        
        # Test parameter validation
        schema = interface.registry.get_operation_schema(operation["name"])
        self._validate_parameters(operation["parameters"], schema)
        
        # Test execution
        result = await interface.execute_operation(operation)
        
        # Test result format
        assert "success" in result
        assert "output" in result
        assert "duration" in result
        
        return result
    
    async def test_ai_reasoning(self, alert_scenario: Dict[str, Any]):
        """Test AI diagnostic reasoning"""
        
        planner = AIdiagnosticPlanner(UniversalConfigLoader())
        context = await self._generate_test_context(alert_scenario)
        
        diagnostic_plan = await planner.create_diagnostic_plan(context)
        
        # Validate diagnostic plan structure
        assert len(diagnostic_plan) >= 3  # At least triage, analysis, resolution
        assert all("phase" in op for op in diagnostic_plan)
        assert all("reasoning" in op for op in diagnostic_plan)
        
        return diagnostic_plan
```

### **6.2 Environment Migration Tests**
```python
async def test_environment_migration():
    """Test same operations work across environments"""
    
    operation = {
        "name": "get_logs",
        "parameters": {
            "target": "market-predictor",
            "lines": 100,
            "level": "error"
        }
    }
    
    environments = ["local_docker", "oracle_cloud", "kubernetes"]
    
    for env in environments:
        # Test operation translates correctly
        interface = UniversalInfrastructureInterface()
        interface.environment = env
        
        result = await interface.execute_operation(operation)
        assert result["success"] is True
        
        # Verify environment-specific implementation
        assert env in result["execution_details"]["environment"]
```

---

## 📚 Configuration Reference

### **Critical Rules for AI Agents**

#### **🚫 NEVER HARDCODE - ALWAYS USE CONFIG**
```python
# ❌ NEVER DO THIS
model = "gpt-4"
temperature = 0.1
timeout = 60

# ✅ ALWAYS DO THIS  
config = UniversalConfigLoader()
llm_config = config.get_llm_config()
model = llm_config["model"]
temperature = llm_config["temperature"] 
timeout = llm_config["timeout"]
```

#### **📁 Configuration File Locations**
- **`infrastructure/config/platform.yml`** - Platform-wide settings, LLM config, credentials
- **`infrastructure/config/agents.yml`** - Agent-specific configurations
- **`infrastructure/config/environments.yml`** - Environment definitions and capabilities
- **`infrastructure/config/operations.yml`** - Operation schemas and parameters
- **`infrastructure/config/command_translations.yml`** - Environment-specific command mappings

#### **🔧 Configuration Access Pattern**
```python
class AIAgent:
    def __init__(self):
        # Load ALL config from infrastructure/config/
        self.config = UniversalConfigLoader()
        
        # Get environment-specific context
        self.environment = self.config.get_current_environment()
        self.capabilities = self.config.get_environment_capabilities(self.environment)
        
        # Get LLM config (NO HARDCODING!)
        self.llm_config = self.config.get_llm_config()
        
        # Initialize interface
        self.interface = UniversalInfrastructureInterface()
```

---

## 🚀 Usage Examples

### **Example 1: AI Diagnostic Reasoning**
```python
# AI receives alert
alert = {
    "alertname": "MarketPredictorDown",
    "service": "market-predictor",
    "severity": "critical"
}

# AI generates diagnostic plan
planner = AIdiagnosticPlanner(config)
context = await generate_ai_context(alert)

diagnostic_plan = await planner.create_diagnostic_plan(context)

# Sample AI-generated operations
[
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
      "since": "10m"
    },
    "reasoning": "Check for recent error patterns"
  },
  {
    "phase": "resolution",
    "operation": "restart_service",
    "parameters": {
      "target": "market-predictor",
      "strategy": "graceful",
      "health_check": true
    },
    "reasoning": "Restart service based on diagnostic findings"
  }
]
```

### **Example 2: Environment-Agnostic Execution**
```python
# Same operation works in any environment
operation = {
    "name": "get_logs",
    "parameters": {
        "target": "market-predictor",
        "lines": 100,
        "since": "1h",
        "filter": "ERROR|FATAL"
    }
}

# Local Docker: docker logs market-predictor --tail 100 --since 1h | grep "ERROR|FATAL"
# Oracle Cloud: oci logging search-logs --log-group market-predictor --limit 100 --time-start 1h --query "ERROR|FATAL"  
# Kubernetes: kubectl logs deployment/market-predictor --tail=100 --since=1h | grep "ERROR|FATAL"

result = await interface.execute_operation(operation)
```

---

## 🎯 Success Criteria

### **Phase Completion Checklist**

#### **Phase 1: Configuration Centralization** ✅
- [ ] All configurations moved to `infrastructure/config/`
- [ ] No hardcoded values in any code
- [ ] Configuration loader implemented
- [ ] Agents read from config files

#### **Phase 2: Universal Interface** ✅  
- [ ] Operation registry implemented
- [ ] Dynamic operation discovery
- [ ] Environment-agnostic operation execution
- [ ] Parameter validation system

#### **Phase 3: Environment Executors** ✅
- [ ] Docker executor implemented
- [ ] Oracle Cloud executor implemented  
- [ ] Kubernetes executor implemented
- [ ] Command translation engine

#### **Phase 4: AI Intelligence** ✅
- [ ] Comprehensive AI context generation
- [ ] Intelligent diagnostic planning
- [ ] Multi-phase reasoning strategy
- [ ] Decision framework implementation

#### **Phase 5: Configuration Externalization** ✅
- [ ] All operations defined in config
- [ ] Environment-specific translations
- [ ] Parameter schemas externalized
- [ ] No hardcoded operation logic

#### **Phase 6: Testing & Validation** ✅
- [ ] Comprehensive test suite
- [ ] Environment migration tests
- [ ] AI reasoning validation
- [ ] End-to-end integration tests

---

## 🔮 Future Enhancements

### **Advanced AI Capabilities**
- **Learning Engine**: AI learns from successful problem resolutions
- **Pattern Recognition**: Identify recurring issues and preventive measures
- **Predictive Analysis**: Anticipate problems before they occur
- **Multi-Service Orchestration**: Coordinate operations across service dependencies

### **Additional Environments**
- **AWS ECS/Fargate**: Amazon container services
- **Google Cloud Run**: Google serverless containers  
- **Azure Container Instances**: Microsoft container platform
- **HashiCorp Nomad**: Multi-cloud orchestration
- **Docker Swarm**: Docker native clustering

### **Enhanced Operations**
- **Performance Profiling**: Deep application performance analysis
- **Security Scanning**: Vulnerability detection and remediation
- **Cost Optimization**: Resource usage optimization recommendations
- **Compliance Checking**: Automated compliance validation

---

## ⚠️ Critical Implementation Notes

### **For AI Agents Implementing This System**

1. **NEVER HARDCODE ANYTHING**
   - All values must come from `infrastructure/config/` files
   - Use `UniversalConfigLoader` for all configuration access
   - No default values in code - everything from config

2. **Always Check Configuration First**
   - Validate config files exist and are readable
   - Fail fast if required configurations are missing
   - Log configuration loading for debugging

3. **Environment Detection**
   - Auto-detect current environment from config
   - Adapt operations to environment capabilities
   - Graceful fallback for unsupported operations

4. **Error Handling**
   - Comprehensive error handling for all operations
   - Clear error messages with context
   - Rollback capabilities for failed operations

5. **Security Considerations**
   - Validate all parameters before execution
   - Implement command injection protection
   - Audit log all executed operations

---

**This Universal Infrastructure Command Interface represents a paradigm shift from hardcoded, environment-specific operations to intelligent, adaptive infrastructure management that works seamlessly across any platform.** 