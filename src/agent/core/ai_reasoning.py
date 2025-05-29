"""AI-driven reasoning engine for DevOps decision making."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from agent.config.settings import get_settings


class AIAction(BaseModel):
    """AI-generated action."""
    
    action_type: str = Field(..., description="Type of action to perform")
    target: str = Field(..., description="Target of the action") 
    command: Optional[str] = Field(default=None, description="Specific command to run")
    reason: str = Field(..., description="AI's reasoning for this action")
    expected_outcome: str = Field(..., description="What AI expects this to achieve")
    risk_level: str = Field(..., description="Low/Medium/High risk assessment")
    timeout_seconds: int = Field(default=60, description="Timeout for this action")
    success_criteria: List[str] = Field(default_factory=list, description="How to determine success")


class AIDecision(BaseModel):
    """AI decision with full reasoning."""
    
    analysis: str = Field(..., description="AI's analysis of the situation")
    root_cause: str = Field(..., description="AI's assessment of root cause")
    decision: str = Field(..., description="AI's decision on what to do")
    action_plan: List[AIAction] = Field(default_factory=list, description="Ordered list of actions")
    risk_assessment: str = Field(..., description="Overall risk assessment")
    confidence: float = Field(..., description="AI confidence in this decision (0-1)")
    fallback_options: List[str] = Field(default_factory=list, description="Alternative approaches")
    escalation_criteria: List[str] = Field(default_factory=list, description="When to escalate to human")


class AIDevOpsReasoning:
    """Pure AI-driven reasoning for DevOps operations."""
    
    def __init__(self):
        """Initialize AI reasoning engine."""
        self.logger = logging.getLogger(__name__)
        
        # Get settings with proper LLM configuration
        self.settings = get_settings()
        
        # Initialize OpenAI client with configuration from settings
        self.llm = ChatOpenAI(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            timeout=self.settings.llm_timeout,
            api_key=self.settings.openai_api_key
        )
    
    async def analyze_and_decide(self, context: Dict) -> AIDecision:
        """Analyze situation and make AI-driven decision.
        
        Args:
            context: Complete context gathered from AIContextGatherer
            
        Returns:
            AI decision with reasoning and action plan
        """
        self.logger.info("Starting AI analysis and decision making...")
        
        try:
            # Create comprehensive prompt for AI analysis
            analysis_prompt = self._create_analysis_prompt(context)
            
            # Get AI analysis using proper async method
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=analysis_prompt)
            ]
            
            # Use ainvoke instead of agenerate for better async support
            response = await self.llm.ainvoke(messages)
            ai_response = response.content
            
            # Parse AI response into structured decision
            decision = self._parse_ai_response(ai_response, context)
            
            self.logger.info(f"AI analysis complete. Confidence: {decision.confidence:.2f}")
            self.logger.info(f"Root cause identified: {decision.root_cause}")
            self.logger.info(f"Action plan has {len(decision.action_plan)} steps")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in AI analysis: {e}")
            # Return minimal safe decision
            return AIDecision(
                analysis=f"AI analysis failed: {e}",
                root_cause="Unable to determine due to AI failure",
                decision="Escalate to human intervention",
                action_plan=[],
                risk_assessment="High - AI system unavailable",
                confidence=0.0,
                fallback_options=["Manual investigation required"],
                escalation_criteria=["AI system failure"]
            )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI DevOps engineer."""
        return """You are a senior DevOps engineer with 15+ years of experience managing production systems. 
        You have deep expertise in:
        - Docker and container orchestration
        - Kubernetes and microservices
        - System monitoring and observability 
        - Incident response and recovery
        - Infrastructure as code
        - Performance optimization
        - Security and compliance

        CORE PRINCIPLES:
        1. Safety first - never take risky actions without understanding impact
        2. Thorough analysis - understand the root cause before acting
        3. Minimal intervention - use the least disruptive solution that works
        4. Validation - always verify that solutions actually work
        5. Documentation - explain your reasoning clearly
        6. Escalation - know when human intervention is needed

        DECISION MAKING APPROACH:
        1. Analyze the complete situation objectively
        2. Identify the actual root cause (not just symptoms)
        3. Consider multiple solution approaches
        4. Choose the safest, most effective solution
        5. Plan validation steps to confirm success
        6. Identify fallback options if primary solution fails

        You respond with structured JSON containing your analysis, reasoning, and action plan.
        Be creative and adaptive - don't follow rigid patterns. Each situation is unique.
        Think through the problem step by step like a real DevOps engineer would."""
    
    def _create_analysis_prompt(self, context: Dict) -> str:
        """Create comprehensive analysis prompt for AI."""
        
        # Extract key information for AI focus
        alert_summary = self._extract_alert_summary(context)
        system_summary = self._extract_system_summary(context)
        container_summary = self._extract_container_summary(context)
        
        prompt = f"""
INCIDENT ANALYSIS REQUEST

I need your expert DevOps analysis of a production incident.

=== ALERT DETAILS ===
{alert_summary}

=== SYSTEM STATE ===
{system_summary}

=== CONTAINER ENVIRONMENT ===
{container_summary}

=== COMPLETE CONTEXT ===
{json.dumps(context, indent=2, default=str)}

=== YOUR TASK ===

Analyze this incident as a senior DevOps engineer and provide:

1. SITUATION ANALYSIS
   - What exactly is happening?
   - What are the symptoms vs root cause?
   - How severe is this issue?

2. ROOT CAUSE INVESTIGATION  
   - What is the most likely root cause?
   - What evidence supports this theory?
   - Are there any other possible causes?

3. SOLUTION STRATEGY
   - What is your recommended approach?
   - Why is this the best option?
   - What are the risks and mitigation strategies?

4. ACTION PLAN
   - Step-by-step actions to resolve this
   - For each action: what it does, why it's needed, expected outcome
   - How to validate each step worked

5. RISK ASSESSMENT
   - What could go wrong with your plan?
   - What are the fallback options?
   - When should we escalate to human intervention?

RESPONSE FORMAT: Provide your response as a JSON object with this structure:
{{
    "analysis": "Your detailed analysis of what's happening",
    "root_cause": "Your assessment of the root cause", 
    "decision": "Your decision on what to do",
    "action_plan": [
        {{
            "action_type": "specific_action_name",
            "target": "what_to_act_on",
            "command": "exact_command_if_applicable", 
            "reason": "why_this_action",
            "expected_outcome": "what_should_happen",
            "risk_level": "Low/Medium/High",
            "timeout_seconds": 60,
            "success_criteria": ["how_to_know_it_worked"]
        }}
    ],
    "risk_assessment": "Overall risk level and mitigation",
    "confidence": 0.85,
    "fallback_options": ["alternative_approaches"],
    "escalation_criteria": ["when_to_call_human"]
}}

Think step by step. Be thorough but practical. Focus on getting the service back online safely.
"""
        return prompt
    
    def _extract_alert_summary(self, context: Dict) -> str:
        """Extract alert summary for AI focus."""
        alert_data = context.get("alert_details", {})
        alerts = alert_data.get("alerts", [])
        
        if not alerts:
            return "No alert information available"
        
        summary = []
        for alert in alerts:
            alert_name = alert.get("labels", {}).get("alertname", "Unknown")
            service = alert.get("labels", {}).get("service", "Unknown")
            severity = alert.get("labels", {}).get("severity", "Unknown")
            status = alert.get("status", "Unknown")
            description = alert.get("annotations", {}).get("summary", "No description")
            
            summary.append(f"Alert: {alert_name} | Service: {service} | Severity: {severity} | Status: {status} | Description: {description}")
        
        return "\n".join(summary)
    
    def _extract_system_summary(self, context: Dict) -> str:
        """Extract system summary for AI focus."""
        system_state = context.get("system_state", {})
        service_status = context.get("service_status", {})
        
        summary = []
        summary.append(f"Docker Available: {system_state.get('docker_available', False)}")
        
        if system_state.get("docker_version"):
            summary.append(f"Docker Version: {system_state['docker_version']}")
        
        # Service status summary
        summary.append("\nService Health:")
        for service, status in service_status.items():
            available = status.get("available", False)
            response_time = status.get("response_time_ms")
            error = status.get("error")
            
            status_str = f"  {service}: {'UP' if available else 'DOWN'}"
            if response_time:
                status_str += f" ({response_time}ms)"
            if error:
                status_str += f" - Error: {error}"
            summary.append(status_str)
        
        return "\n".join(summary)
    
    def _extract_container_summary(self, context: Dict) -> str:
        """Extract container summary for AI focus."""
        docker_env = context.get("docker_environment", {})
        
        if not docker_env.get("available", False):
            return "Docker environment not available"
        
        containers = docker_env.get("containers", {})
        summary = []
        
        summary.append(f"Total Containers: {containers.get('total', 0)}")
        summary.append(f"Running: {containers.get('running', 0)}")
        summary.append(f"Stopped: {containers.get('stopped', 0)}")
        
        summary.append("\nContainer Details:")
        for container in containers.get("details", []):
            name = container.get("name", "Unknown")
            status = container.get("status", "Unknown")
            service = container.get("compose_service", "N/A")
            restart_count = container.get("restart_count", 0)
            
            container_str = f"  {name} ({service}): {status}"
            if restart_count > 0:
                container_str += f" - Restarts: {restart_count}"
            summary.append(container_str)
        
        return "\n".join(summary)
    
    def _parse_ai_response(self, ai_response: str, context: Dict) -> AIDecision:
        """Parse AI response into structured decision."""
        try:
            # Try to extract JSON from AI response
            ai_response_clean = ai_response.strip()
            
            # Find JSON content (sometimes AI wraps it in markdown)
            if "```json" in ai_response_clean:
                start = ai_response_clean.find("```json") + 7
                end = ai_response_clean.find("```", start)
                ai_response_clean = ai_response_clean[start:end].strip()
            elif ai_response_clean.startswith("```") and ai_response_clean.endswith("```"):
                ai_response_clean = ai_response_clean[3:-3].strip()
            
            # Parse JSON
            ai_data = json.loads(ai_response_clean)
            
            # Convert action plan to AIAction objects
            action_plan = []
            for action_data in ai_data.get("action_plan", []):
                action = AIAction(
                    action_type=action_data.get("action_type", "unknown"),
                    target=action_data.get("target", "unknown"),
                    command=action_data.get("command"),
                    reason=action_data.get("reason", "No reason provided"),
                    expected_outcome=action_data.get("expected_outcome", "Unknown outcome"),
                    risk_level=action_data.get("risk_level", "Medium"),
                    timeout_seconds=action_data.get("timeout_seconds", 60),
                    success_criteria=action_data.get("success_criteria", [])
                )
                action_plan.append(action)
            
            decision = AIDecision(
                analysis=ai_data.get("analysis", "No analysis provided"),
                root_cause=ai_data.get("root_cause", "Unknown"),
                decision=ai_data.get("decision", "No decision provided"),
                action_plan=action_plan,
                risk_assessment=ai_data.get("risk_assessment", "Unknown risk"),
                confidence=float(ai_data.get("confidence", 0.5)),
                fallback_options=ai_data.get("fallback_options", []),
                escalation_criteria=ai_data.get("escalation_criteria", [])
            )
            
            return decision
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            self.logger.error(f"Failed to parse AI response: {e}")
            self.logger.debug(f"AI response was: {ai_response}")
            
            # Create fallback decision from raw AI response
            return AIDecision(
                analysis=f"AI provided unstructured response: {ai_response[:500]}...",
                root_cause="Unable to parse AI analysis",
                decision="Escalate due to AI parsing failure",
                action_plan=[],
                risk_assessment="High - AI communication failure",
                confidence=0.1,
                fallback_options=["Manual analysis required"],
                escalation_criteria=["AI response parsing failure"]
            )
    
    async def evaluate_action_result(self, action: AIAction, result: Dict, context: Dict) -> Dict:
        """Evaluate the result of an action and decide next steps.
        
        Args:
            action: The action that was performed
            result: Result of the action execution
            context: Current system context
            
        Returns:
            AI evaluation and next step recommendations
        """
        evaluation_prompt = f"""
ACTION RESULT EVALUATION

I just executed this action:
Action: {action.action_type}
Target: {action.target}
Command: {action.command}
Expected Outcome: {action.expected_outcome}
Success Criteria: {action.success_criteria}

ACTUAL RESULT:
{json.dumps(result, indent=2, default=str)}

CURRENT CONTEXT:
{json.dumps(context, indent=2, default=str)}

As a DevOps engineer, evaluate:
1. Did the action succeed or fail?
2. Did it achieve the expected outcome?
3. What should happen next?
4. Are there any unexpected issues?
5. Should we continue, retry, or try a different approach?

Respond with JSON:
{{
    "success": true/false,
    "evaluation": "detailed_evaluation",
    "next_recommendation": "what_to_do_next",
    "continue_plan": true/false,
    "alternative_action": "if_different_approach_needed",
    "escalate": true/false,
    "reason": "reasoning_for_recommendation"
}}
"""
        
        try:
            messages = [
                SystemMessage(content=self._get_system_prompt()),
                HumanMessage(content=evaluation_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            ai_response = response.content
            
            # Parse AI evaluation
            if "```json" in ai_response:
                start = ai_response.find("```json") + 7
                end = ai_response.find("```", start)
                ai_response = ai_response[start:end].strip()
            
            evaluation = json.loads(ai_response)
            return evaluation
            
        except Exception as e:
            self.logger.error(f"Error in AI action evaluation: {e}")
            return {
                "success": False,
                "evaluation": f"AI evaluation failed: {e}",
                "next_recommendation": "Manual review required",
                "continue_plan": False,
                "escalate": True,
                "reason": "AI evaluation system failure"
            } 