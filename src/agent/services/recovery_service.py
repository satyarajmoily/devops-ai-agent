"""Pure AI-driven recovery service without any hardcoded patterns."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from agent.core.ai_context import AIContextGatherer
from agent.core.ai_reasoning import AIDevOpsReasoning, AIDecision
from agent.core.ai_executor import FlexibleActionExecutor, PlanExecutionResult
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
        self.action_executor = FlexibleActionExecutor()
        
        self.logger.info("🤖 Pure AI Recovery Service initialized - zero hardcoded patterns")
    
    async def execute_recovery(self, alert_data: Dict) -> AIRecoveryResult:
        """Execute pure AI-driven recovery operation.
        
        Args:
            alert_data: Alert data from webhook
            
        Returns:
            AI recovery result
        """
        start_time = datetime.utcnow()
        
        # Extract basic alert info for logging
        alert_name = self._extract_alert_name(alert_data)
        service_name = self._extract_service_name(alert_data)
        
        self.logger.info(f"🤖 Starting AI-driven recovery for alert: {alert_name}")
        self.logger.info(f"   Target service: {service_name}")
        self.logger.info("   AI will analyze the situation and decide what to do...")
        
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
            self.logger.info(f"📋 Action Plan: {len(ai_decision.action_plan)} steps")
            self.logger.info(f"🎯 Confidence: {ai_decision.confidence:.2f}")
            
            # Step 3: Execute AI-generated plan
            if ai_decision.action_plan:
                self.logger.info("⚡ Executing AI-generated action plan...")
                execution_result = await self.action_executor.execute_ai_plan(ai_decision, context)
                
                # Calculate results
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                return AIRecoveryResult(
                    success=execution_result.success,
                    alert_name=alert_name,
                    service_name=service_name,
                    ai_analysis=ai_decision.analysis,
                    root_cause=ai_decision.root_cause,
                    ai_decision=ai_decision.decision,
                    actions_executed=len(execution_result.actions_executed),
                    duration_seconds=duration,
                    confidence=ai_decision.confidence,
                    escalation_required=execution_result.escalation_required,
                    lessons_learned=execution_result.lessons_learned,
                    execution_details=self._create_execution_summary(execution_result)
                )
            else:
                # AI decided no actions needed or immediate escalation
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                escalation_needed = any(criteria in ai_decision.decision.lower() 
                                      for criteria in ["escalate", "human", "manual"])
                
                return AIRecoveryResult(
                    success=not escalation_needed,
                    alert_name=alert_name,
                    service_name=service_name,
                    ai_analysis=ai_decision.analysis,
                    root_cause=ai_decision.root_cause,
                    ai_decision=ai_decision.decision,
                    actions_executed=0,
                    duration_seconds=duration,
                    confidence=ai_decision.confidence,
                    escalation_required=escalation_needed,
                    lessons_learned=[f"AI determined no automated actions needed: {ai_decision.decision}"]
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
    
    def _create_execution_summary(self, execution_result: PlanExecutionResult) -> Dict:
        """Create summary of execution results."""
        return {
            "total_actions": len(execution_result.actions_executed),
            "successful_actions": sum(1 for action in execution_result.actions_executed if action.success),
            "failed_actions": sum(1 for action in execution_result.actions_executed if not action.success),
            "execution_time": execution_result.total_duration,
            "action_types": [action.action_type for action in execution_result.actions_executed],
            "final_success": execution_result.success,
            "escalation_needed": execution_result.escalation_required
        }


# For backward compatibility - replace the old RecoveryService
class RecoveryService:
    """Wrapper for backward compatibility with pure AI recovery."""
    
    def __init__(self):
        """Initialize wrapper."""
        self.ai_recovery = PureAIRecoveryService()
        self.logger = logging.getLogger(__name__)
        
        self.logger.warning("⚠️ Old RecoveryService is deprecated - using pure AI recovery")
    
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
            "steps_executed": [{"action": "ai_driven_recovery", "success": ai_result.success}],
            "duration_seconds": ai_result.duration_seconds,
            "error_message": None if ai_result.success else "AI recovery failed",
            "recommendations": ai_result.lessons_learned,
            "metrics": {
                "ai_confidence": ai_result.confidence,
                "actions_executed": ai_result.actions_executed,
                "escalation_required": ai_result.escalation_required
            }
        } 