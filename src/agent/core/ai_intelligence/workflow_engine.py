"""
Workflow Engine
Intelligent operation chaining and multi-step diagnostic workflows
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from .diagnostic_planner import DiagnosticStep, DiagnosticPhase, DiagnosticPlan
from ...config.simple_config import get_config

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """Status of individual step execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_FOR_CONDITION = "waiting_for_condition"

@dataclass
class WorkflowStepResult:
    """Result of executing a workflow step"""
    step_id: str
    status: StepStatus
    operation_result: Dict[str, Any]
    execution_time: float
    timestamp: datetime
    error_message: Optional[str] = None
    insights: Dict[str, Any] = None

@dataclass
class WorkflowExecution:
    """Complete workflow execution tracking"""
    workflow_id: str
    plan: DiagnosticPlan
    status: WorkflowStatus
    started_at: datetime
    current_phase: Optional[DiagnosticPhase]
    current_step_index: int
    step_results: List[WorkflowStepResult]
    total_execution_time: float
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

class WorkflowEngine:
    """
    Intelligent workflow execution engine
    Executes diagnostic plans with adaptive logic and intelligent decision making
    """
    
    def __init__(self, config, universal_interface):
        """Initialize workflow engine"""
        self.config = config
        self.universal_interface = universal_interface
        self.logger = logging.getLogger(__name__)
        
        # Active workflow tracking
        self.active_workflows = {}
        self.workflow_history = []
        
        # Workflow execution configuration
        self.max_concurrent_workflows = 3
        self.step_timeout_default = 300  # 5 minutes
        self.workflow_timeout_default = 3600  # 1 hour
        
        # Adaptive decision rules
        self.decision_rules = self._load_decision_rules()
        
        self.logger.info("Workflow Engine initialized for intelligent operation chaining")
    
    def _load_decision_rules(self) -> Dict[str, Any]:
        """Load adaptive decision rules for workflow execution"""
        return {
            "resource_threshold_rules": {
                "high_cpu": {
                    "threshold": 80.0,
                    "actions": ["scale_service", "investigate_cpu_usage"],
                    "skip_if_below": 50.0
                },
                "high_memory": {
                    "threshold": 90.0,
                    "actions": ["restart_service", "investigate_memory_leak"],
                    "skip_if_below": 70.0
                },
                "high_disk": {
                    "threshold": 85.0,
                    "actions": ["cleanup_logs", "investigate_disk_usage"],
                    "skip_if_below": 60.0
                }
            },
            "error_pattern_rules": {
                "connection_errors": {
                    "patterns": ["connection refused", "timeout", "network error"],
                    "next_actions": ["check_network", "restart_service", "check_dependencies"]
                },
                "memory_errors": {
                    "patterns": ["out of memory", "oom", "memory exhausted"],
                    "next_actions": ["restart_service", "investigate_memory", "scale_service"]
                },
                "database_errors": {
                    "patterns": ["connection pool", "lock timeout", "deadlock"],
                    "next_actions": ["restart_database_connections", "optimize_queries", "check_db_health"]
                }
            },
            "conditional_execution": {
                "skip_restart_if_recently_restarted": {
                    "condition": "last_restart_within_minutes",
                    "threshold": 15,
                    "alternative_actions": ["investigate_logs", "check_dependencies"]
                },
                "skip_scaling_if_already_scaled": {
                    "condition": "recent_scaling_within_minutes", 
                    "threshold": 30,
                    "alternative_actions": ["monitor_performance", "check_resource_utilization"]
                }
            }
        }
    
    async def execute_workflow(self, plan: DiagnosticPlan, options: Dict[str, Any] = None) -> WorkflowExecution:
        """
        Execute a diagnostic workflow with intelligent decision making
        
        Args:
            plan: Diagnostic plan to execute
            options: Execution options (timeout, concurrency, etc.)
        
        Returns:
            Workflow execution result
        """
        workflow_id = f"workflow_{plan.incident_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        options = options or {}
        
        # Check concurrent workflow limits
        if len(self.active_workflows) >= self.max_concurrent_workflows:
            raise RuntimeError(f"Maximum concurrent workflows ({self.max_concurrent_workflows}) exceeded")
        
        self.logger.info(f"Starting workflow execution: {workflow_id}")
        
        # Create workflow execution
        workflow_execution = WorkflowExecution(
            workflow_id=workflow_id,
            plan=plan,
            status=WorkflowStatus.RUNNING,
            started_at=datetime.now(),
            current_phase=None,
            current_step_index=0,
            step_results=[],
            total_execution_time=0.0
        )
        
        # Add to active workflows
        self.active_workflows[workflow_id] = workflow_execution
        
        try:
            # Execute phases in order
            for phase in [DiagnosticPhase.TRIAGE, DiagnosticPhase.ISOLATION, 
                         DiagnosticPhase.ANALYSIS, DiagnosticPhase.RESOLUTION, 
                         DiagnosticPhase.VALIDATION]:
                
                if phase in plan.phases:
                    workflow_execution.current_phase = phase
                    
                    self.logger.info(f"Executing phase: {phase.value}")
                    
                    # Execute steps in this phase
                    phase_success = await self._execute_phase(workflow_execution, phase, options)
                    
                    if not phase_success:
                        # Phase failed, decide whether to continue or abort
                        should_continue = await self._decide_phase_failure_response(
                            workflow_execution, phase
                        )
                        
                        if not should_continue:
                            workflow_execution.status = WorkflowStatus.FAILED
                            workflow_execution.failure_reason = f"Phase {phase.value} failed and workflow terminated"
                            break
            
            # Complete workflow if not already failed
            if workflow_execution.status == WorkflowStatus.RUNNING:
                workflow_execution.status = WorkflowStatus.COMPLETED
                workflow_execution.completed_at = datetime.now()
                workflow_execution.total_execution_time = (
                    workflow_execution.completed_at - workflow_execution.started_at
                ).total_seconds()
                
                self.logger.info(f"Workflow completed successfully in {workflow_execution.total_execution_time:.1f}s")
            
        except Exception as e:
            workflow_execution.status = WorkflowStatus.FAILED
            workflow_execution.failure_reason = str(e)
            workflow_execution.completed_at = datetime.now()
            self.logger.error(f"Workflow execution failed: {e}")
        
        finally:
            # Remove from active workflows and add to history
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            self.workflow_history.append(workflow_execution)
            
            # Keep only recent history
            if len(self.workflow_history) > 100:
                self.workflow_history = self.workflow_history[-100:]
        
        return workflow_execution
    
    async def _execute_phase(self, workflow: WorkflowExecution, phase: DiagnosticPhase, options: Dict[str, Any]) -> bool:
        """Execute all steps in a diagnostic phase"""
        steps = workflow.plan.phases.get(phase, [])
        
        if not steps:
            self.logger.info(f"No steps defined for phase: {phase.value}")
            return True
        
        phase_success = True
        
        for step_index, step in enumerate(steps):
            workflow.current_step_index = step_index
            
            # Check if step should be executed based on adaptive logic
            should_execute = await self._should_execute_step(workflow, step)
            
            if not should_execute:
                # Skip step and record why
                step_result = WorkflowStepResult(
                    step_id=f"{phase.value}_{step_index}",
                    status=StepStatus.SKIPPED,
                    operation_result={"reason": "Skipped by adaptive logic"},
                    execution_time=0.0,
                    timestamp=datetime.now()
                )
                workflow.step_results.append(step_result)
                continue
            
            # Execute step
            step_result = await self._execute_step(workflow, step, step_index)
            workflow.step_results.append(step_result)
            
            # Analyze step result and decide next actions
            next_action = await self._analyze_step_result(workflow, step, step_result)
            
            if next_action == "abort_phase":
                phase_success = False
                break
            elif next_action == "skip_remaining":
                # Skip remaining steps in this phase
                break
            elif next_action == "add_extra_step":
                # Add additional step based on results
                extra_step = await self._generate_extra_step(workflow, step, step_result)
                if extra_step:
                    extra_result = await self._execute_step(workflow, extra_step, f"{step_index}_extra")
                    workflow.step_results.append(extra_result)
            
            # Brief pause between steps to avoid overwhelming the system
            await asyncio.sleep(1)
        
        return phase_success
    
    async def _should_execute_step(self, workflow: WorkflowExecution, step: DiagnosticStep) -> bool:
        """Determine if a step should be executed based on adaptive logic"""
        
        # Check if step is redundant based on previous results
        if await self._is_step_redundant(workflow, step):
            self.logger.info(f"Skipping redundant step: {step.operation}")
            return False
        
        # Check conditional execution rules
        if step.operation == "restart_service":
            # Don't restart if recently restarted
            if await self._was_recently_restarted(workflow, step.parameters.get("target")):
                self.logger.info(f"Skipping restart - service was recently restarted")
                return False
        
        elif step.operation == "scale_service":
            # Don't scale if recently scaled
            if await self._was_recently_scaled(workflow, step.parameters.get("target")):
                self.logger.info(f"Skipping scaling - service was recently scaled")
                return False
        
        # Check resource thresholds
        if step.operation == "check_resources":
            # Always execute resource checks
            return True
        
        return True
    
    async def _is_step_redundant(self, workflow: WorkflowExecution, step: DiagnosticStep) -> bool:
        """Check if step is redundant based on previous executions"""
        for previous_result in workflow.step_results:
            if (previous_result.operation_result.get("operation") == step.operation and
                previous_result.status == StepStatus.COMPLETED):
                
                # Check if parameters are similar
                prev_params = previous_result.operation_result.get("metadata", {}).get("parameters_used", {})
                current_params = step.parameters
                
                # Simple similarity check - could be enhanced
                if prev_params.get("target") == current_params.get("target"):
                    return True
        
        return False
    
    async def _was_recently_restarted(self, workflow: WorkflowExecution, service: str) -> bool:
        """Check if service was recently restarted"""
        # Check workflow history for recent restart operations
        recent_threshold = datetime.now() - timedelta(minutes=15)
        
        for result in workflow.step_results:
            if (result.operation_result.get("operation") == "restart_service" and
                result.timestamp > recent_threshold and
                result.operation_result.get("metadata", {}).get("parameters_used", {}).get("target") == service):
                return True
        
        return False
    
    async def _was_recently_scaled(self, workflow: WorkflowExecution, service: str) -> bool:
        """Check if service was recently scaled"""
        recent_threshold = datetime.now() - timedelta(minutes=30)
        
        for result in workflow.step_results:
            if (result.operation_result.get("operation") == "scale_service" and
                result.timestamp > recent_threshold and
                result.operation_result.get("metadata", {}).get("parameters_used", {}).get("target") == service):
                return True
        
        return False
    
    async def _execute_step(self, workflow: WorkflowExecution, step: DiagnosticStep, step_index) -> WorkflowStepResult:
        """Execute a single diagnostic step"""
        step_id = f"{workflow.current_phase.value}_{step_index}" if workflow.current_phase else str(step_index)
        start_time = datetime.now()
        
        self.logger.info(f"Executing step {step_id}: {step.operation}")
        
        try:
            # Prepare operation for execution
            operation = {
                "name": step.operation,
                "parameters": step.parameters
            }
            
            # Execute operation through universal interface
            result = await self.universal_interface.execute_operation(operation)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Determine step status based on operation result
            if result.get("success", False):
                status = StepStatus.COMPLETED
                error_message = None
            else:
                status = StepStatus.FAILED
                error_message = result.get("error", "Unknown error")
            
            # Extract insights from result
            insights = await self._extract_step_insights(step, result)
            
            step_result = WorkflowStepResult(
                step_id=step_id,
                status=status,
                operation_result=result,
                execution_time=execution_time,
                timestamp=datetime.now(),
                error_message=error_message,
                insights=insights
            )
            
            self.logger.info(f"Step {step_id} completed with status: {status.value}")
            return step_result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            step_result = WorkflowStepResult(
                step_id=step_id,
                status=StepStatus.FAILED,
                operation_result={"error": str(e)},
                execution_time=execution_time,
                timestamp=datetime.now(),
                error_message=str(e)
            )
            
            self.logger.error(f"Step {step_id} failed: {e}")
            return step_result
    
    async def _extract_step_insights(self, step: DiagnosticStep, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from step execution result"""
        insights = {
            "operation_type": step.operation,
            "phase": step.phase.value,
            "success": result.get("success", False),
            "patterns_detected": [],
            "metrics_extracted": {},
            "recommendations": []
        }
        
        output = result.get("output", "")
        
        # Extract patterns based on operation type
        if step.operation == "get_logs":
            insights["patterns_detected"] = self._detect_log_patterns(output)
        elif step.operation == "check_resources":
            insights["metrics_extracted"] = self._extract_resource_metrics(output)
        elif step.operation == "health_check":
            insights["health_status"] = self._analyze_health_output(output)
        
        # Generate recommendations based on insights
        insights["recommendations"] = self._generate_step_recommendations(step, insights)
        
        return insights
    
    def _detect_log_patterns(self, log_output: str) -> List[str]:
        """Detect patterns in log output"""
        patterns = []
        log_lower = log_output.lower()
        
        pattern_indicators = {
            "memory_issues": ["out of memory", "oom", "memory exhausted", "gc overhead"],
            "connection_issues": ["connection refused", "timeout", "connection reset"],
            "database_issues": ["deadlock", "lock timeout", "connection pool"],
            "performance_issues": ["slow query", "high cpu", "response time"],
            "security_issues": ["unauthorized", "forbidden", "authentication failed"]
        }
        
        for pattern_name, indicators in pattern_indicators.items():
            if any(indicator in log_lower for indicator in indicators):
                patterns.append(pattern_name)
        
        return patterns
    
    def _extract_resource_metrics(self, resource_output: str) -> Dict[str, Any]:
        """Extract resource metrics from output"""
        metrics = {}
        
        # Simple pattern matching for common metrics
        # In production, this would be more sophisticated
        import re
        
        # CPU percentage
        cpu_match = re.search(r'cpu[:\s]+(\d+(?:\.\d+)?)%?', resource_output.lower())
        if cpu_match:
            metrics["cpu_percent"] = float(cpu_match.group(1))
        
        # Memory percentage or usage
        memory_match = re.search(r'memory[:\s]+(\d+(?:\.\d+)?)%?', resource_output.lower())
        if memory_match:
            metrics["memory_percent"] = float(memory_match.group(1))
        
        # Disk usage
        disk_match = re.search(r'disk[:\s]+(\d+(?:\.\d+)?)%?', resource_output.lower())
        if disk_match:
            metrics["disk_percent"] = float(disk_match.group(1))
        
        return metrics
    
    def _analyze_health_output(self, health_output: str) -> Dict[str, Any]:
        """Analyze health check output"""
        health_lower = health_output.lower()
        
        health_status = {
            "overall_healthy": False,
            "issues_detected": [],
            "endpoints_checked": 0,
            "endpoints_healthy": 0
        }
        
        if "healthy" in health_lower:
            health_status["overall_healthy"] = True
        
        if "unhealthy" in health_lower or "failed" in health_lower:
            health_status["issues_detected"].append("health_check_failed")
        
        # Count endpoints if mentioned
        endpoint_matches = health_output.count("/health") + health_output.count("/ready")
        health_status["endpoints_checked"] = endpoint_matches
        
        return health_status
    
    def _generate_step_recommendations(self, step: DiagnosticStep, insights: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on step insights"""
        recommendations = []
        
        if not insights.get("success", False):
            recommendations.append(f"Retry {step.operation} with different parameters")
        
        # Recommendations based on detected patterns
        patterns = insights.get("patterns_detected", [])
        
        if "memory_issues" in patterns:
            recommendations.extend([
                "Investigate memory leaks",
                "Consider restarting service",
                "Review memory limits and configuration"
            ])
        
        if "connection_issues" in patterns:
            recommendations.extend([
                "Check network connectivity",
                "Verify service dependencies",
                "Review connection pool settings"
            ])
        
        # Recommendations based on metrics
        metrics = insights.get("metrics_extracted", {})
        
        if metrics.get("cpu_percent", 0) > 80:
            recommendations.append("High CPU usage detected - consider scaling or optimization")
        
        if metrics.get("memory_percent", 0) > 90:
            recommendations.append("High memory usage detected - investigate memory leaks")
        
        return recommendations
    
    async def _analyze_step_result(self, workflow: WorkflowExecution, step: DiagnosticStep, result: WorkflowStepResult) -> str:
        """Analyze step result and determine next action"""
        
        if result.status == StepStatus.FAILED:
            # Check if this is a critical failure that should abort the phase
            if step.operation in ["restart_service", "scale_service"]:
                return "abort_phase"
            else:
                return "continue"
        
        # Analyze insights for next actions
        insights = result.insights or {}
        patterns = insights.get("patterns_detected", [])
        
        # If memory issues detected, might want to add memory investigation step
        if "memory_issues" in patterns and step.operation == "get_logs":
            return "add_extra_step"
        
        # If health check shows all healthy, might skip some remaining steps
        if (step.operation == "health_check" and 
            insights.get("health_status", {}).get("overall_healthy", False)):
            return "skip_remaining"
        
        return "continue"
    
    async def _generate_extra_step(self, workflow: WorkflowExecution, original_step: DiagnosticStep, result: WorkflowStepResult) -> Optional[DiagnosticStep]:
        """Generate an extra step based on step results"""
        insights = result.insights or {}
        patterns = insights.get("patterns_detected", [])
        
        if "memory_issues" in patterns:
            # Add detailed memory investigation
            return DiagnosticStep(
                phase=original_step.phase,
                operation="check_resources",
                parameters={
                    "target": original_step.parameters.get("target", "unknown"),
                    "metrics": ["memory"],
                    "format": "detailed",
                    "historical": True
                },
                reasoning="Memory issues detected in logs, performing detailed memory analysis",
                expected_duration="60s",
                success_criteria="Memory usage patterns identified",
                next_actions=["Apply memory optimizations if needed"]
            )
        
        return None
    
    async def _decide_phase_failure_response(self, workflow: WorkflowExecution, failed_phase: DiagnosticPhase) -> bool:
        """Decide whether to continue workflow after phase failure"""
        
        # Critical phases that should abort workflow on failure
        critical_phases = [DiagnosticPhase.TRIAGE]
        
        if failed_phase in critical_phases:
            self.logger.warning(f"Critical phase {failed_phase.value} failed, aborting workflow")
            return False
        
        # For non-critical phases, check if we have enough successful steps to continue
        successful_steps = [r for r in workflow.step_results if r.status == StepStatus.COMPLETED]
        
        if len(successful_steps) >= 2:
            self.logger.info(f"Phase {failed_phase.value} failed but continuing with {len(successful_steps)} successful steps")
            return True
        else:
            self.logger.warning(f"Phase {failed_phase.value} failed with insufficient successful steps, aborting")
            return False
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause an active workflow"""
        if workflow_id in self.active_workflows:
            self.active_workflows[workflow_id].status = WorkflowStatus.PAUSED
            self.logger.info(f"Workflow {workflow_id} paused")
            return True
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            if workflow.status == WorkflowStatus.PAUSED:
                workflow.status = WorkflowStatus.RUNNING
                self.logger.info(f"Workflow {workflow_id} resumed")
                return True
        return False
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.CANCELLED
            workflow.completed_at = datetime.now()
            
            # Move to history
            del self.active_workflows[workflow_id]
            self.workflow_history.append(workflow)
            
            self.logger.info(f"Workflow {workflow_id} cancelled")
            return True
        return False
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow"""
        
        # Check active workflows
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
        else:
            # Check history
            workflow = next((w for w in self.workflow_history if w.workflow_id == workflow_id), None)
        
        if not workflow:
            return None
        
        return {
            "workflow_id": workflow.workflow_id,
            "status": workflow.status.value,
            "started_at": workflow.started_at.isoformat(),
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "current_phase": workflow.current_phase.value if workflow.current_phase else None,
            "total_steps": len(workflow.step_results),
            "successful_steps": len([r for r in workflow.step_results if r.status == StepStatus.COMPLETED]),
            "failed_steps": len([r for r in workflow.step_results if r.status == StepStatus.FAILED]),
            "execution_time": workflow.total_execution_time,
            "failure_reason": workflow.failure_reason
        }
    
    def get_workflow_analytics(self) -> Dict[str, Any]:
        """Get analytics about workflow executions"""
        all_workflows = list(self.active_workflows.values()) + self.workflow_history
        
        if not all_workflows:
            return {"total_workflows": 0}
        
        completed_workflows = [w for w in all_workflows if w.status == WorkflowStatus.COMPLETED]
        failed_workflows = [w for w in all_workflows if w.status == WorkflowStatus.FAILED]
        
        analytics = {
            "total_workflows": len(all_workflows),
            "active_workflows": len(self.active_workflows),
            "completed_workflows": len(completed_workflows),
            "failed_workflows": len(failed_workflows),
            "success_rate": len(completed_workflows) / len(all_workflows) if all_workflows else 0,
            "avg_execution_time": sum(w.total_execution_time for w in completed_workflows) / len(completed_workflows) if completed_workflows else 0,
            "most_common_failures": {},
            "phase_success_rates": {}
        }
        
        # Analyze failure patterns
        failure_reasons = [w.failure_reason for w in failed_workflows if w.failure_reason]
        failure_counts = {}
        for reason in failure_reasons:
            failure_counts[reason] = failure_counts.get(reason, 0) + 1
        
        analytics["most_common_failures"] = dict(sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        
        return analytics 