"""
Universal Infrastructure Command Interface
Environment-agnostic infrastructure operations with AI intelligence
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import existing components
from .config.universal_config import UniversalConfigLoader
from .operations.operation_registry import OperationRegistry
from .executors import DockerExecutor, OCIExecutor

# Import new AI intelligence components
from .ai_intelligence import (
    DiagnosticPlanner, 
    CreativeCommandGenerator, 
    ContextEnricher,
    PatternMatcher,
    WorkflowEngine
)

logger = logging.getLogger(__name__)

class UniversalInfrastructureInterface:
    """
    Enhanced Universal Infrastructure Interface with AI Intelligence
    Provides intelligent infrastructure operations with multi-phase diagnostics
    """
    
    def __init__(self):
        """Initialize the Universal Infrastructure Interface"""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = UniversalConfigLoader()
        self.environment = self.config.get_current_environment()
        
        # Initialize operation registry
        self.registry = OperationRegistry()
        
        # Initialize executor for current environment
        self.executor = self._get_executor_for_environment()
        
        # Initialize AI intelligence components
        self._initialize_ai_intelligence()
        
        self.logger.info(f"Universal Infrastructure Interface initialized for {self.environment}")
    
    def _get_executor_for_environment(self):
        """Get appropriate executor for current environment"""
        env_type = self.config.get_environment_type()
        
        if env_type in ["docker", "docker_compose"]:
            return DockerExecutor(self.config)
        elif env_type == "oci":
            return OCIExecutor(self.config)
        else:
            raise ValueError(f"Unsupported environment type: {env_type}")
    
    def _initialize_ai_intelligence(self):
        """Initialize AI intelligence components"""
        try:
            # Core AI components
            self.diagnostic_planner = DiagnosticPlanner(self.config)
            self.command_generator = CreativeCommandGenerator(self.config)
            self.context_enricher = ContextEnricher(self.config)
            self.pattern_matcher = PatternMatcher(self.config)
            self.workflow_engine = WorkflowEngine(self.config, self)
            
            self.ai_enabled = True
            self.logger.info("AI Intelligence components initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"AI Intelligence initialization failed: {e}")
            self.ai_enabled = False
            
            # Initialize fallback components
            self.diagnostic_planner = None
            self.command_generator = None
            self.context_enricher = None
            self.pattern_matcher = None
            self.workflow_engine = None
    
    async def execute_operation(self, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single infrastructure operation"""
        
        # Validate operation exists
        operation_name = operation.get("name")
        available_ops = self.registry.get_available_operations(self.environment)
        
        if operation_name not in available_ops:
            return {
                "success": False,
                "error": f"Operation {operation_name} not available in {self.environment}",
                "available_operations": available_ops
            }
        
        # Validate parameters
        try:
            validation_result = self.registry.validate_operation_parameters(operation_name, operation.get("parameters", {}))
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": f"Invalid parameters: {validation_result['errors']}",
                    "parameter_schema": self.registry.get_operation_schema(operation_name)
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Parameter validation failed: {e}"
            }
        
        # Execute operation through executor
        start_time = datetime.now()
        
        try:
            result = await self.executor.execute_operation(operation_name, operation.get("parameters", {}))
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Add execution metadata
            result["metadata"] = {
                "operation": operation_name,
                "environment": self.environment,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat(),
                "parameters_used": operation.get("parameters", {})
            }
            
            # Record execution for learning (if AI enabled)
            if self.ai_enabled and self.context_enricher:
                execution_record = {
                    "operation": operation_name,
                    "parameters": operation.get("parameters", {}),
                    "success": result.get("success", False),
                    "duration": execution_time,
                    "environment": self.environment
                }
                self.context_enricher.record_execution(execution_record)
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            error_result = {
                "success": False,
                "error": str(e),
                "metadata": {
                    "operation": operation_name,
                    "environment": self.environment,
                    "execution_time": execution_time,
                    "timestamp": start_time.isoformat(),
                    "parameters_used": operation.get("parameters", {})
                }
            }
            
            self.logger.error(f"Operation {operation_name} failed: {e}")
            return error_result
    
    async def create_diagnostic_plan(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an intelligent diagnostic plan for an infrastructure incident
        
        Args:
            alert_data: Alert information including service, severity, symptoms
        
        Returns:
            Diagnostic plan with AI-powered step recommendations
        """
        if not self.ai_enabled or not self.diagnostic_planner:
            return await self._create_fallback_diagnostic_plan(alert_data)
        
        try:
            # Generate comprehensive AI context
            incident_context = await self.generate_ai_context(alert_data)
            
            # Create diagnostic plan using AI
            diagnostic_plan = await self.diagnostic_planner.create_diagnostic_plan(incident_context)
            
            # Find matching historical patterns
            pattern_matches = await self.pattern_matcher.find_matching_patterns(incident_context)
            
            # Convert to serializable format
            plan_dict = {
                "incident_id": diagnostic_plan.incident_id,
                "service": diagnostic_plan.service,
                "alert_name": diagnostic_plan.alert_name,
                "severity": diagnostic_plan.severity,
                "estimated_duration": diagnostic_plan.estimated_duration,
                "created_at": diagnostic_plan.created_at.isoformat(),
                "phases": {},
                "pattern_matches": [],
                "ai_insights": {
                    "context_confidence": incident_context.get("context_confidence", {}),
                    "pattern_count": len(pattern_matches),
                    "has_historical_data": len(pattern_matches) > 0
                }
            }
            
            # Convert phases to serializable format
            for phase, steps in diagnostic_plan.phases.items():
                plan_dict["phases"][phase.value] = []
                for step in steps:
                    step_dict = {
                        "operation": step.operation,
                        "parameters": step.parameters,
                        "reasoning": step.reasoning,
                        "expected_duration": step.expected_duration,
                        "success_criteria": step.success_criteria,
                        "next_actions": step.next_actions,
                        "priority": step.priority
                    }
                    plan_dict["phases"][phase.value].append(step_dict)
            
            # Add pattern matches
            for match in pattern_matches:
                match_dict = {
                    "pattern_id": match.pattern_id,
                    "confidence": match.confidence,
                    "matched_symptoms": match.matched_symptoms,
                    "suggested_actions": match.suggested_actions,
                    "estimated_resolution_time": match.estimated_resolution_time,
                    "pattern_frequency": match.pattern_frequency
                }
                plan_dict["pattern_matches"].append(match_dict)
            
            self.logger.info(f"Created AI diagnostic plan with {len(diagnostic_plan.phases)} phases and {len(pattern_matches)} pattern matches")
            return plan_dict
            
        except Exception as e:
            self.logger.error(f"AI diagnostic planning failed: {e}")
            return await self._create_fallback_diagnostic_plan(alert_data)
    
    async def execute_diagnostic_workflow(self, diagnostic_plan: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a complete diagnostic workflow with intelligent step chaining
        
        Args:
            diagnostic_plan: Diagnostic plan to execute
            options: Execution options
        
        Returns:
            Workflow execution results
        """
        if not self.ai_enabled or not self.workflow_engine:
            return await self._execute_fallback_workflow(diagnostic_plan, options)
        
        try:
            # Convert dictionary plan back to DiagnosticPlan object
            from .ai_intelligence.diagnostic_planner import DiagnosticPlan, DiagnosticStep, DiagnosticPhase
            
            # Reconstruct phases
            phases = {}
            for phase_name, steps_data in diagnostic_plan.get("phases", {}).items():
                phase = DiagnosticPhase(phase_name)
                steps = []
                
                for step_data in steps_data:
                    step = DiagnosticStep(
                        phase=phase,
                        operation=step_data["operation"],
                        parameters=step_data["parameters"],
                        reasoning=step_data["reasoning"],
                        expected_duration=step_data["expected_duration"],
                        success_criteria=step_data["success_criteria"],
                        next_actions=step_data["next_actions"],
                        priority=step_data.get("priority", 1)
                    )
                    steps.append(step)
                
                phases[phase] = steps
            
            # Create DiagnosticPlan object
            plan = DiagnosticPlan(
                incident_id=diagnostic_plan["incident_id"],
                service=diagnostic_plan["service"],
                alert_name=diagnostic_plan["alert_name"],
                severity=diagnostic_plan["severity"],
                phases=phases,
                estimated_duration=diagnostic_plan["estimated_duration"],
                created_at=datetime.fromisoformat(diagnostic_plan["created_at"]),
                context={}
            )
            
            # Execute workflow
            workflow_execution = await self.workflow_engine.execute_workflow(plan, options)
            
            # Convert result to serializable format
            result = {
                "workflow_id": workflow_execution.workflow_id,
                "status": workflow_execution.status.value,
                "started_at": workflow_execution.started_at.isoformat(),
                "completed_at": workflow_execution.completed_at.isoformat() if workflow_execution.completed_at else None,
                "total_execution_time": workflow_execution.total_execution_time,
                "step_results": [],
                "success": workflow_execution.status.value == "completed",
                "failure_reason": workflow_execution.failure_reason
            }
            
            # Add step results
            for step_result in workflow_execution.step_results:
                step_dict = {
                    "step_id": step_result.step_id,
                    "status": step_result.status.value,
                    "execution_time": step_result.execution_time,
                    "timestamp": step_result.timestamp.isoformat(),
                    "operation_result": step_result.operation_result,
                    "error_message": step_result.error_message,
                    "insights": step_result.insights
                }
                result["step_results"].append(step_dict)
            
            # Learn from workflow execution if AI enabled
            if self.pattern_matcher:
                await self._learn_from_workflow_execution(workflow_execution)
            
            self.logger.info(f"Workflow {workflow_execution.workflow_id} completed with status: {workflow_execution.status.value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "workflow_id": None,
                "status": "failed"
            }
    
    async def generate_custom_commands(self, incident_context: Dict[str, Any], investigation_focus: str, max_commands: int = 5) -> Dict[str, Any]:
        """
        Generate custom diagnostic commands beyond predefined operations
        
        Args:
            incident_context: Context about the incident
            investigation_focus: Area to focus on (network, performance, security, etc.)
            max_commands: Maximum number of commands to generate
        
        Returns:
            Generated commands with safety metadata
        """
        if not self.ai_enabled or not self.command_generator:
            return {
                "success": False,
                "error": "AI command generation not available",
                "commands": []
            }
        
        try:
            # Generate custom commands
            generated_commands = await self.command_generator.generate_custom_commands(
                incident_context, investigation_focus, max_commands
            )
            
            # Convert to serializable format
            commands_data = []
            for cmd in generated_commands:
                cmd_dict = {
                    "command": cmd.command,
                    "category": cmd.category.value,
                    "purpose": cmd.purpose,
                    "expected_output": cmd.expected_output,
                    "risk_level": cmd.risk_level,
                    "timeout": cmd.timeout,
                    "environment_constraints": cmd.environment_constraints,
                    "fallback_commands": cmd.fallback_commands,
                    "interpretation_hints": cmd.interpretation_hints,
                    "explanation": self.command_generator.get_command_explanation(cmd)
                }
                commands_data.append(cmd_dict)
            
            result = {
                "success": True,
                "commands": commands_data,
                "investigation_focus": investigation_focus,
                "total_generated": len(generated_commands),
                "safety_note": "All commands have been validated for safety. Review before execution."
            }
            
            self.logger.info(f"Generated {len(generated_commands)} custom commands for {investigation_focus} investigation")
            return result
            
        except Exception as e:
            self.logger.error(f"Custom command generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "commands": []
            }
    
    async def generate_ai_context(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive AI context for intelligent decision making
        Enhanced version with deep service architecture understanding
        """
        base_context = {
            # Incident information
            "incident": {
                "alert_name": alert_data.get("alertname", "unknown"),
                "service": alert_data.get("service", "unknown"),
                "severity": alert_data.get("severity", "medium"),
                "duration": alert_data.get("duration", "unknown"),
                "symptoms": alert_data.get("symptoms", []),
                "labels": alert_data.get("labels", {}),
                "annotations": alert_data.get("annotations", {})
            },
            
            # Environment information  
            "environment": {
                "current": self.environment,
                "type": self.config.get_environment_type(),
                "capabilities": self.registry.get_available_operations(self.environment)
            },
            
            # Available operations with detailed schemas
            "detailed_operations": {
                "operations": {
                    op_name: self.registry.get_operation_schema(op_name)
                    for op_name in self.registry.get_available_operations(self.environment)
                }
            }
        }
        
        # Enrich context with AI intelligence if available
        if self.ai_enabled and self.context_enricher:
            try:
                enriched_context = await self.context_enricher.enrich_incident_context(base_context)
                
                # Record incident for correlation analysis
                incident_record = {
                    "alert_name": alert_data.get("alertname"),
                    "service": alert_data.get("service"),
                    "severity": alert_data.get("severity"),
                    "symptoms": alert_data.get("symptoms", [])
                }
                self.context_enricher.record_incident(incident_record)
                
                return enriched_context
                
            except Exception as e:
                self.logger.warning(f"Context enrichment failed, using base context: {e}")
                return base_context
        
        return base_context
    
    async def _create_fallback_diagnostic_plan(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a basic diagnostic plan when AI is not available"""
        service = alert_data.get("service", "unknown")
        alert_name = alert_data.get("alertname", "unknown")
        
        # Basic diagnostic steps
        basic_plan = {
            "incident_id": f"{service}_{alert_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "service": service,
            "alert_name": alert_name,
            "severity": alert_data.get("severity", "medium"),
            "estimated_duration": "10m",
            "created_at": datetime.now().isoformat(),
            "phases": {
                "triage": [
                    {
                        "operation": "check_resources",
                        "parameters": {"target": service, "metrics": ["cpu", "memory"], "format": "summary"},
                        "reasoning": "Quick resource check to identify obvious issues",
                        "expected_duration": "30s",
                        "success_criteria": "Resource metrics obtained",
                        "next_actions": ["Analyze resource usage patterns"],
                        "priority": 1
                    }
                ],
                "investigation": [
                    {
                        "operation": "get_logs",
                        "parameters": {"target": service, "lines": 50, "level": "error"},
                        "reasoning": "Check recent error logs for incident patterns",
                        "expected_duration": "45s",
                        "success_criteria": "Log patterns identified",
                        "next_actions": ["Analyze error patterns"],
                        "priority": 1
                    }
                ]
            },
            "pattern_matches": [],
            "ai_insights": {
                "context_confidence": {"overall_confidence": 0.3, "confidence_level": "low"},
                "pattern_count": 0,
                "has_historical_data": False
            }
        }
        
        self.logger.info("Created fallback diagnostic plan")
        return basic_plan
    
    async def _execute_fallback_workflow(self, diagnostic_plan: Dict[str, Any], options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a basic workflow when AI workflow engine is not available"""
        workflow_id = f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        step_results = []
        
        # Execute steps from all phases
        for phase_name, steps in diagnostic_plan.get("phases", {}).items():
            for i, step in enumerate(steps):
                step_id = f"{phase_name}_{i}"
                
                # Execute operation
                operation = {
                    "name": step["operation"],
                    "parameters": step["parameters"]
                }
                
                result = await self.execute_operation(operation)
                
                step_result = {
                    "step_id": step_id,
                    "status": "completed" if result.get("success") else "failed",
                    "execution_time": result.get("metadata", {}).get("execution_time", 0),
                    "timestamp": datetime.now().isoformat(),
                    "operation_result": result,
                    "error_message": result.get("error") if not result.get("success") else None,
                    "insights": {}
                }
                
                step_results.append(step_result)
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "total_execution_time": total_time,
            "step_results": step_results,
            "success": True,
            "failure_reason": None
        }
    
    async def _learn_from_workflow_execution(self, workflow_execution):
        """Learn from workflow execution results"""
        try:
            # Extract lessons from workflow
            actions_taken = []
            for step_result in workflow_execution.step_results:
                if step_result.status.value == "completed":
                    actions_taken.append(step_result.operation_result.get("metadata", {}).get("operation", "unknown"))
            
            outcome = {
                "success": workflow_execution.status.value == "completed",
                "duration": workflow_execution.total_execution_time,
                "lessons_learned": []
            }
            
            # Reconstruct incident context from plan
            incident_context = {
                "incident": {
                    "service": workflow_execution.plan.service,
                    "alert_name": workflow_execution.plan.alert_name,
                    "severity": workflow_execution.plan.severity,
                    "symptoms": []  # Would need to be preserved from original context
                }
            }
            
            # Learn from resolution
            await self.pattern_matcher.learn_from_resolution(incident_context, actions_taken, outcome)
            
        except Exception as e:
            self.logger.warning(f"Failed to learn from workflow execution: {e}")
    
    def get_ai_analytics(self) -> Dict[str, Any]:
        """Get analytics about AI intelligence components"""
        analytics = {
            "ai_enabled": self.ai_enabled,
            "components_status": {
                "diagnostic_planner": self.diagnostic_planner is not None,
                "command_generator": self.command_generator is not None,
                "context_enricher": self.context_enricher is not None,
                "pattern_matcher": self.pattern_matcher is not None,
                "workflow_engine": self.workflow_engine is not None
            }
        }
        
        if self.ai_enabled:
            try:
                if self.pattern_matcher:
                    analytics["pattern_analytics"] = self.pattern_matcher.get_pattern_analytics()
                
                if self.workflow_engine:
                    analytics["workflow_analytics"] = self.workflow_engine.get_workflow_analytics()
                
            except Exception as e:
                analytics["analytics_error"] = str(e)
        
        return analytics
    
    def get_operation_registry_info(self) -> Dict[str, Any]:
        """Get operation registry information"""
        return {
            "environment": self.environment,
            "available_operations": self.registry.get_available_operations(self.environment),
            "total_operations": len(self.registry.get_available_operations(self.environment)),
            "operation_schemas": {
                op_name: self.registry.get_operation_schema(op_name)
                for op_name in self.registry.get_available_operations(self.environment)
            }
        } 