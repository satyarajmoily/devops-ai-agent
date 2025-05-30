"""Pure AI-driven recovery service without any hardcoded patterns."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from agent.core.ai_context import AIContextGatherer
from agent.core.ai_reasoning import AIDevOpsReasoning, AIDecision
from agent.core.ai_executor import intelligent_executor, PlanExecutionResult
from agent.config.settings import get_settings


class AIRecoveryResult(BaseModel):
    """Result of AI-driven recovery operation."""
    
    success: bool = Field(..., description="Overall recovery success")
    alert_name: str = Field(..., description="Alert that triggered recovery")
    service_name: str = Field(..., description="Target service")
    ai_analysis: str = Field(..., description="AI's analysis of the situation")
    root_cause: str = Field(..., description="AI-identified root cause")
    ai_decision: str = Field(..., description="AI's decision")
    actions_executed: int = Field(..., description="Number of actions executed")
    duration_seconds: float = Field(..., description="Total recovery duration")
    confidence: float = Field(..., description="AI confidence in the solution")
    escalation_required: bool = Field(default=False, description="Whether human intervention is needed")
    lessons_learned: List[str] = Field(default_factory=list, description="Insights from this recovery")
    execution_details: Optional[Dict] = Field(default=None, description="Detailed execution results")


class PureAIRecoveryService:
    """AI-driven recovery service with zero hardcoded patterns."""
    
    def __init__(self):
        """Initialize AI recovery service."""
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI components
        self.context_gatherer = AIContextGatherer()
        self.ai_reasoner = AIDevOpsReasoning()
        
        self.logger.info("🤖 Pure AI Recovery Service initialized - intelligent diagnostic system active")
    
    async def execute_recovery(self, alert_data: Dict) -> AIRecoveryResult:
        """Execute pure AI-driven recovery operation with intelligent diagnostics.
        
        Args:
            alert_data: Alert data from webhook
            
        Returns:
            AI recovery result with comprehensive diagnostic information
        """
        start_time = datetime.utcnow()
        
        # Extract basic alert info for logging
        alert_name = self._extract_alert_name(alert_data)
        service_name = self._extract_service_name(alert_data)
        
        self.logger.info(f"🤖 Starting AI-driven recovery for alert: {alert_name}")
        self.logger.info(f"   Target service: {service_name}")
        self.logger.info("   AI will analyze the situation and create intelligent diagnostic plan...")
        
        try:
            # Step 1: Gather comprehensive context
            self.logger.info("📊 Gathering comprehensive system context...")
            context = await self.context_gatherer.gather_complete_context(alert_data)
            
            # Step 2: AI analysis and decision making
            self.logger.info("🧠 AI analyzing situation and making decision...")
            ai_decision = await self.ai_reasoner.analyze_and_decide(context)
            
            self.logger.info(f"🎯 AI Analysis: {ai_decision.analysis[:200]}...")
            self.logger.info(f"🔍 Root Cause: {ai_decision.root_cause}")
            self.logger.info(f"💡 AI Decision: {ai_decision.decision}")
            self.logger.info(f"🎯 Confidence: {ai_decision.confidence:.2f}")
            
            # Step 3: Execute AI-generated intelligent diagnostic plan
            self.logger.info("⚡ Creating and executing intelligent diagnostic plan...")
            execution_result = await intelligent_executor.execute_ai_plan(ai_decision, context)
            
            # Calculate results
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract lessons learned from execution
            lessons_learned = self._extract_lessons_learned(execution_result, ai_decision)
            
            return AIRecoveryResult(
                success=execution_result.success,
                alert_name=alert_name,
                service_name=service_name,
                ai_analysis=ai_decision.analysis,
                root_cause=ai_decision.root_cause,
                ai_decision=ai_decision.decision,
                actions_executed=len(execution_result.executed_operations),
                duration_seconds=duration,
                confidence=ai_decision.confidence,
                escalation_required=execution_result.escalation_required,
                lessons_learned=lessons_learned,
                execution_details=self._create_execution_summary(execution_result)
            )
                
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"❌ Critical error in AI recovery: {e}")
            
            return AIRecoveryResult(
                success=False,
                alert_name=alert_name,
                service_name=service_name,
                ai_analysis=f"AI recovery system failed: {e}",
                root_cause="AI system failure",
                ai_decision="Escalate to human due to AI system failure",
                actions_executed=0,
                duration_seconds=duration,
                confidence=0.0,
                escalation_required=True,
                lessons_learned=[f"AI recovery system failure: {e}"]
            )
    
    def _extract_alert_name(self, alert_data: Dict) -> str:
        """Extract alert name from alert data."""
        alerts = alert_data.get('alerts', [])
        if alerts:
            return alerts[0].get('labels', {}).get('alertname', 'unknown')
        return 'unknown'
    
    def _extract_service_name(self, alert_data: Dict) -> str:
        """Extract service name from alert data."""
        alerts = alert_data.get('alerts', [])
        if alerts:
            labels = alerts[0].get('labels', {})
            return labels.get('service') or labels.get('job') or labels.get('container', 'unknown')
        return 'unknown'
    
    def _extract_lessons_learned(self, execution_result: PlanExecutionResult, ai_decision: AIDecision) -> List[str]:
        """Extract lessons learned from the execution."""
        lessons = []
        
        # Plan-level insights
        lessons.append(f"AI diagnostic plan type: {execution_result.plan_type}")
        lessons.append(f"Completed {execution_result.phases_completed}/{execution_result.total_phases} diagnostic phases")
        
        # Success/failure patterns
        successful_ops = [op for op in execution_result.executed_operations if op.get('success', False)]
        failed_ops = [op for op in execution_result.executed_operations if not op.get('success', True)]
        
        if successful_ops:
            successful_types = list(set([op.get('operation', 'unknown') for op in successful_ops]))
            lessons.append(f"Successful operations: {', '.join(successful_types)}")
        
        if failed_ops:
            failed_types = list(set([op.get('operation', 'unknown') for op in failed_ops]))
            lessons.append(f"Failed operations: {', '.join(failed_types)}")
        
        # Overall outcome
        if execution_result.success:
            lessons.append("AI diagnostic plan succeeded - automated resolution achieved")
        elif execution_result.escalation_required:
            lessons.append("AI diagnostic plan requires human intervention")
        else:
            lessons.append("AI diagnostic plan partially successful")
        
        # AI confidence correlation
        if ai_decision.confidence > 0.8 and execution_result.success:
            lessons.append("High AI confidence correlated with successful resolution")
        elif ai_decision.confidence < 0.5 and not execution_result.success:
            lessons.append("Low AI confidence correlated with resolution difficulties")
        
        return lessons
    
    def _create_execution_summary(self, execution_result: PlanExecutionResult) -> Dict:
        """Create comprehensive summary of execution results."""
        operation_stats = {}
        for op in execution_result.executed_operations:
            op_type = op.get('operation', 'unknown')
            if op_type not in operation_stats:
                operation_stats[op_type] = {'total': 0, 'successful': 0, 'failed': 0}
            
            operation_stats[op_type]['total'] += 1
            if op.get('success', False):
                operation_stats[op_type]['successful'] += 1
            else:
                operation_stats[op_type]['failed'] += 1
        
        return {
            "plan_type": execution_result.plan_type,
            "phases_completed": execution_result.phases_completed,
            "total_phases": execution_result.total_phases,
            "total_operations": len(execution_result.executed_operations),
            "successful_operations": sum(1 for op in execution_result.executed_operations if op.get('success', False)),
            "failed_operations": sum(1 for op in execution_result.executed_operations if not op.get('success', True)),
            "execution_time": execution_result.duration_seconds,
            "final_status": execution_result.final_status,
            "escalation_required": execution_result.escalation_required,
            "operation_statistics": operation_stats,
            "metadata": execution_result.metadata,
            "operations_executed": [
                {
                    "operation": op.get('operation', 'unknown'),
                    "target": op.get('target', 'unknown'),
                    "success": op.get('success', False),
                    "duration": op.get('duration_seconds', 0),
                    "phase": op.get('phase', 'unknown'),
                    "reasoning": op.get('reasoning', 'No reasoning provided')
                }
                for op in execution_result.executed_operations
            ]
        }


# For backward compatibility - replace the old RecoveryService
class RecoveryService:
    """Wrapper for backward compatibility with pure AI recovery."""
    
    def __init__(self):
        """Initialize wrapper."""
        self.ai_recovery = PureAIRecoveryService()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🔄 Recovery Service using intelligent AI diagnostics")
    
    async def execute_recovery(self, alert_data: Dict) -> Dict:
        """Execute recovery using AI system.
        
        Args:
            alert_data: Alert data from webhook
            
        Returns:
            Recovery result in old format for compatibility
        """
        ai_result = await self.ai_recovery.execute_recovery(alert_data)
        
        # Convert to old format for compatibility
        return {
            "success": ai_result.success,
            "alert_name": ai_result.alert_name,
            "service_name": ai_result.service_name,
            "steps_executed": [
                {
                    "action": f"intelligent_diagnostics_{ai_result.execution_details.get('plan_type', 'unknown')}", 
                    "success": ai_result.success,
                    "details": ai_result.execution_details
                }
            ],
            "duration_seconds": ai_result.duration_seconds,
            "error_message": None if ai_result.success else "AI intelligent diagnostics required escalation",
            "recommendations": ai_result.lessons_learned,
            "escalation_required": ai_result.escalation_required,
            "ai_analysis": ai_result.ai_analysis,
            "root_cause": ai_result.root_cause,
            "ai_decision": ai_result.ai_decision,
            "confidence": ai_result.confidence
        } 