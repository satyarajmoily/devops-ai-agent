"""
Multi-Phase Diagnostic Planner
Implements sophisticated AI reasoning for infrastructure problem diagnosis
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ...config.simple_config import get_config

logger = logging.getLogger(__name__)

class DiagnosticPhase(Enum):
    """Diagnostic phases for systematic problem resolution"""
    TRIAGE = "triage"
    ISOLATION = "isolation"
    ANALYSIS = "analysis"
    RESOLUTION = "resolution"
    VALIDATION = "validation"

@dataclass
class DiagnosticStep:
    """Individual step in diagnostic workflow"""
    phase: DiagnosticPhase
    operation: str
    parameters: Dict[str, Any]
    reasoning: str
    expected_duration: str
    success_criteria: str
    next_actions: List[str]
    priority: int = 1
    depends_on: List[str] = None
    timeout: int = 60

@dataclass
class DiagnosticPlan:
    """Complete diagnostic plan with phases and steps"""
    incident_id: str
    service: str
    alert_name: str
    severity: str
    phases: Dict[DiagnosticPhase, List[DiagnosticStep]]
    estimated_duration: str
    created_at: datetime
    context: Dict[str, Any]
    problem_type: str = "service_down"
    environment: str = "docker"
    success_criteria: List[str] = None
    escalation_triggers: List[str] = None
    
    def __post_init__(self):
        """Initialize default values after creation"""
        if self.success_criteria is None:
            self.success_criteria = ["Service responding to health checks", "No error logs in last 5 minutes"]
        if self.escalation_triggers is None:
            self.escalation_triggers = ["Multiple restart attempts failed", "Resource exhaustion detected", "Critical error patterns found"]

class DiagnosticPlanner:
    """
    Advanced AI-powered diagnostic planner
    Creates intelligent multi-phase diagnostic plans for infrastructure incidents
    """
    
    def __init__(self, config):
        """Initialize diagnostic planner with configuration"""
        self.config = config
        self.llm_config = config.get_llm_config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM client
        self._initialize_llm_client()
        
        # Load diagnostic patterns and templates
        self.diagnostic_patterns = self._load_diagnostic_patterns()
        self.operation_templates = self._load_operation_templates()
        
        self.logger.info("Diagnostic Planner initialized with multi-phase reasoning")
    
    def _initialize_llm_client(self):
        """Initialize LLM client from configuration"""
        try:
            import openai
            self.llm_client = openai.AsyncOpenAI(
                api_key=self.llm_config["api_key"]
            )
        except ImportError:
            raise RuntimeError("OpenAI package not available. Install with: pip install openai")
        except KeyError as e:
            raise RuntimeError(f"Missing LLM configuration: {e}")
    
    def _load_diagnostic_patterns(self) -> Dict[str, Any]:
        """Load diagnostic patterns for different incident types"""
        return {
            "service_down": {
                "phases": [DiagnosticPhase.TRIAGE, DiagnosticPhase.ISOLATION, DiagnosticPhase.RESOLUTION],
                "primary_operations": ["check_resources", "get_logs", "health_check", "restart_service"],
                "escalation_criteria": ["high_cpu", "out_of_memory", "disk_full", "network_issue"]
            },
            "high_latency": {
                "phases": [DiagnosticPhase.TRIAGE, DiagnosticPhase.ANALYSIS, DiagnosticPhase.RESOLUTION],
                "primary_operations": ["check_resources", "get_logs", "execute_command"],
                "escalation_criteria": ["cpu_bottleneck", "memory_pressure", "io_wait", "network_congestion"]
            },
            "resource_exhaustion": {
                "phases": [DiagnosticPhase.TRIAGE, DiagnosticPhase.ISOLATION, DiagnosticPhase.RESOLUTION],
                "primary_operations": ["check_resources", "get_logs", "scale_service"],
                "escalation_criteria": ["memory_leak", "cpu_spike", "disk_usage", "connection_limit"]
            },
            "deployment_failure": {
                "phases": [DiagnosticPhase.TRIAGE, DiagnosticPhase.ANALYSIS, DiagnosticPhase.RESOLUTION],
                "primary_operations": ["get_logs", "health_check", "execute_command", "restart_service"],
                "escalation_criteria": ["config_error", "dependency_failure", "permission_issue", "image_pull_error"]
            }
        }
    
    def _load_operation_templates(self) -> Dict[str, Any]:
        """Load operation templates for different scenarios"""
        return {
            "triage_resource_check": {
                "operation": "check_resources",
                "parameters": {
                    "target": "{service}",
                    "metrics": ["cpu", "memory", "disk"],
                    "format": "summary",
                    "threshold_alerts": True
                },
                "reasoning": "Quick resource assessment to identify obvious bottlenecks",
                "success_criteria": "CPU < 80%, Memory < 90%, Disk < 85%"
            },
            "error_log_analysis": {
                "operation": "get_logs",
                "parameters": {
                    "target": "{service}",
                    "lines": 100,
                    "level": "error",
                    "since": "15m",
                    "timestamps": True
                },
                "reasoning": "Analyze recent error logs for incident patterns",
                "success_criteria": "Error patterns identified or no critical errors found"
            },
            "performance_deep_dive": {
                "operation": "check_resources",
                "parameters": {
                    "target": "{service}",
                    "metrics": ["cpu", "memory", "io", "network"],
                    "format": "detailed",
                    "historical": True,
                    "duration": "1h"
                },
                "reasoning": "Detailed performance analysis with historical context",
                "success_criteria": "Performance bottlenecks identified or baseline confirmed"
            },
            "health_validation": {
                "operation": "health_check",
                "parameters": {
                    "target": "{service}",
                    "endpoints": ["/health", "/ready", "/metrics"],
                    "timeout": 10,
                    "retries": 3
                },
                "reasoning": "Comprehensive service health validation",
                "success_criteria": "All health endpoints responding normally"
            }
        }
    
    async def create_diagnostic_plan(self, incident_context: Dict[str, Any]) -> DiagnosticPlan:
        """
        Create comprehensive diagnostic plan using AI reasoning
        
        Args:
            incident_context: Context about the incident including alert data, service info, environment
        
        Returns:
            Complete diagnostic plan with multi-phase approach
        """
        self.logger.info(f"Creating diagnostic plan for incident: {incident_context.get('incident', {}).get('alert_name', 'unknown')}")
        
        # Extract incident information
        incident = incident_context.get("incident", {})
        service = incident.get("service", "unknown")
        alert_name = incident.get("alert_name", "unknown")
        severity = incident.get("severity", "medium")
        
        # Generate incident ID
        incident_id = f"{service}_{alert_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Classify incident type
        incident_type = self._classify_incident(incident_context)
        
        # Generate AI-powered diagnostic steps
        diagnostic_steps = await self._generate_ai_diagnostic_steps(incident_context, incident_type)
        
        # Organize steps by phases
        phases = self._organize_steps_by_phases(diagnostic_steps)
        
        # Estimate total duration
        estimated_duration = self._calculate_estimated_duration(phases)
        
        # Create diagnostic plan
        plan = DiagnosticPlan(
            incident_id=incident_id,
            service=service,
            alert_name=alert_name,
            severity=severity,
            phases=phases,
            estimated_duration=estimated_duration,
            created_at=datetime.now(),
            context=incident_context,
            problem_type=incident_type,
            environment=incident_context.get("environment", {}).get("current", "docker")
        )
        
        self.logger.info(f"Created diagnostic plan with {len(diagnostic_steps)} steps across {len(phases)} phases")
        return plan
    
    def _classify_incident(self, context: Dict[str, Any]) -> str:
        """Classify incident type based on context"""
        incident = context.get("incident", {})
        alert_name = incident.get("alert_name", "").lower()
        symptoms = incident.get("symptoms", [])
        
        # Simple classification logic - could be enhanced with ML
        if any(keyword in alert_name for keyword in ["down", "unavailable", "failed"]):
            return "service_down"
        elif any(keyword in alert_name for keyword in ["slow", "latency", "timeout"]):
            return "high_latency"
        elif any(keyword in alert_name for keyword in ["memory", "cpu", "disk", "resource"]):
            return "resource_exhaustion"
        elif any(keyword in alert_name for keyword in ["deploy", "startup", "config"]):
            return "deployment_failure"
        else:
            return "service_down"  # Default fallback
    
    async def _generate_ai_diagnostic_steps(self, context: Dict[str, Any], incident_type: str) -> List[DiagnosticStep]:
        """Generate diagnostic steps using AI reasoning"""
        
        # Build comprehensive prompt for AI
        prompt = self._build_diagnostic_prompt(context, incident_type)
        
        try:
            # Get AI response
            response = await self.llm_client.chat.completions.create(
                model=self.llm_config["model"],
                temperature=self.llm_config.get("temperature", 0.1),
                max_tokens=self.llm_config.get("max_tokens", 4000),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Senior Site Reliability Engineer with expertise in infrastructure diagnostics. You create systematic diagnostic plans using available operations."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            # Parse AI response into diagnostic steps
            ai_content = response.choices[0].message.content
            steps = self._parse_ai_diagnostic_response(ai_content, context)
            
            return steps
            
        except Exception as e:
            self.logger.error(f"AI diagnostic generation failed: {e}")
            # Fallback to template-based approach
            return self._generate_template_diagnostic_steps(context, incident_type)
    
    def _build_diagnostic_prompt(self, context: Dict[str, Any], incident_type: str) -> str:
        """Build comprehensive prompt for AI diagnostic planning"""
        
        incident = context.get("incident", {})
        environment = context.get("environment", {})
        operations = context.get("detailed_operations", {}).get("operations", {})
        
        # Get relevant patterns for this incident type
        patterns = self.diagnostic_patterns.get(incident_type, self.diagnostic_patterns["service_down"])
        
        prompt = f"""
INFRASTRUCTURE DIAGNOSTIC PLANNING

## INCIDENT ANALYSIS
Service: {incident.get('service', 'unknown')}
Alert: {incident.get('alert_name', 'unknown')}
Severity: {incident.get('severity', 'medium')}
Duration: {incident.get('duration', 'unknown')}
Incident Type: {incident_type}
Symptoms: {incident.get('symptoms', [])}

## ENVIRONMENT CONTEXT
Platform: {environment.get('current', 'unknown')}
Type: {environment.get('type', 'unknown')}
Capabilities: {environment.get('capabilities', [])}

## AVAILABLE OPERATIONS
{self._format_operations_for_prompt(operations)}

## DIAGNOSTIC STRATEGY
Create a systematic diagnostic plan following these phases:

1. **TRIAGE** (0-2 minutes): Quick assessment and immediate safety checks
2. **ISOLATION** (2-5 minutes): Narrow down problem scope and eliminate obvious causes  
3. **ANALYSIS** (5-15 minutes): Deep investigation and root cause analysis
4. **RESOLUTION** (10+ minutes): Apply targeted fixes and validate
5. **VALIDATION** (Post-fix): Verify resolution and monitor for regression

## DECISION FRAMEWORK
**When to use get_logs:**
- Service errors: level="error", since="15m", lines=100
- Performance issues: filter="slow|timeout|error", lines=200
- Post-incident: since="1h", timestamps=true

**When to use check_resources:**
- High utilization alerts: metrics=["cpu","memory","disk"], format="detailed"
- Performance issues: metrics=["cpu","memory","io"], historical=true
- Before scaling: metrics=["all"], threshold_alerts=true

**When to use health_check:**
- Service availability: endpoints=["/health"], retries=3
- Post-restart: endpoints=["/health", "/ready"], timeout=30
- Load balancer checks: endpoints=["/metrics"], retries=1

**When to use restart_service:**
- Memory leaks: strategy="graceful", backup=true, health_check=true
- Config changes: strategy="rolling", wait_for_ready=true
- Critical failures: strategy="force", rollback_on_failure=true

## INCIDENT-SPECIFIC GUIDANCE
Based on incident type '{incident_type}':
- Recommended phases: {[phase.value for phase in patterns['phases']]}
- Primary operations: {patterns['primary_operations']}
- Escalation criteria: {patterns['escalation_criteria']}

## OUTPUT FORMAT
Return a JSON array of diagnostic steps with this exact structure:
[
  {{
    "phase": "triage|isolation|analysis|resolution|validation",
    "operation": "operation_name",
    "parameters": {{
      "target": "{incident.get('service')}",
      "...": "other_parameters_as_needed"
    }},
    "reasoning": "Why this step is needed and what it will reveal",
    "expected_duration": "30s|2m|5m",
    "success_criteria": "What indicates this step succeeded",
    "next_actions": ["What to do based on results"],
    "priority": 1,
    "timeout": 60
  }}
]

CRITICAL: Always set "target" parameter to the service name "{incident.get('service')}" for ALL operations that require a target.

Generate 6-10 diagnostic steps covering multiple phases.
Prioritize based on {incident.get('severity', 'medium')} severity.
Consider {environment.get('type', 'unknown')} environment constraints.
"""
        
        return prompt
    
    def _format_operations_for_prompt(self, operations: Dict[str, Any]) -> str:
        """Format available operations for AI prompt"""
        if not operations:
            return "No operations available"
        
        formatted = []
        for op_name, op_config in operations.items():
            params = op_config.get("parameters", {})
            param_names = list(params.keys()) if params else []
            description = op_config.get("description", "No description")
            
            formatted.append(f"- **{op_name}**: {description}")
            if param_names:
                formatted.append(f"  Parameters: {', '.join(param_names[:5])}")  # Limit for readability
        
        return "\n".join(formatted)
    
    def _parse_ai_diagnostic_response(self, ai_content: str, context: Dict[str, Any]) -> List[DiagnosticStep]:
        """Parse AI response into diagnostic steps"""
        try:
            # Try to extract JSON from AI response
            json_start = ai_content.find('[')
            json_end = ai_content.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in AI response")
            
            json_content = ai_content[json_start:json_end]
            steps_data = json.loads(json_content)
            
            # Convert to DiagnosticStep objects and validate parameters
            steps = []
            service_name = context.get("incident", {}).get("service", "unknown")
            
            for step_data in steps_data:
                parameters = step_data.get("parameters", {})
                
                # Ensure target parameter is set correctly for operations that need it
                operation = step_data.get("operation", "check_resources")
                if operation in ["health_check", "get_logs", "restart_service", "check_resources", "scale_service"]:
                    if "target" not in parameters or not parameters["target"] or parameters["target"] == "unknown":
                        parameters["target"] = service_name
                        self.logger.warning(f"Fixed missing target parameter for {operation}, set to {service_name}")
                
                step = DiagnosticStep(
                    phase=DiagnosticPhase(step_data.get("phase", "triage")),
                    operation=operation,
                    parameters=parameters,
                    reasoning=step_data.get("reasoning", "AI-generated diagnostic step"),
                    expected_duration=step_data.get("expected_duration", "60s"),
                    success_criteria=step_data.get("success_criteria", "Operation completes successfully"),
                    next_actions=step_data.get("next_actions", []),
                    priority=step_data.get("priority", 1),
                    timeout=step_data.get("timeout", 60)
                )
                steps.append(step)
            
            return steps
            
        except Exception as e:
            self.logger.error(f"Failed to parse AI diagnostic response: {e}")
            self.logger.debug(f"AI response content: {ai_content}")
            # Return empty list, fallback will be used
            return []
    
    def _generate_template_diagnostic_steps(self, context: Dict[str, Any], incident_type: str) -> List[DiagnosticStep]:
        """Generate diagnostic steps using predefined templates (fallback)"""
        incident = context.get("incident", {})
        service = incident.get("service", "unknown")
        
        # Basic template-based steps
        steps = [
            DiagnosticStep(
                phase=DiagnosticPhase.TRIAGE,
                operation="check_resources",
                parameters={
                    "target": service,
                    "metrics": ["cpu", "memory"],
                    "format": "summary"
                },
                reasoning="Quick resource check to identify obvious bottlenecks",
                expected_duration="30s",
                success_criteria="Resource utilization within normal limits",
                next_actions=["If high usage → detailed analysis", "If normal → check logs"]
            ),
            DiagnosticStep(
                phase=DiagnosticPhase.ISOLATION,
                operation="get_logs",
                parameters={
                    "target": service,
                    "lines": 50,
                    "level": "error",
                    "since": "15m"
                },
                reasoning="Check recent error logs for incident patterns",
                expected_duration="45s",
                success_criteria="Error patterns identified or no critical errors",
                next_actions=["If errors found → analyze patterns", "If clean → check health"]
            ),
            DiagnosticStep(
                phase=DiagnosticPhase.VALIDATION,
                operation="health_check",
                parameters={
                    "target": service,
                    "endpoints": ["/health"],
                    "retries": 3
                },
                reasoning="Verify service health status",
                expected_duration="30s",
                success_criteria="Health endpoints responding correctly",
                next_actions=["If unhealthy → restart service", "If healthy → monitor"]
            )
        ]
        
        self.logger.info(f"Generated {len(steps)} template-based diagnostic steps")
        return steps
    
    def _organize_steps_by_phases(self, steps: List[DiagnosticStep]) -> Dict[DiagnosticPhase, List[DiagnosticStep]]:
        """Organize diagnostic steps by phases"""
        phases = {}
        
        for step in steps:
            if step.phase not in phases:
                phases[step.phase] = []
            phases[step.phase].append(step)
        
        # Sort steps within each phase by priority
        for phase in phases:
            phases[phase].sort(key=lambda s: s.priority)
        
        return phases
    
    def _calculate_estimated_duration(self, phases: Dict[DiagnosticPhase, List[DiagnosticStep]]) -> str:
        """Calculate estimated total duration for diagnostic plan"""
        total_minutes = 0
        
        for phase, steps in phases.items():
            for step in steps:
                duration_str = step.expected_duration
                # Parse duration (e.g., "30s", "2m", "5m")
                if duration_str.endswith('s'):
                    total_minutes += int(duration_str[:-1]) / 60
                elif duration_str.endswith('m'):
                    total_minutes += int(duration_str[:-1])
                else:
                    total_minutes += 2  # Default 2 minutes
        
        if total_minutes < 60:
            return f"{int(total_minutes)}m"
        else:
            hours = int(total_minutes // 60)
            minutes = int(total_minutes % 60)
            return f"{hours}h {minutes}m"
    
    async def optimize_plan_based_on_results(self, plan: DiagnosticPlan, completed_steps: List[Dict[str, Any]]) -> DiagnosticPlan:
        """Optimize remaining diagnostic plan based on completed step results"""
        self.logger.info(f"Optimizing diagnostic plan based on {len(completed_steps)} completed steps")
        
        # Analyze completed step results
        insights = self._analyze_step_results(completed_steps)
        
        # Generate optimized steps for remaining phases
        remaining_phases = [phase for phase in plan.phases.keys() 
                          if phase not in [DiagnosticPhase(step["phase"]) for step in completed_steps]]
        
        if remaining_phases:
            # Create optimization context
            optimization_context = {
                **plan.context,
                "completed_steps": completed_steps,
                "insights": insights,
                "remaining_phases": [phase.value for phase in remaining_phases]
            }
            
            # Generate optimized steps
            optimized_steps = await self._generate_optimized_steps(optimization_context)
            
            # Update plan with optimized steps
            for step in optimized_steps:
                if step.phase in plan.phases:
                    plan.phases[step.phase].append(step)
                else:
                    plan.phases[step.phase] = [step]
        
        return plan
    
    def _analyze_step_results(self, completed_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze completed step results to extract insights"""
        insights = {
            "high_resource_usage": False,
            "error_patterns_found": False,
            "service_healthy": True,
            "performance_issues": False,
            "suggested_actions": []
        }
        
        for step in completed_steps:
            if step.get("success", False):
                operation = step.get("operation", "")
                output = step.get("output", "")
                
                if operation == "check_resources":
                    # Analyze resource usage patterns
                    if any(keyword in output.lower() for keyword in ["high", "exceeded", "critical"]):
                        insights["high_resource_usage"] = True
                        insights["suggested_actions"].append("Scale service or optimize resources")
                
                elif operation == "get_logs":
                    # Analyze log patterns
                    if any(keyword in output.lower() for keyword in ["error", "exception", "failed"]):
                        insights["error_patterns_found"] = True
                        insights["suggested_actions"].append("Investigate specific error patterns")
                
                elif operation == "health_check":
                    # Analyze health status
                    if "unhealthy" in output.lower() or not step.get("success", True):
                        insights["service_healthy"] = False
                        insights["suggested_actions"].append("Service restart may be required")
        
        return insights
    
    async def _generate_optimized_steps(self, context: Dict[str, Any]) -> List[DiagnosticStep]:
        """Generate optimized diagnostic steps based on previous results"""
        insights = context.get("insights", {})
        
        # Simple optimization logic - could be enhanced with more sophisticated AI
        optimized_steps = []
        
        if insights.get("high_resource_usage") and DiagnosticPhase.RESOLUTION in context.get("remaining_phases", []):
            optimized_steps.append(
                DiagnosticStep(
                    phase=DiagnosticPhase.RESOLUTION,
                    operation="scale_service",
                    parameters={
                        "target": context["incident"]["service"],
                        "replicas": 2,
                        "strategy": "gradual"
                    },
                    reasoning="High resource usage detected, scaling service to handle load",
                    expected_duration="2m",
                    success_criteria="Service scaled successfully with improved performance",
                    next_actions=["Monitor resource usage", "Validate performance improvement"]
                )
            )
        
        if not insights.get("service_healthy") and DiagnosticPhase.RESOLUTION in context.get("remaining_phases", []):
            optimized_steps.append(
                DiagnosticStep(
                    phase=DiagnosticPhase.RESOLUTION,
                    operation="restart_service",
                    parameters={
                        "target": context["incident"]["service"],
                        "strategy": "graceful",
                        "health_check": True,
                        "backup": True
                    },
                    reasoning="Service health check failed, graceful restart required",
                    expected_duration="3m",
                    success_criteria="Service restarted and health checks passing",
                    next_actions=["Monitor service stability", "Verify functionality"]
                )
            )
        
        return optimized_steps 