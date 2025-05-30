"""AI-driven action executor for dynamic DevOps operations."""

import asyncio
import logging
import subprocess
import time
import json
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from agent.core.ai_reasoning import AIAction, AIDecision
from agent.core.universal_executor import universal_executor, OperationResult
from agent.core.ai_diagnostic_planner import ai_diagnostic_planner, DiagnosticPlan
from agent.config.settings import get_settings


class ActionResult(BaseModel):
    """Result of action execution."""
    
    success: bool = Field(..., description="Whether action succeeded")
    action_type: str = Field(..., description="Type of action executed")
    target: str = Field(..., description="Target of the action")
    command: Optional[str] = Field(default=None, description="Command that was executed")
    output: Optional[str] = Field(default=None, description="Output from action")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    duration_seconds: float = Field(..., description="Time taken to execute")
    validation_results: Dict = Field(default_factory=dict, description="Validation check results")
    additional_data: Dict = Field(default_factory=dict, description="Additional data from execution")


class PlanExecutionResult(BaseModel):
    """Result of executing a complete diagnostic plan."""
    
    success: bool = Field(..., description="Overall plan success")
    plan_type: str = Field(..., description="Type of diagnostic plan executed")
    phases_completed: int = Field(..., description="Number of phases completed")
    total_phases: int = Field(..., description="Total number of phases")
    executed_operations: List[Dict] = Field(default_factory=list, description="All executed operations")
    duration_seconds: float = Field(..., description="Total execution time")
    final_status: str = Field(..., description="Final status description")
    escalation_required: bool = Field(default=False, description="Whether escalation is needed")
    metadata: Dict = Field(default_factory=dict, description="Additional execution metadata")


class IntelligentActionExecutor:
    """Executes AI-generated diagnostic plans using universal infrastructure operations."""
    
    def __init__(self):
        """Initialize intelligent action executor."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
    
    async def execute_ai_plan(self, ai_decision: AIDecision, context: Dict) -> PlanExecutionResult:
        """Execute an AI-generated action plan using intelligent diagnostics.
        
        Args:
            ai_decision: AI decision with action plan
            context: Current system context
            
        Returns:
            Execution results with full diagnostic information
        """
        start_time = time.time()
        self.logger.info(f"🧠 Executing intelligent AI diagnostic plan")
        self.logger.info(f"📋 AI Analysis: {ai_decision.analysis}")
        self.logger.info(f"🔍 Root Cause: {ai_decision.root_cause}")
        self.logger.info(f"💡 AI Decision: {ai_decision.decision}")
        
        try:
            # Create comprehensive diagnostic plan
            alert_context = self._extract_alert_context(ai_decision, context)
            diagnostic_plan = await ai_diagnostic_planner.create_diagnostic_plan(alert_context)
            
            # Log the diagnostic strategy
            strategy_explanation = ai_diagnostic_planner.explain_diagnostic_strategy(diagnostic_plan)
            self.logger.info(f"📊 Diagnostic Strategy:\n{strategy_explanation}")
            
            # Execute the diagnostic plan
            execution_result = await self._execute_diagnostic_plan(diagnostic_plan)
            
            execution_result.duration_seconds = time.time() - start_time
            return execution_result
            
        except Exception as e:
            self.logger.error(f"❌ Intelligent plan execution failed: {e}")
            # Fallback to simple action execution
            return await self._execute_fallback_actions(ai_decision.action_plan, start_time)
    
    def _extract_alert_context(self, ai_decision: AIDecision, context: Dict) -> Dict[str, Any]:
        """Extract alert context for diagnostic planning."""
        
        # Extract service name from actions or context
        service = "unknown"
        for action in ai_decision.action_plan:
            if action.target and action.target != "unknown":
                service = action.target
                break
        
        # Determine problem symptoms from AI analysis
        symptoms = ai_decision.analysis or "Service appears to be down"
        
        # Extract severity from decision or default
        severity = "medium"
        if "critical" in ai_decision.decision.lower() or "urgent" in ai_decision.decision.lower():
            severity = "critical"
        elif "high" in ai_decision.decision.lower():
            severity = "high"
        
        return {
            "alert_name": context.get("alert_name", "ServiceDown"),
            "service": service,
            "severity": severity,
            "symptoms": symptoms,
            "duration": context.get("duration", "Unknown"),
            "recent_changes": context.get("recent_changes", "None reported"),
            "error_messages": context.get("error_messages", "None available")
        }
    
    async def _execute_diagnostic_plan(self, plan: DiagnosticPlan) -> PlanExecutionResult:
        """Execute a comprehensive diagnostic plan."""
        
        start_time = time.time()
        executed_operations = []
        phases_completed = 0
        escalation_required = False
        
        self.logger.info(f"🚀 Starting diagnostic plan execution: {plan.problem_type}")
        
        for phase_idx, phase in enumerate(plan.phases):
            self.logger.info(f"📍 Phase {phase_idx + 1}: {phase.name} (max {phase.max_duration}s)")
            
            phase_start_time = time.time()
            phase_success = True
            
            # Execute operations in the phase
            if phase.parallel_execution:
                # Execute operations in parallel
                tasks = []
                for operation in phase.operations:
                    task = self._execute_single_operation(operation)
                    tasks.append(task)
                
                operation_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for i, result in enumerate(operation_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"❌ Operation {phase.operations[i]['operation']} failed: {result}")
                        phase_success = False
                        executed_operations.append({
                            "operation": phase.operations[i]['operation'],
                            "success": False,
                            "error": str(result),
                            "phase": phase.name
                        })
                    else:
                        executed_operations.append({
                            **result.to_dict(),
                            "phase": phase.name,
                            "reasoning": phase.operations[i].get('reasoning', 'No reasoning provided')
                        })
                        if not result.success:
                            phase_success = False
            else:
                # Execute operations sequentially
                for operation in phase.operations:
                    result = await self._execute_single_operation(operation)
                    executed_operations.append({
                        **result.to_dict(),
                        "phase": phase.name,
                        "reasoning": operation.get('reasoning', 'No reasoning provided')
                    })
                    
                    if not result.success:
                        phase_success = False
                        self.logger.warning(f"⚠️ Operation {operation['operation']} failed, continuing with phase...")
            
            phase_duration = time.time() - phase_start_time
            
            if phase_success:
                phases_completed += 1
                self.logger.info(f"✅ Phase {phase.name} completed successfully in {phase_duration:.1f}s")
            else:
                self.logger.warning(f"⚠️ Phase {phase.name} completed with failures in {phase_duration:.1f}s")
                phases_completed += 1  # Count as completed even with failures
            
            # Check if we should escalate based on phase results
            if not phase_success and phase.name in ["immediate_triage", "resolution"]:
                escalation_required = True
                self.logger.warning(f"🚨 Critical phase {phase.name} failed, escalation may be required")
        
        # Determine final status
        overall_success = phases_completed == len(plan.phases) and not escalation_required
        
        if overall_success:
            final_status = "✅ Diagnostic plan completed successfully - issue resolved"
        elif escalation_required:
            final_status = "🚨 Diagnostic plan completed but escalation required"
        else:
            final_status = f"⚠️ Diagnostic plan partially completed ({phases_completed}/{len(plan.phases)} phases)"
        
        self.logger.info(f"🏁 {final_status}")
        
        return PlanExecutionResult(
            success=overall_success,
            plan_type=plan.problem_type,
            phases_completed=phases_completed,
            total_phases=len(plan.phases),
            executed_operations=executed_operations,
            duration_seconds=time.time() - start_time,
            final_status=final_status,
            escalation_required=escalation_required,
            metadata={
                "plan_severity": plan.severity,
                "plan_environment": plan.environment,
                "estimated_duration": plan.estimated_duration,
                "success_criteria": plan.success_criteria,
                "escalation_triggers": plan.escalation_triggers
            }
        )
    
    async def _execute_single_operation(self, operation: Dict[str, Any]) -> OperationResult:
        """Execute a single infrastructure operation."""
        
        op_name = operation['operation']
        parameters = operation['parameters']
        reasoning = operation.get('reasoning', 'No reasoning provided')
        
        self.logger.info(f"🔧 Executing {op_name} on {parameters.get('target', 'unknown')}")
        self.logger.info(f"   💭 Reasoning: {reasoning}")
        
        try:
            result = await universal_executor.execute_operation(op_name, parameters)
            
            if result.success:
                self.logger.info(f"   ✅ {op_name} succeeded: {result.output[:100]}...")
            else:
                self.logger.warning(f"   ❌ {op_name} failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"   💥 {op_name} execution error: {e}")
            return OperationResult(
                operation=op_name,
                target=parameters.get('target', 'unknown'),
                success=False,
                output="",
                error_message=str(e)
            )
    
    async def _execute_fallback_actions(self, action_plan: List[AIAction], start_time: float) -> PlanExecutionResult:
        """Execute fallback actions when intelligent planning fails."""
        
        self.logger.warning("🔄 Falling back to basic action execution")
        
        executed_operations = []
        success_count = 0
        
        for action in action_plan:
            # Convert AIAction to operation parameters
            operation_result = await self._convert_and_execute_action(action)
            executed_operations.append(operation_result.to_dict())
            
            if operation_result.success:
                success_count += 1
        
        overall_success = success_count == len(action_plan)
        
        return PlanExecutionResult(
            success=overall_success,
            plan_type="fallback_actions",
            phases_completed=1,
            total_phases=1,
            executed_operations=executed_operations,
            duration_seconds=time.time() - start_time,
            final_status=f"Fallback execution: {success_count}/{len(action_plan)} actions succeeded",
            escalation_required=not overall_success,
            metadata={"fallback_mode": True}
        )
    
    async def _convert_and_execute_action(self, action: AIAction) -> OperationResult:
        """Convert legacy AIAction to universal operation and execute."""
        
        # Map legacy action types to universal operations
        operation_mapping = {
            "restart_service": "restart_service",
            "restart_container": "restart_service",
            "check_logs": "get_logs",
            "analyze_logs": "get_logs",
            "check_health": "check_health",
            "verify_service": "check_health",
            "validate_service": "check_health",
            "docker_compose_up": "restart_service",
            "recreate_service": "restart_service",
            "compose_recreate": "restart_service",
            "run_command": "execute_command",
            "execute_command": "execute_command",
            "shell_command": "execute_command",
            "check_docker": "check_health",
            "docker_status": "check_health",
            "docker_info": "check_resources"
        }
        
        operation_name = operation_mapping.get(action.action_type, "execute_command")
        
        # Build parameters based on action
        parameters = {"target": action.target}
        
        if operation_name == "get_logs":
            parameters.update({
                "lines": 100,
                "level": "error" if "error" in action.action_type.lower() else "all"
            })
        elif operation_name == "restart_service":
            parameters.update({
                "strategy": "graceful",
                "timeout": action.timeout_seconds or 30,
                "health_check": True
            })
        elif operation_name == "execute_command":
            parameters.update({
                "command": action.command or "echo 'No command specified'",
                "timeout": action.timeout_seconds or 30
            })
        elif operation_name == "check_health":
            parameters.update({
                "timeout": action.timeout_seconds or 10,
                "retry_count": 1
            })
        elif operation_name == "check_resources":
            parameters.update({
                "metrics": ["cpu", "memory", "disk"],
                "format": "summary"
            })
        
        return await universal_executor.execute_operation(operation_name, parameters)


# Create global instance with new name to avoid conflicts
intelligent_executor = IntelligentActionExecutor() 